import json
import boto3
import re

s3 = boto3.resource('s3')
ec2 = boto3.resource('ec2')


def lambda_handler(event, context):
    
    # it overwrites event variable with the event coming from previous lambda
    event= event.get("responsePayload")
    
    if(str(event.get("account"))=="1111111111"):
        
        event["aws_access_key_id"] = "111111111"
        event["aws_secret_access_key"] = "111111111111
        
    return event
