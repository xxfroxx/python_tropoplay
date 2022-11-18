# Python infra demo
In order to deploy AWS CloudFormation templates, I'm using for this demo the Python Library Troposhere .

To use this demo install and configure the following framework:
```
# Install Python Troposphere
Please follow the instructions under this link: https://pypi.org/project/troposphere/

# AWS CLI and Named Profile
You should have installed AWS CLI and have configured at least the default named profile.

# Deploy the stack
You just need to execute the bash script: ./kickoff.sh, make sure to make it executable with "chmod +x kickoff.sh".
```

The deployment will create an AWS ECR Repository, after it will create a Docker image based on a NodeJS demo app, the same will be pushed to the ECR Repo.

Then the following AWS infrastructure will be deployed: ALB, TargetGroup, Listeners, VPC, 2 Public Subnets, Security Groups (one per ALB and one per ECS), then an ECS Fargate environment with TaskDefinition, Service and its task.

The demo app can be only accessed via ALB DNS as the ECS Security Group is allowing traffic only from ALB port 8080.

The application will be accesible throught the ALB DNS which will be visible in the terminal output after executing `./kickoff`, if you missed to copy it for any reason, still you can retrieve from the cloudformation template outputs.

Please feel free to ask any questions.