# Username-Tag-Creator

We assume You and AWS organization set in place with all the neccesary permissions to ensure that resource creation events and all related info are to be passed between the accounts of the organization. For the sake of this document the ID of our organization is o-myexampleOrgId 

TagCreator Lambda function creates labels with the creator ID to track who did what. This is a highly valuable feature to help us keep track of our resources and reduce the time consuming resource management. We will deploy a pair of lambda functions; ExtractSns and TagCreatorId, in the us-east-1 region in Security Account that we will call ReceiverAccount in our organization to centralize the control and tagging of our resources being deployed in any account of the organization. Also, we will adress the Member Account which is sending the event as SenderAccount to help with the clarity of this doc. Ideally, our lambdas in the ReceiverAccount are fired when any AWS resource is deployed in any SenderAccount either by using the console or the AWS SDK for Python (Boto3). Once the resource is deployed Cloudwatch captures and sends the event through Event Buses to a matching Event Bus in ReceiverAccount. From Cloudwatch-Event Buses in ReceiverAccount to a Topic SNS named  that sends a string with the event info to the ExtractSns function allowing it to be executed from any region within ReceiverAccount, we need this intermedial lambda because Tagcreator only processes events in Json format and we must convert the string sent by SnsSendToLambda back to json format . the aforementioned lambda passes the event to TagCreator function to process the event .- say RunInstances and created the tags with a Key/value as instructed by the code , in our case UserName = UserNamehere. This sequence of sns topic - lambdas our Tag-Creator in ReceiverAccount ensures that if we deploy a VPC with a route table, both resources will get a tag with the use name who did the deployment. 

# 1. Create a Role in ReceiverAccount

We create a role in ReceiverAccount with enough permissions to assume role, security token services and create tags. Let us call our Role TagCreatorLambdaRole. if you are not too proficient about how to define policies in json just attach AdministratorAccess permission policy to the role.

# 2. Deploy Lambda Functions in ReceiverAccount

We set our lambda functions in virginia region or us-east-1. Any deployment event from any region in any sender account within the organization gets sent to the matching region in RecepientAccount. Once the event is ReceiverAccount from CloudWatch in any region the event is sent to our lambdas thru Sns Topic to ExtractSns Lambda Function.

We use the role, TagCreatorLambdaRole,  to the lambda function to create labels.

Create or import lambda functions:

1. ExtractSns: extracts the message of the event coming from Sns Topics which is a form of a string and return the cloudwatch event back in Json format.  

2. TagCreatorId: It only runs when resource creation events happen. Using rescursivity search and extracts all the creation ids of the event to create the tag of who executed the deployment whether it was an access role (Remember we are using Access Roles to jump to any account in the organization from the master account) or an IAM user.

# 3. Bind lambda functions through target

When the ExtractSNS function does its job correctly it invokes and return the CloudWatch event to TagCreatorId function. In ExtractSNS configuration we go to "add destination" and in Destination configuration select source > Asynchronous invocation, Condition > On success, Destination type > Lambda function, in Destination select TagCreatorId. Hit Save

# 4. Create SNS Topic "SnsSendToLambda" and Subscribe Lambda Function "ExtractSNS" in us-east-2 in ReceiverAccount

Why we need SNS Topic "SnsSendToLambda"? CloudWatch enable us to pass events to any region by targeting SNS Topics.  SnsSendToLambdaOhio will be deploy in us-east-2 (Ohio) and still sends a string to resources deployed in us-east-1 (Virginia) which it is where we have deployed our Lambdas. Let us keep in mind that Cloudwatch events only passes events between matchin regions across accounts. So, If a vpc deployment happens in us-east-2 in SenderAcccount, this event is then captured by cloudwatch event buses in us-east-2 will be passed to a matching event buses to CloudWatch in the ReceipentAccount in us-east-2. Hence, our event info already is in ReceiverAccount, yet in us-east-2 (Ohio region). We can forward the event to our lambdas in us-east-1 by using SNS topic to pass the message in a form of a string to resources that may be located in a different region.

Ergo, create a Sns Topic called SnsSendToLambda in us-east-1 in ReceiverAccount with the necessary permissions to publish messages to a Lambda function; use aws lambda and select ExtractSNS as endpoint , and hit "Create Subscription".

# 5. Add the necessary permissions in Event Buses in ReceiverAccount in the matching region (for this example us-east-2)
CloudWatch has a default Event Bus and it is stateless, it means we have to set the permissions for it to start to receive events from our organization. Therefore we add a  Event Buses Permission that allows CloudWatch in  ReceiverAccount to get all events from any account in the organization.
In Cloudwatch in us-east-2 go to the Event Buses tab in the menu. After, add a new permission. Type = Organization and Organization ID =  o-myexampleOrgId, and hit add. By this action the default event bus in EventBridge will get a policy with permissions enough to receive event calls from any account in the organization. 
 
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
  }
}
```

In Targets configure rule details, in name type "SnsSendToLambdaOhio", you may add a description if you choose to, and click "Create Rule"

# 6  In SenderAccount create a matching CloudWatch event Rule in same region (we are using us-east-2 - Ohio Region) and link it to event Bus in matching region in ReceiverAccount.

Create an event pattern the same as the previous one and select as Target the default Event bus in Receveiver Account. Here there the SNS Topic "SnsSendToLambdaOhio" that ultimately sends the message to the lambda function "ExtractSnS". Select as Target "Event bus in another AWS Account, Provide the id of ReceiverAccount and create a new role for the execution of the event bus, CloudWatch does it for you...yeah nice with the appropiate permissions
A new Role is created with the following permissions:
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
Note: For this example the account Id for ReceiverAccount is 11111111111111. Replace that number for your receiver account ID.

# 7 Setting up the appropiate permsissions to a Lambda Execution Role in ReceiverAccount and Assume a Role in SenderAccount
If you haven't already, configure these two AWS Identity and Access Management (IAM) roles:

LambdaAdmin in ReceiverAccount – The primary role in receiver account that gives the Lambda function permission to do its work.
The Assumed role – a role in SenderAccount; say LambdaExecute  that the Lambda function in ReceiverAccount assumes to gain across-account resource access, in this case resources from SendingAccount

Therefore, follow these instructions:

1.    In ReceivingAccount - Attach the following IAM policy to your Lambda function's execution, LambdaAdmin, role to assume the role "LambdaExecute" in SendingAccount:

Note: Replace 222222222222 with the AWS account ID of SendingAccount.

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
or to allow any member account from the organization let us just tack the "*" wild card in Aws account ID

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

Is noteworthy to say you should keep consistency the Role name created in the Different Accounts of your Organization. For this document we chose to name the Role in SendingAccount, LambdaExecute, for clarity purposes.

2.    In ReceivingAccount - Edit the trust relationship of the assumed role in with the following Json:

Note: Replace 111111111111 with the AWS account ID of ReceivingAccount.
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

# 8 Check the tags
We check for the tag managment of the resources newly deployed from Account B and verify that a tag with the user ID is present to ensure the proper functioning of the Lambda Tagging function


# Note: If you want to implement the function in different regions, repeat steps 3 to 7



