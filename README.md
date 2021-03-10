# Automatization for Tag Creation with the Username ARN and ID:

We already have to have an AWS organization set in place with all the neccesary permissions accross accounts to ensure that resource creation events and all related event calls are to be passed between the accounts of the organization. 
At least two accounts. A ReceiverAccount with ID 111111111111 and a SenderAccount with ID 222222222222. For the sake of this document the ID of our organization is o-myexampleOrgId 

## List of Resources Used or Deployed
### IAM Roles
**LambdaAdmin** - Role with the necessary permissions to enable the Lambda functions to perform the task with want them to do In ReceiverAccount
**LambdaExecute** - Role we create in SenderAccount with to be assumed by LambdaAdmin from ReceiverAccount to get the creation events.
### Sns Topics
**SendEventToExtractSnsLambda** - We deploy this Sns Topic in us-east-2 in Reciever account to send the creation event to ExtracSns to us-east-1. Sns topics allow us to send events across regions.
### Lambda functions
**ExtractSns** - Converts the string coming from the Sns Topic "SnsSendToLambdaOhio" back into Json. It has as target destination TagCreatorId Lambda Function.
**TagCreatorId**- creates tags with the creator ID and arn to track who did what. This is a highly valuable feature to help keep tracking resources and reduce the time consuming resource management. 
CloudWatch Rules - We create a rule to capture events in us-east-2 in sender account and in the receiver account also in us-east-2. also we have to add a permission to allow even buses to pass events in the organization and edit trust relationships. 

## How does it work? 
We will pass a deployment event in us-east-2 in SenderAccount to lambda functions in us-east-1 in a ReceiverAccount to create tags onto the resources newly deployed the ReceivingAccount. So, we have to create a pipeline to make this posible.
We will deploy a pair of lambda functions; ExtractSns and TagCreatorId in the us-east-1 region in a designated account that we will be ReceiverAccount in our organization. The purpose is to centralize the control and tagging of resources being deployed in any member account of the organization. Also, we will use the Member Account which will be sending the creation event calls as SenderAccount to help you to follow this tutorial. 
When properly set our lambdas in the ReceiverAccount are fired when any AWS resource is deployed by SenderAccount either by using the console or the AWS SDK for Python (Boto3). The Process begins this way; a Vpc is deployed, then Cloudwatch captures and sends the event through Event Buses to a matching Event Bus in ReceiverAccount in the same region. From ReceiverAccount in us-east-2, Cloudwatch-Event Buses sends it to a Topic SNS named "SnsSendToLambdaOhio" (also in us-east-2) that sends a string with the event info to the ExtractSns function (that is in us-east-1). With this setting we allowteh call event to be passed from the Ohio to Virginia region within ReceiverAccount. Then we can repeat the same process for the other regions that apply.
We need a intermedial"SnsSendToLambdaOhio" SNS topic to "ExtractSNS" Lambda Function  because Tagcreator only processes events in Json format and we must convert the string sent by Sns Topics need to be converted back into json format . the aforementioned "ExtractSNS" lambda passes the event to TagCreator lambda function to process the event and crate the tags .- say the call event is RunInstances and creating the tags with a Key/value is instructed by the code , in our case UserName = UserNamehere, then a newly Instance deployed in a sender account will have its UserName tags with the user name as value created automatically even though the pair of lambda functions are in a receiver account in another region.
As conclusion, this sequence of Cloudwatch - Event Buses - sns topics -and lambda functions from SenderAccount to ReceiverAccount ensures that if we deploy a VPC with a route table in any region from any account in the organization the resources will get a tag with the user name who did the deployment automatically.
You can repeate these steps in any regions and any accounts that apply.

# 1. Create a Role in ReceiverAccount

We create a role in ReceiverAccount with enough permissions to assume role, security token services and create tags. Let us call our Role LambdaAdmin. if you are not too proficient about how to define policies in json just attach AdministratorAccess permission policy to the role.

# 2. Deploy Lambda Functions in ReceiverAccount

We set our lambda functions in virginia region or us-east-1. Any deployment event from any region from any sender account within the organization gets sent to the matching region in RecepientAccount. Once the event is ReceiverAccount from CloudWatch in any region the event is sent to our lambdas thru Sns Topic to ExtractSns Lambda Function.

We use the role, LambdaAdmin,  for the lambda functions to extract the Sns message and create the tags.

## Create or import lambda functions:

**1. ExtractSns:** extracts the message of the event coming from Sns Topics which is a form of a string and return the cloudwatch event back in Json format.  

**2. TagCreatorId:** It only runs when resource creation events happen. Using rescursivity search and extracts all the creation ids of the event to create the tag of who executed the deployment whether it was an access role (Remember we are using Access Roles to jump to any account in the organization from the master account) or an IAM user.

# 3. Bind lambda functions through target

In ExtractSns - When the ExtractSNS function does its job correctly it invokes and returns the CloudWatch event to TagCreatorId function. In ExtractSNS configuration we go to "add destination" and in Destination configuration select source > Asynchronous invocation, Condition > On success, Destination type > Lambda function, in Destination select TagCreatorId. Hit Save

# 4. Create SNS Topic "SnsSendToLambdaOhio" and Subscribe it to Lambda Function "ExtractSNS" in us-east-2 in ReceiverAccount

