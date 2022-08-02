import boto3
import json
import logging
from zipfile import ZipFile
from io import BytesIO
import urllib3
import os
import uuid
import time
import shutil
import hashlib

iamClient = boto3.client('iam')
lambdaClient = boto3.client('lambda')
s3 = boto3.resource('s3')

tmpDir = "/tmp/code"
libPrefix = "lib"

log = logging.getLogger()
log.setLevel(logging.INFO)

def lambda_handler(event, context):
    log.info(event)

    functionDefinitions = {}
    uid = uuid.uuid4().hex[0:12]
    baseDir = "{}/{}".format(tmpDir,uid)

    # fetch the function definitions for each ARN

    for eventType in event:
        log.info(f'Event type :{eventType}')
        functionDefinitions[eventType] = []
        for functionDetails in event[eventType]:
            log.info(f'Function ARN :{functionDetails["function_arn"]}')
            functionARN, functionVersion = parseFunctionNameVersion(functionDetails["function_arn"])
            funcDef = getFunctionDefinition(functionARN,functionVersion)
            functionDefinitions[eventType].append(funcDef)

    # identify the memory, runtime, timeout and function polcies

    functionPolicyArns = None
    runtime = ""
    timeout = 1
    memory = 128

    try:
        runtime = identifyRuntime(functionDefinitions)
        memory = calculateTotalMemory(functionDefinitions)
        timeout = calculateTotalTimeout(functionDefinitions)
        functionPolicyArns = getFunctionAttachedPolicyArns(functionDefinitions)

    except Exception as e:
        log.error(e)
        return

    log.info(f'runtimes :{runtime}')
    log.info(f'timeout :{timeout}')
    log.info(f'memory :{memory}')
    log.info(f'function policie Arns {functionPolicyArns}')

    # used in description of combined Lambda Function
    functionsCombined = []

    for eventType in functionDefinitions:

        try:
            for functionDefinition in functionDefinitions[eventType]:
                functionName = functionDefinition["Configuration"]["FunctionName"]
                functionLocation = functionDefinition["Code"]["Location"]
                downloadAndUncompressFunctions(baseDir,functionName,functionLocation)
                log.info(f'Download complete for :{functionName}')
                functionsCombined.append(functionName)

        except Exception as e:
            log.error(e)
    try:

        # download the LambdaChainer function
        functionARN, functionVersion = parseFunctionNameVersion(os.environ['LAMBDA_CHAINER_ARN'])
        response = getFunctionDefinition(functionARN,functionVersion)
        functionName = response["Configuration"]["FunctionName"]
        functionLocation = response["Code"]["Location"]
        downloadAndUncompressFunctions(baseDir,None,functionLocation)
        log.info(f'Download complete for :{functionName}')

    except Exception as e:
        log.error(e)

    # generate the functions.json file
    functionJSONArray = {}

    try:
        for eventType in event:
            log.info(f'Event :{eventType}')
            functionJSONArray[eventType] = []
            for functionDefinition in functionDefinitions[eventType]:
                log.info(f'Event type :{eventType} - {functionDefinition["Configuration"]["FunctionName"]}')
                functionInvocationDetails = {}
                functionInvocationDetails["function_name"] = functionDefinition["Configuration"]["FunctionName"]
                functionInvocationDetails["handler"] = functionDefinition["Configuration"]["Handler"]
                functionJSONArray[eventType].append(functionInvocationDetails)

        log.info(f'Functions JSON :{functionJSONArray}')
        functionJSONPath = f'{baseDir}/functions.json'
        log.info(f'FunctionJSONPath :{functionJSONPath}')
        with open(functionJSONPath, 'w') as file:
            json.dump(functionJSONArray, file,indent=4)

    except Exception as e:
        log.error(f'Error while generating functions.json file: {e}')

    # hash = hashlib.md5("-".join(functionsCombined).encode()).hexdigest()[0:12]
    # create consistent hash of function names to be used.
    combinedFunctionName = "{}-{}-{}".format(os.environ["STACK_NAME"],"CombinedFunction",uid)

    combinedFunctionDescription = "LambdaChainer:{}".format("-".join(functionsCombined))

    # zip the functions combined and upload to S3
    s3FileName = f'assembly_function/{combinedFunctionName}.zip'
    zipFileName = f'/tmp/test_{uid}.zip'
    zipFilesInDir(baseDir, zipFileName,libPrefix)
    s3.meta.client.upload_file(zipFileName, os.environ["S3_BUCKET"], s3FileName)

    # create the LambdaChainer Function & Role
    combinedRoleArn = createCombinedFunctionRole(os.environ["STACK_NAME"],functionPolicyArns,uid)

    # added sleep since the IAM role propagation takes a small amount of time and sometimes
    # Lambda function creation fails in the interim
    time.sleep(10)
    log.info(f'Combined role :{combinedRoleArn}')

    if checkFunctionCodeSize(zipFileName,event):
        createLambdaFunction(combinedFunctionName, combinedFunctionDescription, combinedRoleArn,s3FileName,memory,runtime,timeout)
    cleanup(zipFileName,baseDir)
    log.info(f'Combined function name created:{combinedFunctionName}')


