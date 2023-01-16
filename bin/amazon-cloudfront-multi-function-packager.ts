#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { AmazonCloudfrontMultiFunctionPackagerStack } from '../lib/amazon-cloudfront-multi-function-packager-stack';

const app = new cdk.App();
new AmazonCloudfrontMultiFunctionPackagerStack(app, 'MFPStack', {
  description: "Multi-function packager tool for Amazon CloudFront Edge Functions (uksb-1t9uc46mc)",
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: 'us-east-1' },
  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
});
