#!/usr/bin/env python3

import os
import json
from ap_helper import *

from dotenv import load_dotenv
load_dotenv()



def handler_function(func, upload_s3=False):

    taskid = ecs_instance_taskid()

    try:

        missing = missing_variables()
        data = {}

        if missing:
            raise Exception("Function is missing th following environmental variables: {}".foramat(missing))

        region = os.environ['AP_AWS_REGION']
        bucket = os.environ['AP_ECR_TASK']
        table  = os.environ['AP_ECR_TASK']
        task_data = os.environ['AP_ECR_TASK_DATA']

        data   = convert_strings(json.loads(task_data))

        if check_table(table, region=region):

            data['taskid'] = taskid
            data['error']  = None
            data['result'] = None

            result = func(data)

            if upload_s3 and upload_to_s3( bucket, result):
                data['result'] = bucket + "/" + result
            else:
                data['result'] = json.dumps(result)

            put_item(table, taskid, json.dumps(data), region=region)

        else:
            raise Exception('No database access to Dynamodb')

    except Exception as e:
        data['error'] = str(e)
        put_item(table, taskid, json.dumps(data), region=region)
        print('ERROR:' + str(e))



if __name__ == "__main__":

    # Import your main kickoff file.
    import main

    # Specify your main kickoff function.  environmental variables are send to this function in a `data` dictionary.
    func = main.topic_analysis

    # If set to true, result of above function should be a filename that will be uploaded to S3 (specified bucket)
    upload_s3 = True

    handler_function(func, upload_s3=upload_s3)
