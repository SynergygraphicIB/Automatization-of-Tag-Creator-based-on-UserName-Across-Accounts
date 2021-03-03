# Username-Tag-Creator

We assume You and AWS organization set in place with all the neccesary permissions to ensure that resource creation events and all related info are to be passed between the accounts of the organization. For the sake of this document the ID of our organization is o-yvQk5gerjaja 

TagCreator Lambda function creates labels with the creator ID to track who did what. This is a highly valuable feature to help us keep track of our resources and reduce the time consuming resource management. We will deploy a pair of lambda functions; ExtractSns and TagCreatorId, in the us-east-1 region in Security Account that we will call ReceiverAccount in our organization to centralize the control and tagging of our resources being deployed in any account of the organization. Also, we will adress the Member Account which is sending the event as SenderAccount to help with the clarity of this doc. Ideally, our lambdas in the ReceiverAccount are fired when any AWS resource is deployed in any SenderAccount either by using the console or the AWS SDK for Python (Boto3). Once the resource is deployed Cloudwatch captures and sends the event through Event Buses to a matching Event Bus in ReceiverAccount. From Cloudwatch-Event Buses in ReceiverAccount to a Topic SNS named  that sends a string with the event info to the ExtractSns function allowing it to be executed from any region within ReceiverAccount, we need this intermidial lambda because Tagcreator only processes events in Json format and we must convert the string sent by SnsSendToLambda back to json format . the aforementioned lambda passes the event to TagCreator function to process the event .- say RunInstances and created the tags with a Key/value as instructed by the code , in our case UserName = UserNamehere. This sequence of sns topic - lambdas our Tag-Creator in ReceiverAccount ensures that if we deploy a VPC with a route table, both resources will get a tag with the use name who did the deployment. 

# 1. Create a Role in ReceiverAccount
We create a role in ReceiverAccount with enough permissions to assume role, security token services and create tags. Let us call our Role TagCreatorLambdaRole. if you are not too proficient about how to define policies in json just attach AdministratorAccess permission policy to the role.

# 2. Deploy Lambda Functions in ReceiverAccount
We set our lambda functions in virginia region or us-east-1. Any deployment event from any region in any sender account within the organization gets sent to the matching region in RecepientAccount. Once the event is ReceiverAccount from CloudWatch in any region the event is sent to our lambdas thru Sns Topic to ExtractSns Lambda Function.

We use the role, TagCreatorLambdaRole,  to the lambda function to create labels.

Create or import lambda functions:

1. ExtractSns: extracts the message of the event coming from Sns Topics which is a form of a string and return the cloudwatch event back in Json format.  

2. TagCreatorId: It only runs when resource creation events happen. Using rescursivity search and extracts all the creation ids of the event to create the tag of who executed the deployment whether it was an access role (Remember we are using Access Roles to jump to any account in the organization from the master account) or an IAM user.

# 3. Bind lambda functions through target

.When the ExtractSNS function does its job correctly it invokes and return the CloudWatch event to TagCreatorId function. In ExtractSNS configuration we go to "add destination" and in Destination configuration select source > Asynchronous invocation, Condition > On success, Destination type > Lambda function, in Destination select TagCreatorId. Hit Save

# 4. Create SNS Topic and Subscribe Lambda Function in ReceiverAccount

Create a Sns Topic in ReceiverAccount with the necessary permissions to publish messages in the Lambda function and subscribe it to the ExtractSNS lambda function. CloudWatch enable us publish events to any region. Since our lambda functions are base in Virgina (us-east-1) we must ensure that deployments from any region are sent to the lambda function sequence in Account A.

# 4. Add the necessary permissions in Event Buses in Account A
 Add an Event Buses Permission hat allows account A to receive all events from all the accounts in the organization

# 5 Create CloudWatch event Rule and link to the SNS topic in Account A
 Create event pattern that captures all creation events using AWS API Call via CloudTrail and select the previously created Topic SNS as destination

# 6  Create a CloudWatch event Rule in Account B and link it to event Bus in Account A
Create an event pattern the same as the previous one and select as Target the Event bus in Account A since this is where we are parking the SNS Topic that ultimately sends the message with the event to the lambda function, Select as Target "Event bus in another AWS Account, Provide the id of account A and create a new role for the execution of the event bus, Cloud Watch does it for you...yeah nice with the appropiate permissions

# 7 Setting up the appropiate permsissions to a Lambda Execution Role in Account A and Assume Role in account B
If you haven't already, configure these two AWS Identity and Access Management (IAM) roles:

LambdaAdminAccountA – The primary role in account A that gives the Lambda function permission to do its work.
The Assumed role – a role in account B, Say LambdaExecuteAccountB  that the Lambda function in account A assumes to gain access to cross-account resources, in this case resources from Account B.
Then, follow these instructions:

1.    In Account A - Attach the following IAM policy to your Lambda function's execution role to assume the role in account B:

Note: Replace 222222222222 with the AWS account ID of account B.
```json

{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::222222222222:role/LambdaExecuteAccountB"
    }
}
```
Is noteworthy to say you should keep consistency the Role name created in the Different Accounts of your Organization. For this document we chose to name the Role in account B, LambdaExecuteAccountB, for clarity purposes.

2.    In Account B - Edit the trust relationship of the assumed role in with the following Json:

Note: Replace 111111111111 with the AWS account ID of account A.
```json

"Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111111111111:role/LambdaAdminAccountA"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

# 8 Check the tags
We check for the tag managment of the resources newly deployed from Account B and verify that a tag with the user ID is present to ensure the proper functioning of the Lambda Tagging function


# Note: If you want to implement the function in different regions, repeat steps 3 to 7



