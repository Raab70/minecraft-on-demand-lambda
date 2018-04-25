#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime, timezone
import sys
import boto3

S3_TERRAFORM_PLAN_BUCKET = os.getenv('S3_TERRAFORM_PLAN_BUCKET')
S3_TERRAFORM_STATE_BUCKET = os.getenv('S3_TERRAFORM_STATE_BUCKET')
EC2 = boto3.client('ec2')


def find_instance():
    # Find name Minecraft
    instances = EC2.describe_instances(
        Filters=[{
            'Name': 'tag:Name',
            'Values': ['Minecraft']
        }]
    )
    if len(instances['Reservations']) != 1:
        raise RuntimeError("Could not identify minecraft server")
    if len(instances['Reservations'][0]['Instances']) != 1:
        raise RuntimeError("Could not identify minecraft server")
    return instances['Reservations'][0]['Instances'][0]


def start_server():
    instance = find_instance()
    print("Starting instance!")
    resp = EC2.start_instances(
        InstanceIds=[instance['InstanceId']]
    )
    return instance.get('PublicIpAddress')


def stop_server():
    instance = find_instance()
    now = datetime.now(timezone.utc)
    print(now)
    print(instance['LaunchTime'])
    if (now - instance['LaunchTime']).total_seconds() <= 1800:
        print("Not stopping instance which started in the last 30 minutes")
        return
    print("Stopping instance which was launched at: %s" % instance['LaunchTime'])
    resp = EC2.stop_instances(
        InstanceIds=[instance['InstanceId']]
    )


def lambda_handler_destroy(event, context):
    stop_server()
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': """{"message":"success"}"""
    }


def lambda_handler_deploy(event, context):
    ip = start_server()
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': """{"message":"success"}"""
    }
