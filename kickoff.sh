#!/bin/bash

STACK_NAME="${STACK_NAME:-pocViaplay}"

aws ecr create-repository --repository-name test-viaplay --region eu-west-3

aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 203919308041.dkr.ecr.eu-west-3.amazonaws.com

docker build -t my-node-app .

docker tag my-node-app:latest 203919308041.dkr.ecr.eu-west-3.amazonaws.com/test-viaplay:latest

docker push 203919308041.dkr.ecr.eu-west-3.amazonaws.com/test-viaplay:latest

python3 vpc_no_alb.py \
  > viaplay_vpc_ecs.yaml

aws cloudformation deploy \
  --no-fail-on-empty-changeset \
  --template-file viaplay_vpc_ecs.yaml \
  --stack-name "${STACK_NAME}" \
  --region eu-west-3