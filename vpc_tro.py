#!/usr/bin/python

import troposphere.elasticloadbalancingv2 as elb

from troposphere import (
    Base64,
    FindInMap,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Tags,
    Template,
)
from troposphere.autoscaling import Metadata
from troposphere.cloudformation import (
    Init,
    InitConfig,
    InitFile,
    InitFiles,
    InitService,
    InitServices,
)
from troposphere.ec2 import (
    EIP,
    VPC,
    Instance,
    InternetGateway,
    NetworkAcl,
    NetworkAclEntry,
    NetworkInterfaceProperty,
    PortRange,
    Route,
    RouteTable,
    SecurityGroup,
    SecurityGroupRule,
    Subnet,
    SubnetNetworkAclAssociation,
    SubnetRouteTableAssociation,
    VPCGatewayAttachment,
)
from troposphere.ecs import (
    AwsvpcConfiguration,
    Cluster,
    ContainerDefinition,
    NetworkConfiguration,
    PortMapping,
    Service,
    TaskDefinition,
    LoadBalancer,

)
from troposphere.policies import CreationPolicy, ResourceSignal

from troposphere.ecr import Repository


t = Template()

t.set_version("2010-09-09")

t.set_description(
    """\
Test for viaplay."""
)

ref_stack_id = Ref("AWS::StackId")


################
# Networking stack
################

VPCResource = t.add_resource(
    VPC("VPC", CidrBlock="10.0.0.0/16", Tags=Tags(Application=ref_stack_id))
)

subnetA = t.add_resource(
    Subnet(
        "SubnetA",
        CidrBlock="10.0.0.0/24",
        VpcId=Ref(VPCResource),
        AvailabilityZone="eu-west-3a",
        Tags=Tags(Application=ref_stack_id),
    )
)


subnetB = t.add_resource(
    Subnet(
        "SubnetB",
        CidrBlock="10.0.1.0/24",
        VpcId=Ref(VPCResource),
        AvailabilityZone="eu-west-3b",
        Tags=Tags(Application=ref_stack_id),
    )
)


internetGateway = t.add_resource(
    InternetGateway("InternetGateway", Tags=Tags(Application=ref_stack_id))
)

gatewayAttachment = t.add_resource(
    VPCGatewayAttachment(
        "AttachGateway", VpcId=Ref(VPCResource), InternetGatewayId=Ref(internetGateway)
    )
)

routeTable = t.add_resource(
    RouteTable(
        "RouteTable", VpcId=Ref(VPCResource), Tags=Tags(Application=ref_stack_id)
    )
)


route = t.add_resource(
    Route(
        "Route",
        DependsOn="AttachGateway",
        GatewayId=Ref("InternetGateway"),
        DestinationCidrBlock="0.0.0.0/0",
        RouteTableId=Ref(routeTable),
    )
)


# Route Association


subnetRouteTableAssociationA = t.add_resource(
    SubnetRouteTableAssociation(
        "SubnetRouteTableAssociationA",
        SubnetId=Ref(subnetA),
        RouteTableId=Ref(routeTable),
    )
)

subnetRouteTableAssociationB = t.add_resource(
    SubnetRouteTableAssociation(
        "SubnetRouteTableAssociationB",
        SubnetId=Ref(subnetB),
        RouteTableId=Ref(routeTable),
    )
)


################
# End Networking stack
################

################
# ALB stack
################

ApplicationElasticLB = t.add_resource(
        elb.LoadBalancer(
            "ApplicationElasticLB",
            Name="ApplicationElasticLB",
            Scheme="internet-facing",
            Subnets=[Ref(subnetA),Ref(subnetB)],
            SecurityGroups=[Ref("AlbSecurityGroup")]
        )
    )

