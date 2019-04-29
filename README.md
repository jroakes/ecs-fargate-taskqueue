# Fargate TaskQueue Boilerplate

Uses AWS Lambda and Fargate for exposing an API for long running tasks. Provides the Python handler and helper code for packaging your container to receive data from environmental variables.  Easily deployable on existing long running Python code.  Results in a json response or S3 file URL.

Hit a /tasks endpoint Lambda function with json body and Lambda will:
* Create a task on Fargate using your container.
* The container will receive your code and execute your code, saving the status (based on taskid) to DynamoDB.
* The saved taskid result in DynamoDB can be JSON or a S3 path if uploaded there.
* Handle error states reasonably well, but this can be greatly improved.


## Deploying

1. `git clone https://github.com/jroakes/fargate-task-queue.git`
1. `pip install --upgrade -r requirements.txt`
1. Move your Python project into the `/project` folder and run once to ensure all requirements are installed.
1. Enter `cd project`
1. Enter `pyflakes .` and review output to clean any unneeded libraries or variables from your project.
1. Enter `pipreqs --use-local --force --clean .` to create a new requirements.txt file.
1. Modify `handler.py` (bottom) to specify the import of your main file and kickoff function to call.
1. Enter `cd ..`.
1. Edit the `.env-template` file with your AWS account info and resource names. Then Enter `mv .env-template .env` to rename.
1. Run `aws ec2 describe-subnets --filters "Name=default-for-az,Values=true"` and select two to add to the AP_SUBNETS variable in .env (comma-separated).
1. Run `chmod -x build.sh` then `./build.sh`.
1. Copy the `LambdaEndpoint` value from the resulting code.


## Usage

### POST
Post the task details and retrieve task id.

**Endpoint**: https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/Prod/tasks

**Request Body**:

* **taskDefinition**: Go to ECS > TaskDefinitions > <task-name> to ensure you are using the right version. Default: <AP_ECR_TASK>:1 Example: ecs-fargate-taskqueue-v4:1
* **containerName**: The name of your container deployed to ECR.  Default: <AP_ECR_TASK> Example: ecs-fargate-taskqueue-v4
* **taskData**: Object of expected values for your python project main function.  This is send in as a data dictionary.

```

{
    "taskDefinition": "ecs-fargate-taskqueue-v4:2",
    "containerName": "ecs-fargate-taskqueue-v4",
    "taskData": {
    	"client_url":"https://www.domain.com/",
    	"topic":"Naming Agency",
    	"name": null,
    	"current_page": "https://www.domain.com/path/",
    	"gsc_access": true
    	}

}

```

**Result**:

```
{
    "taskid": "4b4f0b17-f2fd-4850-bf7e-172704156359",
    "status": "ok"
}
```



### GET
Keep polling to get the task result.

**Endpoint**: https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/Prod/tasks/4b4f0b17-f2fd-4850-bf7e-172704156359

```
{
    "lastStatus": "PENDING",
    "healthStatus": "UNKNOWN",
    "result": "<errors, json, or filename from S3>",
    "taskid": "4b4f0b17-f2fd-4850-bf7e-172704156359",
    "status": "ok"
}
```



## Help From:

* https://github.com/teamhide/drf_cookiecutter_mongo/blob/f80d289597177ec26616787b7a667d2aa9dcbe4c/deploy/ecs.py
* https://medium.com/@mda590/inside-the-aws-re-invent-session-bot-c353830e2104
* https://github.com/mda590/reinvent_bot
* https://github.com/natesilverman/cambia/blob/21f2877a4a59a1a46a24d1dca5a576057517fba1/ecs/execute_ecs_task.py
* https://linuxacademy.com/blog/amazon-web-services-2/deploying-a-containerized-flask-application-with-aws-ecs-and-docker/
* https://gist.github.com/rupakg/52f98fb95e3a8fe8e495dbff9c2fd14d


## Confused or Questions?
* Check `https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/default/tasks` to see the logs of your ECR containers.
* Use the Lambda Test Events to POST body json (escaped) to your /task endpoint. Use the `Amazon API Gateway AWS Proxy` as a template.
* Each time you run `./build.sh` the TaskDefinition name version is incremented by 1.  So If you have tried to deploy twice and are receiving errors from Lambda, change the `taskDefinition` value from, for example, `ecs-fargate-taskqueue-v4:1` to `ecs-fargate-taskqueue-v4:2`.
* Deleting everything: `aws cloudformation delete-stack --stack-name <AP_ECR_TASK>` Example:`aws cloudformation delete-stack --stack-name ecs-fargate-taskqueue-v4`


## TODO:
1. Get Task ID in container for save to dynamodb. (done)
1. Standardize the call to lambda including task definition and env variables (done)
1. Better reporting to output the correct task definition after build. (I don't know how to do this well.  Pull request?)
1. Separate into `deploy with lambda` and `deply without lambda` build scripts as the Lambda function can be used for any task.
1. Would like to have the lambda function create the DB record so that we have a persistent record incase ECR launch fails.  Currently the database is updated by the container handler function.
