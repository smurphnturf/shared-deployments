import os, boto3, logging, json, re, concurrent.futures

logger = logging.getLogger()
logging.basicConfig()
LOGGING_LEVEL = os.environ['LOGGING_LEVEL']
logger.setLevel(LOGGING_LEVEL)

# override boto3 logging configuration
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('boto3').propagate = False
logging.getLogger('botocore').setLevel(logging.ERROR)
logging.getLogger('botocore').propagate = False

max_workers = 5
cf_client = boto3.client('cloudformation')


def delete_pipeline_stack(branch):
    suffix, StackName = sanitize_branch_name(branch)
    response = cf_client.delete_stack(
        StackName=StackName
    )
    waiter = cf_client.get_waiter('stack_delete_complete')
    waiter.wait(StackName=StackName)
    logger.info('successfully deleted CloudFormation stack:{}'.format(StackName))
    return True

def sanitize_branch_name(branch):
    suffix = re.sub('[^0-9a-zA-Z]+', '-', branch)
    StackName = '{}-PPS-branch-{}'.format(os.environ['StackName'], suffix)[:127]
    return suffix, StackName

def create_pipeline_stack(branch, customParameters):
    suffix, StackName = sanitize_branch_name(branch)
    logger.info('creating stack: {}'.format(StackName))
    response = cf_client.create_stack(
        StackName=StackName,
        TemplateURL=os.environ['TemplateURL'],
        Parameters=[
            {
                'ParameterKey': 'Branch',
                'ParameterValue': branch
            },
            {
                'ParameterKey': 'Suffix',
                'ParameterValue': suffix
            },
            {
                'ParameterKey': 'DynamicPipelineCleanupLambdaArn',
                'ParameterValue': os.environ['DynamicPipelineCleanupLambdaArn']
            },
            {
                'ParameterKey': 'ArtifactBucket',
                'ParameterValue': os.environ['ArtifactBucket']
            },
            {
                'ParameterKey': 'ArtifactBucketKeyArn',
                'ParameterValue': os.environ['ArtifactBucketKeyArn']
            },
            {
                'ParameterKey': 'PipelineServiceRoleArn',
                'ParameterValue': os.environ['PipelineServiceRoleArn']
            },
            {
                'ParameterKey': 'SamTranslationBucket',
                'ParameterValue': os.environ['SamTranslationBucket']
            },
        ]+list(map(lambda x: {"ParameterKey": x, "ParameterValue": customParameters[x]}, customParameters))
    )
    waiter = cf_client.get_waiter('stack_create_complete')
    waiter.wait(StackName=StackName)
    logger.info('successfully created new CloudFormation stack:{}'.format(StackName))
    return True

def lambda_handler(event, context):
    logger.info('event:{}'.format(json.dumps(event)))
    result_futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for record in event['Records']:
            message = json.loads(record['Sns']['Message'])
            logger.info('message:{}'.format(json.dumps(message)))
            repository = message['repository']
            ref = message['ref']
            based_ref = message['base_ref']
            event = message['event']
            event_name = message['event_name']
            if ref.split('/')[1] == 'heads':
                # it is branch
                branch = ref.split('/',2)[-1]
                logger.info('branch:{}'.format(branch))
                if branch == 'master':
                    logger.info('skipping branch master, pipeline for this branch created by main stack')
                    continue
                if event_name == 'create': # should be branch create and release
                    # whats the best way to give this to GHA
                    #Serverless-CICD-cross-account-poc-ProjectSetupStack-7TOUHNP27ZUG
                    logger.info('created new branch:{}, creating pipeline for this branch'.format(branch))
                    response = cf_client.describe_stacks(
                        StackName='Serverless-CICD-cross-account-poc-ProjectSetupStack-7TOUHNP27ZUG'
                    )
                    logger.info('Describe_stacks response:{}'.format(response))
                    #template_params = {}
                    #template_params['AppName'] = repository.split('/')[1]
                    #template_params['Suffix'] = 'custom-suffix'
                    stack_outputs = response['Stacks'][0]['Outputs']
                    for output in stack_outputs:
                        logger.info('Output eval:{}'.format(json.dumps(output)))
                        if 'ExportName' in output:
                            logger.info('Exportname:{}'.format(output['ExportName']))
                            if output['ExportName'] == 'Sample-CustomData':
                                output_data = output['OutputValue']
                                break
                    #override AppName
                    json_output_data = json.loads(output_data)
                    json_output_data['AppName'] = repository.split('/')[1]
                    logger.info('Using params:{}'.format(json.dumps(json_output_data)))
                    future = executor.submit(create_pipeline_stack, branch, json_output_data)
                    result_futures.append(future)
                elif event_name == 'delete':
                    logger.info('deleted old branch:{}, deleting pipeline for this branch'.format(branch))
                    future = executor.submit(delete_pipeline_stack, branch)
                    result_futures.append(future)

    for future in result_futures:
        future.result()

    return