#!/usr/bin/env python3

import boto3
import requests
import random
import string
import os


def convert_strings(data):
    print(data)
    for d in data:
        if not isinstance(data[d], str):
            continue
        elif data[d].lower().strip() == 'none':
            data[d] = None
        elif data[d].lower().strip() == 'true':
            data[d] = True
        elif data[d].lower().strip() == 'false':
            data[d] = False

    return data


def missing_variables():

    needed_data = ["AP_ECR_TASK", "AP_ECR_TASK_DATA", "AP_AWS_REGION"]
    missing = []
    for d in needed_data:
        if d not in os.environ:
            missing.append(d)

    if (len(missing)):
        return ', '.join(missing)
    else:
        return False


def upload_to_s3(bucket,filename):
    try:
        client = boto3.resource('s3')
        client.Bucket(bucket).upload_file(Filename=filename,Key=filename)
        return True
    except Exception as e:
        print('ERROR: ' + str(e))
        return False


def get_account_id():
    try:
        client = boto3.resource('sts')
        return client.get_caller_identity()["Account"]
    except Exception as e:
        print('ERROR: ' + str(e))
        return False


# Query client and list_tables to see if table exists or not
def check_table(tablename, region=None):

    # Instantiate your dynamo client object
    client = boto3.client('dynamodb', region_name=region)

    # Get an array of table names associated with the current account and endpoint.
    response = client.list_tables()

    if tablename not in response['TableNames']:

        try:
            # Get the service resource.
            dynamodb = boto3.resource('dynamodb', region_name=region)

            # Create the DynamoDB table called followers
            table = dynamodb.create_table(
                TableName=tablename,
                KeySchema=[
                    {
                        'AttributeName': 'taskid',
                        'KeyType': 'HASH'
                    }

                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'taskid',
                        'AttributeType': 'S'
                    }

                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )

            # Wait until the table exists.
            table.meta.client.get_waiter('table_exists').wait(TableName=tablename)

        except Exception as e:
            print('ERROR: ' + str(e))
            return False

    return True

def put_item(tablename, taskid, jsondata, region=None):

    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(tablename)

    table.put_item(
       Item={
            'taskid': taskid,
            'data': jsondata,
        }
    )


def get_ecs_metadata():

    try:
        return requests.get("http://169.254.170.2/v2/metadata").json()
    except:
        pass

    return {}


def ecs_instance_taskid():

    # http://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-agent-introspection.html
    taskMetadata = get_ecs_metadata()
    if 'TaskARN' in taskMetadata:
        return taskMetadata['TaskARN'].split('/')[-1]
    else:
        return default
