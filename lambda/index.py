#!/usr/bin/env python3

from datetime import datetime
import json
import boto3
from botocore.exceptions import ClientError
import os

AP_ECR_TASK = os.environ['AP_ECR_TASK']
AWS_REGION = os.environ['AP_AWS_REGION']
AP_SUBNETS = os.environ['AP_SUBNETS']

ecs_client = boto3.client('ecs')
sts_client = boto3.client('sts')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

AWS_ACCOUNT_ID = sts_client.get_caller_identity()["Account"]


def get_full_arn(value, valuetype):
    return "arn:aws:ecs:{0}:{1}:{2}/{3}".format(AWS_REGION, AWS_ACCOUNT_ID, valuetype, value)

def get_taskid(taskArn):
    return taskArn.split('task/')[1] if 'task/' in taskArn else False

def verify_body(data):
    expected = ['taskDefinition','containerName','taskData']
    return data if len([d for d in expected if d in data]) == len(expected) else False


def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def submit_to_fargate(data, execution_timestamp):

    '''
    Function: Submits job to fargate.

    Parameters:
    data: dictonary from json loaded body of POST.

    '''
    response = ecs_client.run_task(
        cluster=data.get('cluster', 'default'),
        taskDefinition= get_full_arn(data.get('taskDefinition'), 'task-definition'),
        overrides={
            'containerOverrides': [
                {
                    'name': data.get('containerName'),
                    'environment': [
                                        {"name": "AP_ECR_TASK", "value":AP_ECR_TASK},
                                        {"name": "AP_ECR_TASK_DATA", "value":json.dumps(data.get('taskData'))},
                                        {"name": "AP_AWS_REGION", "value":AWS_REGION}
                                   ]
                },
            ]
        },
        launchType='FARGATE',
        count=1,
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': data.get('subnets', AP_SUBNETS).split(','),
                'assignPublicIp': 'ENABLED'
            }
        }
    )

    return response['tasks'][0]['taskArn']



def get_fargate_status(taskid):

    '''
    Function: Gets status of job from fargate.

    Parameters:
    taskid: str a9f21ea7-c9f5-44b1-b8e6-b31f50ed33c0
    '''
    taskArn = get_full_arn(taskid, 'task')
    response = ecs_client.describe_tasks(tasks=[taskArn])
    tasks = response.get('tasks', None)

    if tasks and len(tasks) > 0:
        task = tasks[0]
        keys = ['lastStatus','stoppedReason','stopCode','healthStatus']
        return { k:task[k] for k in task if k in keys}

    else:
        return {}

def get_db_record(taskid, tablename=None):

    table = dynamodb.Table(tablename)

    try:
        response = table.get_item(
            Key={
                'taskid': taskid
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
        return {'result':e.response['Error']['Message']}
    else:
        if 'Item' in response:
            return {'result':response['Item']['data']}
        else:
            return {'result':'No result'}


def respond(err, res=None):

    if err:
        err['status'] = 'error'
    else:
        res['status'] = 'ok'

    return {
    'statusCode': 404 if err else 200,
    'body': json.dumps(err) if err else json.dumps(res),
    'headers': {'Content-Type':'application/json'}
    }



def lambda_handler(event, context):

    execution_timestamp = str(datetime.now())

    try:

        qsp = event.get('queryStringParameters',{})
        path = event.get('path',None)
        method = event.get('httpMethod', None)

        if method == "POST":
            body = verify_body( json.loads(event.get('body',"{}")) )

            if not body:
                return respond({'message':'Missing taskDefinition, name, or environment data.'})

            taskArn = submit_to_fargate(body, execution_timestamp)

            return respond(None, {'taskid':get_taskid(taskArn)})


        elif method == "GET":

            taskid = event['pathParameters']['proxy']
            status = merge_dicts( get_fargate_status(taskid), get_db_record(taskid, tablename=AP_ECR_TASK) )
            status['taskid'] = taskid
            return respond(None, status)

        else:
            return respond({'message':'No method specified.'})

    except Exception as e:
        return respond({'message': 'ERROR:' + str(e)})
