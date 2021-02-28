import json
import boto3
import re

s3 = boto3.resource('s3')
ec2 = boto3.resource('ec2')


def lambda_handler(event, context):
    
    # it overwrites event variable with the event coming from previous lambda
    event= event.get("responsePayload")
    
    # We capture evenName, userIdentity and awsRegion coming from json
    eventName=event["detail"].get("eventName")
    if("Create" in eventName or (eventName in ["RunInstances","AllocateAddress"])):
        
        principaID= event["detail"]["userIdentity"].get("arn")
        region=event["detail"].get("awsRegion")
        userName = event["detail"]["userIdentity"].get("sessionContext")
    
        key_id = event["aws_access_key_id"] 
        acces_key = event["aws_secret_access_key"]
                
        if(userName != None):
            userName= userName["sessionIssuer"].get("userName")
        else:
            userName= event["detail"]["userIdentity"].get("userName")
            
        client = boto3.client('ec2', region_name = region, aws_access_key_id = key_id, aws_secret_access_key = acces_key)
        
        response =  event["detail"]["responseElements"]
        request = event["detail"]["requestParameters"]
    
        request_ids=[]
        response_ids = []
        
        for request_id in item_generator(request):
            request_ids.append(request_id)
            
        for response_id in item_generator(response):
            if (response_id not in request_ids):
                if(eventName == "RunInstances" and "vpc-" not in response_id):
                    response_ids.append(response_id)
                elif(eventName != "RunInstances"):
                    response_ids.append(response_id)
        
        for ids in response_ids:
            addTagClient(client,userName,principaID, ids)
    else:
        return "Not is event creation"

# addTagClient - function to create tags in all resources newly created
# it adds the value principalID to creatorID tag to each resource created
def addTagClient(client,userName,principaID, ids):
    try:
        response = client.create_tags(
            Resources=[
                ids,
            ],
            Tags=[
                {
                    'Key': 'creatorId',
                    'Value': principaID,
                },
                {
                    'Key': 'UserName',
                    'Value': userName,
                },
            ],
        )
    except Exception as e:
        print (e)
                
                
def item_generator(json_input):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if(type(v)== str):

                if re.match('^[(a-z)]+-[(a-z0-9)]',v.lower()) and "Id" in k : 
                    if (k not in ("requestId","reservationId","ownerId","attachmentId")):
                        yield v
            else:
                yield from item_generator(v)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item)
