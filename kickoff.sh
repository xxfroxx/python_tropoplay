#!/bin/bash

STACK_NAME="${STACK_NAME:-pocViaplay}"

aws ecr create-repository --repository-name test-viaplay --region eu-west-3 --output json

aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 203919308041.dkr.ecr.eu-west-3.amazonaws.com

docker build -t my-node-app .

docker tag my-node-app:latest 203919308041.dkr.ecr.eu-west-3.amazonaws.com/test-viaplay:latest

docker push 203919308041.dkr.ecr.eu-west-3.amazonaws.com/test-viaplay:latest

python3 vpc_tro.py \
  > full_viaplay_vpc_ecs.yaml

aws cloudformation deploy \
  --no-fail-on-empty-changeset \
  --template-file full_viaplay_vpc_ecs.yaml \
  --stack-name "${STACK_NAME}" \
  --region eu-west-3 \
  --output table

echo ""
echo "Please see below the ALB DNS that you can use to access the demo app:"
echo ""
echo "##############################################################################"

aws cloudformation describe-stacks \
--region eu-west-3 \
--stack-name "${STACK_NAME}" \
--query "Stacks[].Outputs[?OutputKey=='URL'].OutputValue" --output text

echo "##############################################################################"