# check code package size depending on Event Type
def checkFunctionCodeSize(zipFileName,event):
    codeSize = os.stat(zipFileName).st_size
    log.info("In checkFunctionCodeSize with size :%s",codeSize)
    viewerEvent = False

    for eventType in event:
        if isViewerEventType(eventType):
            viewerEvent = True

    try:
        if viewerEvent:
            assert codeSize < 1048576 # 1 MB
        else:
            assert codeSize < 52428800 # 50 MB

    except:
        log.error("Function size exceeds the limit allowed")
        return False
    return True

def createLambdaFunction(name,description,role, s3Path,memory,runtime,timeout):

    # create the CombinedFunction
    try:

        response = lambdaClient.create_function(
            Code={
                'S3Bucket': os.environ["S3_BUCKET"],
                'S3Key': s3Path,
            },
            Description=description,
            FunctionName=name,
            Handler='index.handler',
            MemorySize=memory,
            Publish=False,
            Role=role,
            Runtime=runtime,
            Timeout=timeout
        )
    except Exception as e:
        log.error(f'Function already exists :{e}')
        log.info(f'Updating the function :{name}')
        response = lambdaClient.update_function_code(
            FunctionName=name,
            S3Bucket=os.environ["S3_BUCKET"],
            S3Key=s3Path
        )

# clean up the dir and zip files
def cleanup(zipFileName, baseDir):
    # clean the files & directories created
    try:
        os.remove(zipFileName)
        shutil.rmtree(baseDir)
    except OSError as e:
        log.error(f'Error: {e.filename} - {e.strerror}')
    # print("Created function :{}".format(response))

def getFunctionAttachedPolicyArns(functionDefinitions):

    functionPolicyArns = []
    for eventType in functionDefinitions:
        for functionDefinition in functionDefinitions[eventType]:
            roleARN = functionDefinition["Configuration"]["Role"]
            roleName = roleARN[roleARN.rindex("/")+1:]
            log.info(f'Fetching role :{roleName}')
            response = iamClient.list_attached_role_policies(
                RoleName=roleName
            )
            for policy in response["AttachedPolicies"]:
                functionPolicyArns.append(policy['PolicyArn'])
    return functionPolicyArns

def createCombinedFunctionRole(stackName, functionPolicyArns, hash):

    assumeRolePolicyDocument = '{ \
            "Version": "2012-10-17", \
            "Statement": [ \
                { \
                    "Effect": "Allow", \
                    "Principal": { \
                        "Service": [ \
                            "lambda.amazonaws.com", \
                            "edgelambda.amazonaws.com" \
                        ] \
                    }, \
                    "Action": "sts:AssumeRole" \
                } \
            ] \
        }';

    combinedRoleName = "{}-CombineFunctionRole-{}".format(stackName,hash)
    response = iamClient.create_role(
        Path='/service-role/',
        RoleName=combinedRoleName,
        AssumeRolePolicyDocument=assumeRolePolicyDocument,
        Description='Combined LambdaChainer Function Role'
    )

    log.info(f'Role created :{response["Role"]["RoleName"]}')
    combinedRoleArn = response["Role"]["Arn"]
    log.info("Function policy Arns :%s",functionPolicyArns)

    for policyArn in functionPolicyArns:
        response = iamClient.attach_role_policy(
            RoleName=combinedRoleName,
            PolicyArn=policyArn
        )
    log.info('Attached policies')

    return combinedRoleArn

