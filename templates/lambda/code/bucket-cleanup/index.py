import json
import cfnresponse
import boto3
from botocore.exceptions import ClientError
s3 = boto3.resource('s3')
def handler(event, context):
    bucket = s3.Bucket(event['ResourceProperties']['Bucket'])
    print('deleting all objects in bucket ' + bucket)
    if event['RequestType'] == 'Delete':
        try:
            bucket.objects.all().delete()
            return cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
        except ClientError as e:
            print(e)
            return cfnresponse.send(event, context, cfnresponse.FAILED, {})
    else:
        return cfnresponse.send(event, context, cfnresponse.SUCCESS, {})