import os, boto3, logging, json, signal, traceback
from botocore.vendored import requests

logger = logging.getLogger()
logging.basicConfig()
LOGGING_LEVEL = os.environ['LOGGING_LEVEL']
logger.setLevel(LOGGING_LEVEL)

def delete_stack(event, context):
    sts_client = boto3.client('sts')
    response = sts_client.assume_role(
        RoleArn=event['ResourceProperties']['RoleArn'],
        RoleSessionName='CleanupChildStacks'
    )
    session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken']
    )
    cf_client = session.client('cloudformation')
    StackName = event['ResourceProperties']['StackName']
    response = cf_client.delete_stack(
        StackName=StackName
    )
    waiter = cf_client.get_waiter('stack_delete_complete')
    waiter.wait(StackName=StackName)
    logger.info('successfully deleted CloudFormation stack:{}'.format(StackName))
    return True

def lambda_handler(event, context):
    '''Handle Lambda event from AWS'''
    # Setup alarm for remaining runtime minus a second
    signal.alarm(int(context.get_remaining_time_in_millis() / 1000) - 1)
    try:
        logger.info('event: {}'.format(json.dumps(event)))
        if event['RequestType'] == 'Create':
            logger.info('CREATE!')
            send_response(event, context, "SUCCESS",
                        {"Message": "Resource creation successful!"})
        elif event['RequestType'] == 'Update':
            logger.info('UPDATE!')
            send_response(event, context, "SUCCESS",
                        {"Message": "Resource update successful!"})
        elif event['RequestType'] == 'Delete':
            logger.info('DELETE!')
            delete_stack(event, context)
            send_response(event, context, "SUCCESS",
                        {"Message": "Resource deletion successful!"})
        else:
            logger.info('FAILED!')
            send_response(event, context, "FAILED",
                        {"Message": "Unexpected event received from CloudFormation"})
    except: #pylint: disable=W0702
        logger.info('FAILED!')
        traceback.print_exc()
        send_response(event, context, "FAILED", {
            "Message": "Exception during processing"})


def send_response(event, context, response_status, response_data):
    response_body = json.dumps({
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })
    logger.info('Sending data: {}'.format(json.dumps(response_body)))
    logger.info('To URL: {}'.format(event['ResponseURL']))
    headers = {
        'content-type': '',
        'content-length': str(len(response_body))
    }
    response = requests.put(event['ResponseURL'],
                            data=response_body,
                            headers=headers)
    logger.info("CloudFormation returned status code: " + response.reason)

def timeout_handler(_signal, _frame):
    raise Exception('Time exceeded')


signal.signal(signal.SIGALRM, timeout_handler)