import os, boto3, json, signal, traceback
from botocore.vendored import requests
from botocore.exceptions import ClientError

def get_cfn_parameters(e):
    params = []
    cfnp = e['ResourceProperties']['CfnParameters']
    for p in cfnp.keys():
        params.append({"ParameterKey": p, "ParameterValue": cfnp[p]})
    return params

def get_client(service, e, c):
    sts_client = boto3.client('sts')
    response = sts_client.assume_role(RoleArn=e['ResourceProperties']['RoleArn'],RoleSessionName='QuickStartCfnStack')
    session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],aws_secret_access_key=response['Credentials']['SecretAccessKey'],aws_session_token=response['Credentials']['SessionToken'])
    return session.client(service)

def update(e, c):
    cf_client = get_client("cloudformation", e, c)
    rp = e['ResourceProperties']
    try:
        response = cf_client.update_stack(
            StackName=e["PhysicalResourceId"],
            TemplateBody=rp['TemplateBody'],
            Parameters=get_cfn_parameters(e),
            Capabilities=rp['Capabilities']
        )
    except ClientError as er:
        if "No updates are to be performed" not in str(er):
            raise
    return e["PhysicalResourceId"]
    waiter = cf_client.get_waiter('stack_update_complete')
    waiter.wait(StackName=e["PhysicalResourceId"])
    return response['StackId']

def create(e, c):
    cf_client = get_client("cloudformation", e, c)
    rp = e['ResourceProperties']
    response = cf_client.create_stack(
    StackName=rp['StackName'],
    TemplateBody=rp['TemplateBody'],
    Parameters=get_cfn_parameters(e),
    Capabilities=rp['Capabilities']
    )
    waiter = cf_client.get_waiter('stack_create_complete')
    waiter.wait(StackName=rp['StackName'])
    return response['StackId']

def delete(e, c):
    cf_client = get_client("cloudformation", e, c)
    response = cf_client.delete_stack(StackName=e["PhysicalResourceId"])
    waiter = cf_client.get_waiter('stack_delete_complete')
    waiter.wait(StackName=e["PhysicalResourceId"])
    return True

def lambda_handler(e, c):
    signal.alarm(int(c.get_remaining_time_in_millis() / 1000) - 1)
    try:
        print('event: {}'.format(json.dumps(e)))
        if e['RequestType'] == 'Create':
            e['PhysicalResourceId'] = create(e, c)
            send_response(e, c, "SUCCESS", {"Message": "Resource creation successful!"})
        elif e['RequestType'] == 'Update':
            e['PhysicalResourceId'] = update(e, c)
            send_response(e, c, "SUCCESS", {"Message": "Resource update successful!"})
        elif e['RequestType'] == 'Delete':
            delete(e, c)
            send_response(e, c, "SUCCESS", {"Message": "Resource deletion successful!"})
        else:
            send_response(e, c, "FAILED", {"Message": "Unexpected event received from CF"})
    except Exception as er:
        traceback.print_exc()
        send_response(e, c, "FAILED", {"Message": "Exception during processing"})

def send_response(e, c, response_status, response_data):
    if not e.get('PhysicalResourceId'):
        e['PhysicalResourceId'] = c.log_stream_name
    _rb = {
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: " + c.log_stream_name,
        "StackId": e['StackId'],
        "RequestId": e['RequestId'],
        "LogicalResourceId": e['LogicalResourceId'],
        "PhysicalResourceId": e['PhysicalResourceId'],
        "Data": response_data
    }
    rb = json.dumps(_rb)

    print('ResponseBody: %s', rb)
    headers = {
        'content-type': '',
        'content-length': str(len(rb))
    }
    try:
        response = requests.put(e['ResponseURL'], data=rb, headers=headers)
        print("CF returned status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))
        raise

def timeout_handler(_signal, _frame):
    raise Exception('Time exceeded')

signal.signal(signal.SIGALRM, timeout_handler)