## Why we need SNS Topic "SnsSendToLambda"?
CloudWatch enable us to use SNS Topics to pass events to any resource targets in another region.  SnsSendToLambdaOhio will be deploy in us-east-2 (Ohio) and is capable to send a message in a form of a string to resources deployed in us-east-1 such as our Pair of Lambda; which it are the ones who combined do the auto-tagging process.  Once our event info already is in CloudWatch ReceiverAccount (yet in us-east-2) we forward the event to our lambdas in us-east-1 by using SNS topic.

Create a Sns Topic called SnsSendToLambdaOhio in us-east-2 in ReceiverAccount with the necessary permissions.
Them create a subscription to publish messages to a Lambda function; select SnsSendToLambdaOhio as Topic ARN, use AWS lambda as Protocol, and select ExtractSNS as endpoint , and hit "Create Subscription".

# 5. Add the necessary permissions in Event Buses in ReceiverAccount in the matching region (for this example us-east-2)
## We need to add permissions in Event Buses but Why? 
Cloudwatch events only passes events between matching regions across accounts. So, If a vpc deployment happens in us-east-2 in SenderAcccount, this event is then captured by cloudwatch event buses in us-east-2 and it is passed to a matching event buses to CloudWatch in the ReceipentAccount in us-east-2.

CloudWatch has a default Event Bus and it is stateless, it means that we have to set the permissions for it to start to receive events from our organization. Therefore, we add the Permission to get all events from any account in the organization.

In Cloudwatch in us-east-2 go to the Event Buses tab in the menu. After, add a new permission. Type = Organization and select Organization ID =  o-myexampleOrgId, and hit add. By this action the default event bus in EventBridge will get a policy with permissions enough to receive event calls from any account in the organization. 
 
The default event bus name is something like this - arn:aws:events:us-east-2:111111111111:event-bus/default

And the resulting Json policy would look something like this:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "7abc6140-77a4-11eb-bd25-3d06a7f5b3fb1614283388244",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-2:1111111111:event-bus/default",
    "Condition": {
      "StringEquals": {
        "aws:PrincipalOrgID": "o-myexampleOrgId"
      }
    }
  }]
}
```

# 5 In ReceiverAccount in us-east-2 Create a CloudWatch event Rule and link it to the SNS topic "SnsSendToLambdaOhio" also in us-east-2)
 Create event pattern that captures all creation events using AWS API Call via CloudTrail and select the previously created Topic SNS. 
In the CloudWacht menu select Rules, In Rules, click Create Rule button, and choose "Custom Event Pattern" and attach this json:

```json
{
  "source": [
    "*"
  ],
  "detail-type": [
    "AWS API Call via CloudTrail"
  ]
}
```

In Targets configure rule details, in name type "SnsSendToLambdaOhio", you may add a description if you choose to, and click "Create Rule".

# 6  In SenderAccount create a matching CloudWatch event Rule in same region (we are using us-east-2 - Ohio Region) and link it to event Bus in matching region in ReceiverAccount.

Create an event pattern the same as the previous one and select as Target the default Event bus in Receveiver Account. Select as Target "Event bus in another AWS Account, Provide the id of ReceiverAccount, per example "111111111111" and create a new role for the execution of the event bus, CloudWatch does it for you...yeah really nice and with the appropiate permissions. the Event Bus Targeted is "arn:aws:events:us-east-2:111111111111:event-bus/default"
A new Role is automatically created with the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "events:PutEvents"
            ],
            "Resource": [
                "arn:aws:events:us-east-2:111111111111:event-bus/default"
            ]
        }
    ]
}
```
**Note:** If you choose to create your own role you can use this example. Here, the account Id for ReceiverAccount is 11111111111111. Replace that number for your receiver account ID with your own designated receiver account.

# 7 Setting up the appropiate permsissions to a Lambda Execution Role in ReceiverAccount to Assume a Role in the SenderAccount
If you haven't already, configure these two AWS Identity and Access Management (IAM) roles:

**LambdaAdmin in ReceiverAccount** – The primary role in receiver account that gives the Lambda functions permission to do its work.

**The Assumed role** – a role in SenderAccount; say LambdaExecute  that the Lambda function in ReceiverAccount assumes to gain across-account resource access, in this case resources from SendingAccount

Therefore, follow these instructions:

1.    **In ReceivingAccount** - Attach the following IAM policy to your Lambda function's role "LambdaAdmin" to assume the role "LambdaExecute" in SendingAccount:

**Note:** Replace 222222222222 with the AWS account ID of SendingAccount.

```json

{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::222222222222:role/LambdaExecute"
    }
}
```
or to allow any member account from the organization let us just tack the "*" in the Resource value.

```json

{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::*:role/LambdaExecute"
    }
}
```

Is noteworthy to say you should keep consistency the Role name created in the Different Accounts of your Organization to use this policy when setting any other region in any other account. For this document we chose to name the Role in SendingAccount, LambdaExecute, for clarity purposes.

2.    **In ReceivingAccount** - Edit the trust relationship of the assumed role in with the following Json:

**Note:** Replace 111111111111 with the AWS account ID of ReceivingAccount.
```json

"Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::111111111111:role/LambdaAdmin"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```
# Deploy a VPC in SendingAccount
Either by console or by AWS CLi SDK for boto3 deploy a Vpc or any resource that you desire.

# 8 Check the tags
Once the deployment process is done we check the tags of the resources newly deployed and verify that there exist a tag with the user ID  and the arn with the creator. That is phow we  ensure the proper functioning of the Lambda AutoTagging function.


### Note: If you want to implement the function in different regions, repeat steps 4 to 6 and replace the region values as applicable



