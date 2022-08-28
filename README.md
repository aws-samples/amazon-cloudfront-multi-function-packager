# Multi-function packager tool - Amazon CloudFront

This tool allows you to package multiple Edge Functions - Lambda@Edge or CloudFront Functions into a single function with minimal code changes.

## Pre-requisites:

1. Install [CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html).
1. Install [NPM](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

## Steps to build

1. Clone this repository

`git clone https://github.com/aws-samples/amazon-cloudfront-multi-function-packager`

2. Change into the directory and run below commands
- `cd amazon-cloudfront-multi-function-package`
- `npm install`
- `cdk bootstrap`
- `cdk deploy`

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