def identifyRuntime(functionDefinitions):

    runtimes = []
    for eventType in functionDefinitions:
        for functionDefinition in functionDefinitions[eventType]:
            log.info(f'Function/Runtime :{functionDefinition["Configuration"]["FunctionName"]}/{functionDefinition["Configuration"]["Runtime"]}')
            runtimes.append(functionDefinition["Configuration"]["Runtime"])
    uniqueRuntimes = list(dict.fromkeys(runtimes))

    if len(uniqueRuntimes) > 1:
        # log.info("Duplicate runtimes exist in the function :{}".format(runtimes))
        raise Exception("Sorry, Runtimes is not consistent :{}".format(runtimes))
    log.info('Runtime is consistent across all functions')
    return uniqueRuntimes[0]

def calculateTotalMemory(functionDefinitions):
    maxMemory = 0
    viewerTypeEvent = False

    for eventType in functionDefinitions:
        if isViewerEventType(eventType):
            viewerTypeEvent = True
        for functionDefinition in functionDefinitions[eventType]:
                maxMemory = max(functionDefinition["Configuration"]["MemorySize"],maxMemory)

    log.info(f'Memory to be allocated :{maxMemory}')

    # adjust for viewer origin type max allowed memory
    if viewerTypeEvent:
        maxMemory = min(maxMemory,128) # for viewer event type the max memory=128MB
    else:
        maxMemory = min(maxMemory,10000) # for origin event type the max memory=10GB

    return maxMemory

def isViewerEventType(eventType):
    if eventType == ("viewer-request" or "viewer-response"):
        return True
    return False

def calculateTotalTimeout(functionDefinitions):
    timeout = 0
    viewerTypeEvent = False

    for eventType in functionDefinitions:
        if isViewerEventType(eventType):
            viewerTypeEvent = True
        for functionDefinition in functionDefinitions[eventType]:
            timeout += functionDefinition["Configuration"]["Timeout"]

    # adjust for viewer origin type max allowed timeouts
    if viewerTypeEvent:
        timeout = min(timeout,5) # for viewer event type the default timeout=5
    else:
        timeout = min(timeout,30) # for origin event type the default timeout=30

    log.info(f'Timeout to be allocated :{timeout}')
    return timeout

def getFunctionDefinition(functionARN,functionVersion):

    response = lambdaClient.get_function(
        FunctionName=functionARN,
        Qualifier=functionVersion
    )

    return response

def downloadAndUncompressFunctions(baseDir,functionName,functionLocation):

    try:

        http = urllib3.PoolManager()
        response = http.request('GET', functionLocation, preload_content=False)

        with ZipFile(BytesIO(response.read())) as my_zip_file:
            for contained_file in my_zip_file.namelist():
                # functionName is not present for the main LambdaChainer function and hece
                # we change the directory structure accordingly
                if functionName is None:
                    path = f'{baseDir}/{contained_file}'
                else:
                    path = f'{baseDir}/{functionName}/{contained_file}'

                dir = os.path.dirname(path)
                os.makedirs(dir, exist_ok=True)
                # log.info("Path :"+path)
                # log.info("Dir :"+dir)
                # log.info(os.path.isdir(path))
                if os.path.isdir(path):
                    continue
                else:
                    with open(path , "wb") as output:
                        # log.info(contained_file)
                        for line in my_zip_file.open(contained_file).readlines():
                            # print(line)
                            output.write(line)
    except:
        raise Exception(f'Sorry, there was an erro during download of function :{functionName}')

def parseFunctionNameVersion(functionARN):
    index = functionARN.rindex(":")
    return functionARN[0:index],functionARN[index+1:]

# Zip the files from given directory that matches the filter
def zipFilesInDir(dirName, zipFileName,prefix):
   # create a ZipFile object
   log.info(f'Root dir :{dirName}')

   with ZipFile(zipFileName, 'w') as zipObj:
       # Iterate over all the files in directory
       for folderName, subfolders, fileNames in os.walk(dirName):
           for fileName in fileNames:
               # create complete filepath of file in directory
               filePath = os.path.join(folderName, fileName)

               # add prefix only for individual functions not for the main ChainerFunction files
               if folderName == dirName:
                   fileName = filePath.replace(dirName,"")
               else:
                   fileName = filePath.replace(dirName,prefix)

               # Add file to zip
               zipObj.write(filePath, fileName)
