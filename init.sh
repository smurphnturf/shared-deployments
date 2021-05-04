#!/bin/bash

# check if infra bucket exists au-slyp-com-shared-cross-account-template-base-poc or else make it

#sam build --template templates/full-stack.template.yaml -b .aws-sam/build --debug

#sam deploy --stack-name=shared-deployments --s3-prefix=shared-deployments --profile=shared-poweruser --s3-bucket=au-slyp-com-shared-cross-account-template-base-poc \
#--parameter-overrides=\
#DevAwsAccountId=293952095306 \
#ProdAwsAccountId=040536061213 \
#S3BucketName=au-slyp-com-shared-cross-account-template-base-poc \
#S3KeyPrefix=shared-deployments  \
#--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND


aws --profile=shared-poweruser cloudformation package --template-file templates/full-stack.template.yaml --output-template-file full-stack-transformed.yaml --s3-bucket au-slyp-com-shared-cross-account-template-base-poc
aws --profile=shared-poweruser cloudformation deploy --template full-stack-transformed.yaml --stack-name shared-deployments --parameter-overrides DevAwsAccountId=293952095306 ProdAwsAccountId=040536061213 S3BucketName=au-slyp-com-shared-cross-account-template-base-poc S3KeyPrefix=shared-deployments --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND 

exit 


#sam build --template pipeline.template.yaml -b .aws-sam/build --debug

#sam deploy --stack-name=shared-deployments-pipeline --s3-prefix=shared-deployments-pipeline --profile=shared-poweruser --s3-bucket=au-slyp-com-shared-cross-account-template-base-poc \
#--parameter-overrides=\
#ArtifactBucket=au-slyp-com-shared-cross-account-template-base-poc \
#ArtifactBucketKeyArn=arn:aws:kms:ap-southeast-2:833843385348:key/d83cee07-2c94-415e-adfa-0b148224e8dc \
#--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND