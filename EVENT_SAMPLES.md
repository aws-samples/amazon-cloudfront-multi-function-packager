For ‘Event JSON’ use below JSON structure to combine Lambda@Edge Functions using their ARNs.
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
Example to combine Lambda@Edge functions and attach to single event trigger.
{
"viewer-request":[
    {
    "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:TrueClientIPFunction:1"
    },
    {
    "function_arn":"arn:aws:lambda:us-east-1:123456789012:function:NormalizationFunction:1"
    }
 ]
}
Note: Lambda Function ARNs include the specific version of Lambda Function. Change the ARNs to match your environment.

The JSON structure defines two Lambda@Edge function ARNs which will be combined (in the order defined) to a new Lambda function and associated to the ‘Viewer-Request’ event trigger.

Example to combine Lambda@Edge functions and attach to more than one event trigger.
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
Note: change Lambda Function ARNs to match your environment.
