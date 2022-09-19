# Multi-function packager tool - Amazon CloudFront

This tool allows you to package multiple Edge Functions - Lambda@Edge or CloudFront Functions into a single function with minimal code changes.

## Pre-requisites:

1. Install [CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html).
1. Install [NPM](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).
1. You must have the Lambda@Edge (Node.js runtimes only supported) and CloudFront Functions defined in your AWS account.

## Steps to build

1. Clone and deploy the CDK solution in AWS N.Virginia region (us-east-1)

1. Change into the directory and run below commands
    - `cd amazon-cloudfront-multi-function-package`
    - `npm install`
    - `cdk bootstrap`
    - `cdk deploy`

1. The stack creates an S3 bucket to hold assembled code artifacts and three Lambda Functions explained below.
*{StackName}-LambdaFunctionPackager{UniqueID}* which is the main Lambda Multi-function packager

## Usage

### Procedure to chain Lambda@Edge functions:

1.	To combine Lambda@Edge functions, navigate to *{StackName}-LambdaFunctionAssembly* function on the [AWS Lambda console](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions) in *us-east-1*.

2.	 We will use the ‘Test’ feature of AWS Lambda service to build our combined function artifacts. Switch to the ‘Test’ tab to ‘Create new event’, give it a name.

![Procedure to chain Lambda@Edge functions](images/lambda_functions.jpg "Procedure to chain Lambda@Edge functions")

For ‘Event JSON’ use below JSON structure to combine Lambda@Edge Functions using their ARNs.
```
{
"viewer-request":[
    {
    "function_arn":"Lambda Function ARN1:Version1"
    },
    {
    "function_arn":"Lambda Function ARN2:Version2"
    }
 ]
}
```
Example to combine Lambda@Edge functions and attach to more than one event trigger.
```
{
"origin-request":[
    {
        "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:RedirectionFunction:1"
    },
    {
        "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:ABTestingCookieFunction:1"
    },
    {
        "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:DeviceDetectionFunction:1"
    }
    
 ],
"origin-response":[
    {
        "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:CacheControlFunction:$LATEST"
    },
    {
        "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:HSTSInsertionFunction:2"
    }
 ]
}
```
Note: change Lambda Function ARNs to match your environment.

3. *Save changes* to the event and select *Test* in the Lambda console to generate the Combined Function and Role.

4. Check the Lambda console for the newly created combined Lambda@Edge Function. Study the code structure
![View combined Lambda@Edge functions](images/view_combined_function.png "View combined Lambda@Edge functions")

The ‘*lib*’ folder contains the individual L@E function code and its dependencies.

The ‘*functions.json*’ would contain the mapping between Lambda@Edge event triggers and functions to invoke based for an event type.

```
{
    "origin-request": [
        {
            "function_name": "ABTestingCookieFunction",
            "handler": "index.handler"
        },
        {
            "function_name": "DeviceDetectionFunction",
            "handler": "index.handler"
        },
        {
            "function_name": "RedirectionFunction",
            "handler": "index.handler"
        }
    ],
    "origin-response": [
        {
            "function_name": "CacheControlFunction",
            "handler": "entrypoint.hook"
        },
        {
            "function_name": "HSTSInsertionFunction",
            "handler": "entrypoint.hook"
        }
    ]
}
```
Note: The Multi-function packager framework itself is agnostic to event triggers and invokes only relevant functions for the event type currently being triggered. For example, in above functions.json if a origin-request event is being triggered, then ‘ABTestingCookieFunction’,‘DeviceDetectionFunction’ and ‘RedirectionFunction’ functions are invoked.

The ‘*index.js*’ the main multi-function packager function which orchestrates these calls by first reading the functions.json file, loading the modules and executing the relevant functions. This function itself is agnostic to a particular event type and can handle all 4 event triggers: viewer-request, viewer-response, origin-request & origin-response

### Procedure to chain CloudFront Functions:



## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
