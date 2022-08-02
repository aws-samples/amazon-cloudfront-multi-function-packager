# Multi-function packager tool - Amazon CloudFront

This tool allows you to package multiple Edge Functions - Lambda@Edge or CloudFront Functions into a single function with minimal code changes.

## Pre-requisites:

1. Install 'make'.
1. Install git.

## Steps to build

1. Clone this repository.

2. In the 'Makefile'
- set 'bucket' variable to the Amazon S3 bucket in us-east-1 which will hold your build artifacts.
- set 'profile' variable to the AWS CLI profile which has necessary permissions to deploy AWS resources using CloudFormation.

3. Run `make all`. This would build the project and copy the assets into an S3 bucket and deploy the CloudFormation template in the AWS region set.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
