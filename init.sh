#!/bin/bash

sam build --template templates/full-stack.template.yaml -b .aws-sam/build --debug

sam deploy --stack-name=shared-deployments --s3-prefix=shared-deployments --profile=shared-poweruser --s3-bucket=au-slyp-com-shared-cross-account-template-base-poc \
--parameter-overrides=\
DevAwsAccountId=293952095306 \
ProdAwsAccountId=040536061213 \
S3BucketName=au-slyp-com-shared-cross-account-template-base-poc \
S3KeyPrefix=shared-deployments  \
--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND