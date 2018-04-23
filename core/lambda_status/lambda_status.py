#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mcstatus import MinecraftServer
import json
import boto3
import os
import socket

S3_TERRAFORM_PLAN_BUCKET = os.environ.get('S3_TERRAFORM_PLAN_BUCKET')
S3_TERRAFORM_STATE_BUCKET = os.environ.get('S3_TERRAFORM_STATE_BUCKET')
EC2 = boto3.client('ec2')


def find_instance():
    # Find name Minecraft
    instance = None
    instances = EC2.describe_instances(
        Filters=[{
            'Name': 'tag:Name',
            'Values': ['Minecraft']
        }]
    )
    if len(instances['Reservations'][0]['Instances']) == 1:
        instance = instances['Reservations'][0]['Instances'][0]
    return instance


def lambda_handler_status(event, context):
    print("Handling request")
    instance = find_instance()

    ip = None
    try:
        ip = instance['PublicIpAddress']
    except Exception as exc:
        pass

    status = {'status': 'offline'}
    if not ip:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(status)
        }

    try:
        socket.create_connection((ip, 22), timeout=1)
        status['status'] = 'pending'
        status['host'] = ip
    except (socket.error, socket.timeout, Exception) as exc:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(status)
        }

    try:
        server = MinecraftServer.lookup(ip + ':25565')
        status = server.status().raw
        status['status'] = 'online'
        status['host'] = ip
    except AttributeError as exc:
        # silence mcstatus bug:
        # Exception ignored in: <bound method TCPSocketConnection.__del__ of <mcstatus.protocol.connection.TCPSocketConnection object at 0x7fef589619b0>>
        # Traceback (most recent call last):
        # File "/var/task/mcstatus/protocol/connection.py", line 153, in __del__
        #     self.socket.close()
        # AttributeError: 'TCPSocketConnection' object has no attribute 'socket'
        pass
    except Exception as exc:
        pass

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(status)
    }
