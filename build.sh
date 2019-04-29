
# sudo apt-get install dos2unix
# `dos2unix build.sh` if receiving line-ending errors.

# Load .env file
source .env

AP_AWS_ACCOUNT_ID="$(aws sts get-caller-identity --output text --query 'Account')"

sudo $(aws ecr get-login --no-include-email --region $AP_AWS_REGION)

sudo docker build -t $AP_ECR_TASK .

sudo docker tag ${AP_ECR_TASK}:latest ${AP_AWS_ACCOUNT_ID}.dkr.ecr.${AP_AWS_REGION}.amazonaws.com/${AP_ECR_TASK}

aws ecr create-repository --repository-name $AP_ECR_TASK

aws s3 mb s3://${AP_ECR_TASK}

docker push ${AP_AWS_ACCOUNT_ID}.dkr.ecr.${AP_AWS_REGION}.amazonaws.com/${AP_ECR_TASK}

aws cloudformation package --template-file aws_deploy.yaml --s3-bucket $AP_ECR_TASK --output-template-file aws_deploy_packaged.yaml

aws cloudformation deploy \
    --template-file aws_deploy_packaged.yaml \
    --stack-name ${AP_ECR_TASK} \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides BucketName=${AP_ECR_TASK} DBName=${AP_ECR_TASK} SubNets=${AP_SUBNETS}


echo 'Endpoint below: '
aws cloudformation list-exports