TargetGroupEcs = t.add_resource(
    elb.TargetGroup(
        "TargetGroupEcs",
        DependsOn="ApplicationElasticLB",
        HealthCheckIntervalSeconds="30",
        HealthCheckProtocol="HTTP",
        HealthCheckTimeoutSeconds="10",
        HealthyThresholdCount="4",
        Matcher=elb.Matcher(HttpCode="200"),
        TargetType="ip",
        Name="tg-fargate",
        Port="8080",
        Protocol="HTTP",
        UnhealthyThresholdCount="3",
        VpcId=Ref(VPCResource),
    )
)
Listener = t.add_resource(
    elb.Listener(
        "Listener",
        Port="8080",
        Protocol="HTTP",
        LoadBalancerArn=Ref(ApplicationElasticLB),
        DefaultActions=[
            elb.Action(Type="forward", TargetGroupArn=Ref(TargetGroupEcs))
        ],
    )
)
t.add_resource(
    elb.ListenerRule(
        "ListenerRuleEcs",
        ListenerArn=Ref(Listener),
        Conditions=[elb.Condition(Field="path-pattern", Values=["/"])],
        Actions=[elb.ListenerRuleAction(Type="forward", TargetGroupArn=Ref(TargetGroupEcs))],
        Priority="1",
    )
)



################
# Security Group Fargate
################

fargateSecurityGroup = t.add_resource(
    SecurityGroup(
        "FargateSecurityGroup",
        GroupDescription="Enable HTTP access via port 8080",
        SecurityGroupIngress=[
            SecurityGroupRule(
                #IpProtocol="tcp", FromPort="8080", ToPort="8080", CidrIp="0.0.0.0/0"
                IpProtocol="tcp", FromPort="8080", ToPort="8080", SourceSecurityGroupId=Ref("AlbSecurityGroup")
            ),
        ],
        VpcId=Ref(VPCResource),
    )
)

################
# Security Group ALB
################

albSecurityGroup = t.add_resource(
    SecurityGroup(
        "AlbSecurityGroup",
        GroupDescription="Enable access all protocols",
        SecurityGroupIngress=[
            SecurityGroupRule(
                IpProtocol="tcp", FromPort="0", ToPort="65535", CidrIp="0.0.0.0/0"
            ),
        ],
        VpcId=Ref(VPCResource),
    )
)

################
# Fargate stack
################

cluster = t.add_resource(Cluster("Cluster"))

task_definition = t.add_resource(
    TaskDefinition(
        "TaskDefinition",
        RequiresCompatibilities=["FARGATE"],
        Cpu="256",
        Memory="512",
        NetworkMode="awsvpc",
        ExecutionRoleArn="arn:aws:iam::203919308041:role/ecsTaskExecutionRole",
        ContainerDefinitions=[
            ContainerDefinition(
                Name="cont_viaplay",
                Image="203919308041.dkr.ecr.eu-west-3.amazonaws.com/test-viaplay:latest",
                Essential=True,
                PortMappings=[PortMapping(ContainerPort=8080)],
            )
        ],
    )
)

service = t.add_resource(
    Service(
        "SrvCustom002",
        Cluster=Ref(cluster),
        DesiredCount=1,
        TaskDefinition=Ref(task_definition),
        LaunchType="FARGATE",
        LoadBalancers=[
            LoadBalancer(
                ContainerName="cont_viaplay",
                ContainerPort=8080,
                TargetGroupArn=Ref("TargetGroupEcs"),
                #LoadBalancerName=Ref("ApplicationElasticLB"),
            ),
        ],
        NetworkConfiguration=NetworkConfiguration(
            AwsvpcConfiguration=AwsvpcConfiguration(Subnets=[Ref("SubnetA"),Ref("SubnetB")],
            AssignPublicIp="ENABLED",
            SecurityGroups=[Ref(fargateSecurityGroup)],)
        ),
        #DependsOn="TargetGroupEcs",
    )
)





################
# Outputs
################

#https://towardsthecloud.com/aws-cloudformation-resource-attributes

t.add_output(
    [
        Output(
            "SecurityGroup",
            Description="Security Group for ECS Fargate",
            Value=Ref(fargateSecurityGroup),
        ),
        Output(
            "SubnetA",
            Description="Subnet ID",
            Value=GetAtt(subnetA, "SubnetId"),
        ),
        Output(
            "SubnetB",
            Description="Subnet ID",
            Value=GetAtt(subnetB, "SubnetId"),
        ),
        Output(
            "URL",
            Description="URL of the sample website",
            Value=Join("", ["http://", GetAtt(ApplicationElasticLB, "DNSName"),":8080"]),
        ),
    ]
)




print(t.to_yaml())