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
*{StackName}-LambdaFunctionPackager{UniqueID}* : which is the main Lambda Multi-function packager

## Usage

### Procedure to chain Lambda@Edge functions:
1.	To combine Lambda@Edge functions, navigate to *{StackName}-LambdaFunctionAssembly* function on the [AWS Lambda console](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions) in *us-east-1*.
2.	 We will use the ‘Test’ feature of AWS Lambda service to build our combined function artifacts. Switch to the ‘Test’ tab to ‘Create new event’, give it a name.

![Procedure to chain Lambda@Edge functions](images/lambda_functions.jpg "Procedure to chain Lambda@Edge functions")

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
