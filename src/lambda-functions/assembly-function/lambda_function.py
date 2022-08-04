import boto3
import logging
import os
import uuid
from pathlib import Path

cloudfront = boto3.client('cloudfront')

log = logging.getLogger()
log.setLevel(logging.INFO)

MAIN_FUNCTION_TEMPLATE = Path('main_template.js').read_text()
FUNCTION_TEMPLATE = Path('function_template.js').read_text()

def lambda_handler(event, context):
    log.info(event)

    functionDefinitions = {}
    uid = uuid.uuid4().hex[0:12]
    # baseDir = "{}/{}".format(tmpDir,uid)

    # fetch the function definitions for each ARN

    for eventType in event:
        log.info(f'Event type :{eventType}')
        functionDefinitions[eventType] = []
        for functionDetails in event[eventType]:
            log.info(f'Function Name :{functionDetails["function_name"]}')
            funcDef = getFunctionDefinition(functionDetails["function_name"],functionDetails["stage"])
            log.debug(f'FuncDef: {funcDef}')
            #downloadFunctions(baseDir,functionDetails["function_name"],funcDef)
            functionDefinitions[eventType].append(funcDef)

    log.info(f'{functionDefinitions}')

    functionCode = "";
    functionList = "";

    for eventType in event:
        for functionDetails in functionDefinitions[eventType]:
            log.info(f'Function details {functionDetails}')
            functionCode = functionCode + FUNCTION_TEMPLATE.format(**functionDetails) + '\n'
            functionList = functionList + functionDetails["functionName"] + ','

    # log.info(f'Function code combined :{functionCode}')
    log.info(f'Function List combined :{functionList}')

    combinedFunctionCode = MAIN_FUNCTION_TEMPLATE.format(FUNCTION_CODE=functionCode,IMPORTS='',FUNCTION_LIST=functionList)

    combinedFunctionName = "{}-{}-{}".format(os.environ["STACK_NAME"],"CombinedFunction",uid)
    log.info(f'Combined function name:{combinedFunctionName}')

    # s3FileName = f'assembly_function/{combinedFunctionName}/index.js'
    # s3.meta.client.put_object(Body=combinedFunctionCode,Bucket=os.environ["S3_BUCKET"],Key=s3FileName)

    combinedFunctionDescription = f'FunctionChainer:{functionList}'

    combinedFunctionCodeEncoded = combinedFunctionCode.encode('utf-8')

    if checkFunctionCodeSize(combinedFunctionCodeEncoded):
        response = cloudfront.create_function(
            Name=combinedFunctionName,
            FunctionConfig={
                'Comment': combinedFunctionDescription,
                'Runtime': 'cloudfront-js-1.0'
            },
            FunctionCode=combinedFunctionCode.encode('utf-8')
        )

# check combined function size is less than 10 KB
def checkFunctionCodeSize(code):
    log.info("Function code length %s",len(code))
    try:
        assert len(code) < 10240
    except Exception as e:
        log.error("Function size is greated allowed limits of 10 KB")
        return False
    return True

# get the function definition metadata
def getFunctionDefinition(functionName,stage):

    response = cloudfront.get_function(
        Name=functionName,
        Stage=stage
    )

    return {"functionName":functionName,"functionCode":response["FunctionCode"].read().decode("utf-8")}
