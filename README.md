# Python infra demo
I'm using for this demo the Library Troposhere in order to deploy AWS CloudFormation templates.

To use this demo follow this:
```
# Install Python Troposphere
In order to do so, please follow the instructions under this link: https://pypi.org/project/troposphere/

# AWS CLI and Named Profile
You should have installed AWS CLI and have configured at least the default named profile.

# Deploy the stack
You just need to execute the bash script: ./kickoff.sh, make sure to make it executable with "chmod +x kickoff.sh".
```

The deployment will create an AWS ECR Repository, after it will create a Docker image based on a NodeJS demo app, the same will be pushed to the ECR Repo.

Then the following AWS infrastructure will be deployed: a VPC, 2 Public Subnets, an ECS Fargate environment with TaskDefinition and Service.

The application will be accesible throught the Public IP of the Docker container port 8080, running in the ECS Service Task.

## NOTE REGARDING ALB
I had some issues to deploy ALB, I did try and as a proof I left in this repo a file called `vpc_tro.py`, where you can see that I have all the stack completed for deploying ALB, actually it partially worked, but I had an issue with the ECS Service attribute called `LoadBalancers`, which prevents the ECS Service to attach the ALB, so I couldn't use the ALB DNS to access the app.

I might able to elaborate on this issue if necessary.

Please feel free to ask any questions.