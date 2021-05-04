# first ChildAccountRole needs to be deployed 
in any accounts that will be deployed from the shared account or the test shared account

# Next we need a bucket:   
aws s3 --profile shared-poweruser mb s3://au-slyp-com-shared-cross-account-template-base-poc --region ap-southeast-2

# Remember clean up
Delete the cross account stacks in the sub accounts


# Put pipeline stack into s3
## this needs to happen with every branch commit in case it changed per project..... fuck
aws --profile shared-poweruser s3 cp templates/apps/sample-app/pipeline.template.yaml s3://au-slyp-com-shared-cross-account-template-base-poc/serverless-cicd/templates/pipeline.template.yaml --acl private


# Build parent stack:

sam build --template templates/full-stack.template.yaml -b .aws-sam/build --debug

sam deploy --stack-name=Serverless-CICD-cross-account-poc --s3-prefix=serverless-cicd --profile=shared-poweruser --s3-bucket=au-slyp-com-shared-cross-account-template-base-poc --parameter-overrides=DevAwsAccountId=293952095306 ProdAwsAccountId=040536061213 S3BucketName=au-slyp-com-shared-cross-account-template-base-poc S3KeyPrefix=serverless-cicd  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND



{"repository":"smurphnturf/shared-deployments","ref":"refs/heads/release/self-deployment-test-1","base_ref":"","event_name":"create"}