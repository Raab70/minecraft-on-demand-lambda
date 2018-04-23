#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import errno
import boto3


DISCORD_CLIENT_TOKEN = os.getenv('DISCORD_CLIENT_TOKEN')
DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')

S3_TERRAFORM_PLAN_BUCKET = os.getenv('S3_TERRAFORM_PLAN_BUCKET')
S3_TERRAFORM_STATE_BUCKET = os.getenv('S3_TERRAFORM_STATE_BUCKET')

MODULE_DIR = '/tmp/python_modules'
EC2 = boto3.client('ec2')


def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True)
    except TypeError as exc:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def import_unbundled_packages():
    mkdir_p(MODULE_DIR)
    sys.path.append(MODULE_DIR)
    install_and_import('requests')
    install_and_import('discord.py', import_as='discord')


def send_discord_message(message):
    try:
        client = discord.Client()
        async def async_part():
            await client.login(DISCORD_CLIENT_TOKEN)
            await client.send_message(discord.Object(id=DISCORD_CHANNEL), message)
            await client.close()
        client.loop.run_until_complete(async_part())
    except discord.errors.HTTPException:
        print("Couldn't send discord message!")


def install_and_import(package, import_as=None):
    import importlib
    if import_as is None:
        import_as = package
    try:
        importlib.import_module(import_as)
    except ImportError:
        import pip
        print(pip.__version__)
        pip.main(['install', '--target', MODULE_DIR, package])
    finally:
        globals()[import_as] = importlib.import_module(import_as)


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
    print("Stopping instance")
    resp = EC2.stop_instances(
        InstanceIds=[instance['InstanceId']]
    )


def lambda_handler_destroy(event, context):
    import_unbundled_packages()
    send_discord_message('Stopping Server')
    stop_server()
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': """{"message":"success"}"""
    }


def lambda_handler_deploy(event, context):
    import_unbundled_packages()
    send_discord_message('Starting Server')
    ip = start_server()
    send_discord_message('Server started at {} with Minecraft v1.12.2. Please allow a few minutes for login to become available'.format(ip))
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': """{"message":"success"}"""
    }
