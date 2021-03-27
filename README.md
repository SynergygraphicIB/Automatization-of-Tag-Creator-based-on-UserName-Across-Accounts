# Automatization for Tag Creation with the Username ARN and ID:
This is an open-source solution to deploy **AutoTagging** using `CloudTrail` and channel the event invoke through `Cloudwatch Events` and `EventBrigdge` across accounts to a endpointt that is going to be a lambda function` to `tag resources` at the moment of creation with the arn of who created, the username ID, and the time of creation. 
Insofar we have the following services sucessfully tested for auto-tag creation; `all ec2 services, S3, CloudTrail, CloudWatch, System Manager, Code Pipeline, CodeBuild, Sns, Sqs, IAM, and Cloudformation`. Each of those services get a tag with Creator ID, the ARN, and Time of Creation.

### PreFlight Check
1. Intermedial level in Python. So you can adapt and customized the `.py` files to your needs
2. Basic to intermedial Understanding about how to edit json policies in `EventBridge Rules` to change the rule filters base on your use cases since we have not cover every single resource in AWS.
3. An existing `AWS Organization`
2. A `Resource Access Manager (RAM)` enabled for the organization
3. One AWS Account to centralize and receive all creation events known as the "the Central or *Receiver Account"*. Here is where we deploy **AutoTagging Lambda function**.
4. In Every other linked/ sender  account included in your organization will need the following
    A. `Cloudwatch` log group collecting `cloudtrail` for every region.
    B. Cloudwatch and Eventbridge rules for every region for Receiver account and in the linked accounts in order to create a pipeline to pass the create events from the source region in any linked account to the lambda function in us-east-1 in central or receiving account.

## List of Resources Used or Deployed
### Two AWS Accounts subscribed to an Organization
**A Receiver/Central AWS Account**
One existing AWS account attached to and organization that we are going to use to deploy the auto tagging lambda function in us-east-1 and that for the purpose of this project its Id will be 111111111111

**A Sender/linked AWS Account**
A Second existing AWS account that for the purpose of this exercise we will have an Id 222222222222 and that is attached to and organization. We are going to deploy AWS resources in us-east-1, action which will create an event. This event will be sent through a pipeline that will have as endpoint the **lambda autotagging** in us-east-1 in account 111111111111. Thus fulfilling the purpose of centralizing auto-tagging for any linked account that we do the setting we are going to explain in this document.

**AWS Organizations**
An Existing AWS organization that for the purpose of this project has an ID my-org-id-1234
**Resource Access Management (RAM)**
Must be sure that Enabling sharing with AWS Organizations. In the Central Account go to ```Services Tab > type RAM in the search for services text box > select Resource Access Manager > In the RAM menu go to Settings - "Enable sharing with AWS Organizations"``` must be checked out.

***{poner screenshot aqui EnableAWSOrganizations.jpg}***

### IAM Roles
We need the **AutoTagging Lambda** in *Receiver Account* a role with permission to assume a role in a linked account to create resources, such as `Ec2, S3, SNS`. In addition we have to follow the least priviledge access principle when attaching or creating policies for such roles.

**AutoTaggingMasterLambda** - Resource Role to give permission to lambda autotagging function in *receiver account* to assume role in *linked account* with AWS STS service
More Details about the policies we need in the Steps section of this document.

**AutoTaggingExecuteLambda** - Role we create in every *linked account* whose policy only has limited permissions to do the tagging of newly deployed resources. This is the role that  **AutoTaggingMasterLambda** from *Receiver Account* assumes to make possible the recollection of creation events across accounts.
See `AutoTagginPolicy.json`

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "sqs:UntagQueue",
                "logs:*",
                "iam:TagMFADevice",
                "codepipeline:ListTagsForResource",
                "cloudformation:UpdateStackSet",
                "cloudformation:CreateChangeSet",
                "iam:TagSAMLProvider",
                "codebuild:UpdateProject",
                "s3:DeleteJobTagging",
                "ssm:RemoveTagsFromResource",
                "cloudtrail:AddTags",
                "ssm:AddTagsToResource",
                "codepipeline:GetPipeline",
                "cloudformation:UpdateStack",
                "s3:PutObjectTagging",
                "s3:DeleteObjectTagging",
                "iam:UntagSAMLProvider",
                "s3:DeleteStorageLensConfigurationTagging",
                "ec2:CreateTags",
                "ssm:GetParameters",
                "s3:DeleteObjectVersionTagging",
                "iam:TagPolicy",
                "codepipeline:UntagResource",
                "cloudformation:UntagResource",
                "resource-explorer:*",
                "sns:TagResource",
                "mediastore:UntagResource",
                "cloudformation:UpdateStackInstances",
                "iam:UntagRole",
                "ec2:DeleteTags",
                "codepipeline:CreatePipeline",
                "iam:TagRole",
                "s3:ReplicateTags",
                "cloudformation:UpdateTerminationProtection",
                "codepipeline:CreateCustomActionType",
                "sns:UntagResource",
                "codepipeline:TagResource",
                "s3:PutBucketTagging",
                "tag:*",
                "codebuild:BatchGetProjects",
                "s3:PutStorageLensConfigurationTagging",
                "s3:PutObjectVersionTagging",
                "s3:PutJobTagging",
                "iam:UntagServerCertificate",
                "iam:TagUser",
                "iam:UntagUser",
                "sqs:TagQueue",
                "ssm:ListTagsForResource",
                "iam:UntagMFADevice",
                "iam:TagServerCertificate",
                "cloudformation:TagResource",
                "iam:UntagPolicy",
                "iam:UntagOpenIDConnectProvider",
                "iam:UntagInstanceProfile",
                "iam:TagOpenIDConnectProvider",
                "mediastore:TagResource",
                "codepipeline:PutWebhook",
                "cloudtrail:RemoveTags",
                "iam:TagInstanceProfile"
            ],
            "Resource": "*"
        }
    ]
}
```
### EventBridge Rule
**EventAutoTaggingRule** - This rule filters create events coming from `AWS API Call via CloudTrail` that start with the prefix `"Create"` and `"Put"` and `RunInstances`; which is the one to launch a new EC2 instance, and `"AllocateAddress"` for creating an Elastic IP Adress. We used Prefix Matching feature in order to reduce the need to update the rule written in json format  . There are about 650 create events for the different aws services and about 147 put events. So our rule may need little if nothing updating and upgrading to cover new events launched by AWS.

```json
{
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventName": [
      {
        "prefix": "Create"
      },
      {
        "prefix": "Put"
      },
      "RunInstances",
      "AllocateAddress"
    ]
  }
}
```

We will create a rule for every region in the *linked account* that we want to include in the **Auto Tagging** and a matching rule in every matching region in the receiver account

### Sns Topics
**SnsSendToLambda** - The `SNS Topic` that have to be created in every region of the *Receiver Account* where we want to do deployments.  This `SNS Topic` helps to centralize collection of creation events from all regions and all accounts and sent the event metadata to us-east-1 to the **Autotagging lambda** function that we want to do the auto tagging for throughout the organzation. We set this sns topic it as target for rule **"EventAutoTagging"** in `CloudWatch` in order to pass the event to lambda (then again from any region). Sns is one of the few AWS services that can deliver event data across regions, so in order to make our pipeline as scalable as possible we are using `SNS Topics`.
In our project a `CloudWatch Rule` could be deployed in us-east-2 or us-west-1 and stil relay the event using `SNS Topic` as target to pass events to any resource targets in another region, in this case a lambda function in us-east-1. 

### Event Buses Permissions in CloudWatch
**Add Permissions in Event Buses** - 
`CloudWatch` has a default Event Bus and it is stateless, it means that we have to set the permissions for it to start to receive events from the organization. Therefore, we add the Permissions to get all events from any account in the organization in the central of receiver account. Default event bus accepts events from AWS services, `PutEvents API calls,` and other authorized accounts. 

In Addition, We must also manage permissions on the default event bus of the *linked account* to authorize it to share their events with the *Receiver Account* and to add it as as a target to the rules in in `CloudWatch`. 

## We need to add permissions for this particular architecture in Event Buses but Why? 
`Cloudwatch` events only passes events between matching regions across accounts, in this case between *linked account/ us-east-1* and *Receiver Account / us-east-1*. Then, when a Vpc deployment happens in us-east-1 in the *linked account*, this event is then captured by `cloudwatch event buses` and it is passed "through the bus" to a the event bus in `CloudWatch` in *Receiver Account* in us-east-1 as well.

We have to do this permission setting from every region we want to incorporate in the autotagging process and that is why we use the organization, to reduce the modifications needed in the *receiver account*. Once we set the permissions in a certain region in *receiver account* it is ready to pass events from any *linked account* in the organization, instead adding each new account at once.

### Lambda function

**AutoTagging** - Lambda function we deploy in the *Receiver Account* in the us-east-1 region. it converts the event coming from `SNS Topic`  **"AutoTaggingSNS"** in string and converts it back into `json` format. Then, It Auto creates Tags with the creator ID, the ARN, and the time stamp to track who did what and when. This is a highly valuable feature to help keep tracking resources and reduce the time consuming resource management. The lambda  will need to be deployed into the *Receiver account* in the us-east-region and again it the target for the `SNS Topic` **"AutoTaggingSNS**".

## How does it work this pipeline? 
The lambda **"AutoTagging"** function in *Receiver Account* is fired when any AWS resource is deployed by Sender or *linked account* either by using the console or the AWS SDK for Python (Boto3). The newly deployed resource get three tags: User Name, Creator ID, and Create at. which are the basis for any good resource cost control and managment.

A Vpc is launched in us-east-1 in *Linked Account*, but the **Auto-tagging** lambda function is in *Receiver Account* in us-east-1. No matter what creation or deployment event happens, all tagging is going to be done by the **AutoTagging** lambda function . Hence, at the moment of deployment a metadata is generated; Date of creation, and who was the creator, ARN of the creator, etc. Thus the meta data has to be passed from the original point - *linked account* 222222222222 to lambda function in receiver account to do the tagging.

`AWS CloudTrail` records API activity in *sender account* 222222222222 account and logs the creation event - `"CreateVpc`". The Amazon EC2 CreateVpc API CloudTrail event provides a lot of tagging information. For example:
```
User ID of the entity that created the resource from the principalId key
The IAM role the entity assumed during resource creation from the arn key.
The date/time of resource creation from the eventTime key.
The Vpc ID and other metadata contained in the event. 
```

Then, `CloudWatch` filters the creation event base on **EventAutoTaggingRule.** This rule looks for any event that has `"Create"` as a prefix"  and sends the metadata event to the default event bus that is connected to the event bus in *Sender Account* - Account ID 111111111111 us-east-1 too. 

Now the metadata of the event is in *Sender Account*. `CloudWatch` filters and matches the event and sends it to **SNSToAutoTaggingMasterLambda**.

**SNSToAutoTaggingMasterLambda** passes the event to The **AutoTagging lambda function** in a form of string. 

**Autotagging lambda function** is fired. firstly converts the string into a `json` readable format.

The purpose of this pipeline is to centralize the control and tagging of resources being deployed in any *linked account* of the organization - or using our analogy to standardize the registration and tagging of new students no matter from what school from Florida they are coming from.

Following this configuration we can repeat the same process for the other regions in any other linked accounts within the organization that we want to include in the **autotagging.**

By using *SNS Topics* as intermedial step in the pipeline allow us to modify this function to automate tagging it in a single account with very little modifications. We have a separate Git where we explain how you can do the autotagging in a single account.

# 1. Log in into you account designated as Receiver Account 
This is the account we are going to use to centralized the **Autotagging** for any linked Account. 

Be sure you are in US East (N. Virginia) us-east-1 for most of the purposes of this project, though some AWS Services are global, among those Identity and `Access Management (IAM).`

# 2 Setting up the appropiate permsissions to a Lambda Execution Role in ReceiverAccount to Assume a Role in the SenderAccount
Create a role in *Receiver Accoun*t that has enough permissions to execute lambda the auto-tagging lambdafunction and to assume tag creation role in *Sender Account*. Follow the steps:
**Create a rule to allow AutoTaggingMasterLambda role in receiver account  to assume any role named AWSLambdaBasicExecutionRole in any linked/ sender account **

a.- Be sure you are in *Receiver Account* 111111111111
b.- At the console screen go to services and type in the text box `"IAM"` or under All
    ```Services > Security, Identity, & Compliance > IAM```
c.- In `Identity and Access Managment (IAM) menu > go to Policies` and click `"Create policy"` button


***{poner imagen}***

d.- Click Create policy next.
e.- In Create policy window select JSON tab. Click and paste the following policy and click the "Next: tags" button:

```json
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::*:role/AutoTaggingExecuteLambda"
    }
}
```

h.- Click "Next: Review" button
i.- In Review policy window in Name type **"AutoTaggingMasterLambdaPolicy"**
j.- In Description type "Rule to enable **AutoTaggingMasterLambda** Role to assume any role named "AutoTaggingExecuteLambda" in any linked account" and click "Create policy"

**{pegar imagen aqui}**

#### Create AutoTaggingMasterLambda role in receiver account
a.- Be sure you are in `Receiver Account` 111111111111
b.- At the console screen go to services and type in the text box `"IAM"` or under All services > Security, Identity, & Compliance > IAM
d.- In Create Role window > Under "Select type of trusted entity" keep AWS service as your choice
e.- In "Choose a use case" select "Lambda" and click "Next: Permissions" button
{pegar imagen aqui}
f.- In next window, under Attach Permissions policies in the search box type "lambdabasic"
g.- Checkmark the AWS managed policy **"AWSLambdaBasicExecutionRole"**
h.- Under Create policy clear the Search box 
i- Click Filter policies and checkmark "Customer managed"
j.- Scroll down and checkmark the Customer managed policy **"AutoTaggingMasterLambdaPolicy"**
k.-  Click "Next:Tags" button  and click "Next: Review" button too
l.- Under Review, in Role name `*` type **AutoTaggingMasterLambda.** 
m.- In Role description type "Resource Role to give permission to lambda autotagging function in *receiver account* to assume roles named **"AutoTaggingExecuteLambda"** in linked account with AWS STS service". Observe that in Trusted entities you got AWS service: lambda.amazonaws.com and two policies attached to the role.

**{pegar imagen aqui}**


n.- Click "Create Role Button"

**{pegar screenshot aqui}**

Is noteworthy to say you should keep the same role name **"AutoTaggingExecuteLambda"** when setting any other new linked accounts in your organization to not keep adding new policies into this role

# 3. Deploy Autotagging Lambda Function in Receiver Account

We set our lambda function in virginia region or us-east-1. This is the endpoint for any deployment or creation event happening in any region in any account that is configured in the pipeline for **Auto-tagging* and in this lambda function. 

Create a **AutoTagging** lambda function with the console>

a.- In the console click the services tab and look for Lamdba under 
```
All services > Compute > Lambda or just type lambda in the text box. then hit Lambda
```
b.- In the AWS lambda window go to Functions.
c. Click the "Create function" buttom.
d. You will the following options to create your function Author from scratch, Use blueprint, Container Image, and Browse serverless app repository, choose Author from scratch.
e. In Function name type **"AutoTagging"** or any name you choose to, in Runtime look for Python 3.8
f.- In Permissions - click Change default execution role and select "Use an existing role". In the dialog box that opens up look for "AutoTaggingMasterLambda", this is the role we created in the previous step.
g.- Click "Create function" button
{poner una imagen aqui en donde se ilustre el resulatdo de estos pasos}
h.- Under Code source > In Environment click `lambda_function.py`
i.- Delete all existing code an replace it with the code provided in the `TagCreatorID.py` file
j.- Once you paste the new code click "Deploy"
j.- In the Code Source menu click Test
k.- In Configure test event leave Create new test event selected, In event name type create_tags and click "Create Test" Button

{pegar foto aqui}

# 4. Create SNS Topic 
Create a topic - **"SNStoAutoTaggingLambda"** and Subscribe it to Lambda Function **"AutoTagging"** *in ReceiverAccount*. So let us follow the next steps:

a.- Be sure you are in us-east-1 region (SNS works across regions, but still is a regional resource)
b.- At the console screen go to services and type in the text box "sns" or under All ```
```
services > Aplication Intergration > Simple Notification Service
```
c. -CLick at the Simple Notification Service
e.- In the menu to the left click Topics and then The `"Create Topic"` orange buttom.
f.- In Create topic window choose Stardard, In Name type **"SNStoAutoTaggingLambda"**
g.- In the Access policy section we keep the Basic method 
h.- Click Create topic buttom. The topic is created.
{poner una imagen aqui en donde se ilustre el resulatdo de estos pasos}
i.- Now, we create the subscription. Click the Create subscription button.
j. In Details > Topic ARN look for the topic created in the previous steps
k.-In Protocol choose AWS Lambbda and look for the ARN of the lambda function **AutoTagging.**
l.- Hit the Create Subscription Button. Voila! the subscription is done.
{poner una imagen aqui en donde se ilustre el resulatdo de estos pasos}

# 5. In `CloudWatch` in *Receiver Account* add the necessary permissions to `Event Buses` 
In Event Buses we have to manage event bus permissions to enabble passing event metadata:
a.- Be sure you are in us-east-1 region in *Receiver Account*
b.- At the console screen go to services and type in the text box `"Cloudwatch"` or under All
```
services > Management & Governance > Cloudwatch
```
c.- In `Event Buses` item in the menu go to `Event Buses`
d.- Under the permissions section click add permission. A "Add Permission" dialog box opens up. In the Type text box click the arrow and select Organization. In Organization ID select My Organization, your organization Id "my-org-id-1234" should be pre-populated. Hit the Add blue button.

***{poner una imagen aqui en donde se ilustre el resulatdo de estos pasos}***

A Resource-based policy for default event bus is automatically generated.
To check the policy go to ```Amazon EventBridge > Event buses > default``` and you check Permissions tab you will see a Resource-based policy like this
The default event bus name is something like this - `arn:aws:events:us-east-1:111111111111:event-bus/default`

***{poner una imagen aqui en donde se ilustre el resulatdo de estos pasos}***

And the resulting Reso policy would look something like this:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "this-is-how-i-pass-events-btwn-accounts-in-my-org",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-1:111111111111:event-bus/default",
    "Condition": {
      "StringEquals": {
        "aws:PrincipalOrgID": "my-organization-id"
      }
    }
  }]
}
```

**{poner una imagen aqui en donde se ilustre el resulatdo de estos pasos}***

# 6 In Receiver Account create an EventBridge Rule in us-east-1 -or Virginia Region and use as target SnsSendToLambda.
Create a rule that captures all creation events in `Sender Acccount` using `AWS API Call via CloudTrail` and select **SnsSendToLambda** as target:
a.- Be sure you are in `us-east-1` region in `Receiver Account` 
b.- At the console screen go to services and type in the text box `"EventBridge"` or under
```All services > Application Integration > Amazon EventBridge```

***{copiar imagen aqui}***
c.- In the Amazon EventBridge menu select Rules and click "Create Rule" button
d.- Under Name and Description > Name type **"EventAutoTaggingRule**"
e.- Add a Description **"Rule to send creation events to SnsSendToLambda"** if you choose to, it is optional
f.- In Define pattern choose ```"Event pattern" > Custom Pattern```
g.- Copy paste the following json pattern
```json
{
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventName": [
      {
        "prefix": "Create"
      },
      {
        "prefix": "Put"
      },
      "RunInstances",
      "AllocateAddress"
    ]
  }
}
```
Notice that this is exactly the same rule we used in CloudWatch in Receiver Account

***{poner foto aqui donde se vea este verguero}***

h.- In Select event bus leave it as it is, `"AWS default event bus"` and `"Enable the rule on the selected bus"`
i.- In Select` Targets > in Target click the text box, scroll up and select "SNS Topic"`
j.- In Topic text box select **"SnsSendToLambda"**
k.- Click `"Create Rule" `button. 

**{poner imagen aqui}**

# 7  In *SenderAccount* create a matching `EventBridge Rule` in same region (we are using us-east-1 - Virginia Region) and use as target the` event Bus `in matching us-east-1 region in *Receiver Account*.
Create a rule that captures all creation events in `Sender Acccount` using `AWS API Call via CloudTrail` and select default event bus as target:
a.- Be sure you are in us-east-1 region in `Sender Account` 
b.- At the console screen go to services and type in the text box `"EventBridge"` or under ``All services > Application Integration > Amazon EventBridge```

**{copiar imagen aqui}**

c.- In the ```Amazon EventBridge menu select Rules and click "Create Rule" button``
d.- Under Name and ```Description > Name type "EventAutoTaggingRule"``
e.- Add a Description "Rule to send creation events to default event bus in receiver account" if you choose to, it is optional
f.- In Define pattern choose ``"Event pattern" > Custom Pattern``
g.- Copy paste the following json pattern
```json
{
  "detail-type": [
    "AWS API Call via CloudTrail"
  ],
  "detail": {
    "eventName": [
      {
        "prefix": "Create"
      },
      {
        "prefix": "Put"
      },
      "RunInstances",
      "AllocateAddress"
    ]
  }
}
```
Notice that this is exactly the same rule we used in CloudWatch in Receiver Account

***{poner imagen aqui}***
h.- In Select event bus leave it as it is, ```"AWS default event bus" ```and "Enable the rule on the selected bus"

***{poner foto aqui donde se vea este verguero}**
i.- In ``Select Targets > in Target click the text box, scroll up and select "Event bus in another AWS account"``
j.- In Event Bus text box type `"arn:aws:events:us-east-1:111111111111:event-bus/default"` (be sure to replace the Account number with your designated Receiver Account)
k.- Select "Create a new role for this specific resource". EventBridge will create a role for you with the right permissions to pass events into the event bus. Click configure details button.

**{poner imagen aqui que muestre esta vaina}**
l.- Click "Create Rule" button. 
**{poner imagen aqui}**

# 8. Add the necessary permissions to Event Buses in CloudWatch in Sender Account
In `Event Buses` we have to manage event bus permissions to enabble passing event metadata:
a.- Be sure you are in us-east-1 region in *Sender Account*
b.- At the console screen go to services and type in the text box `"Cloudwatch"` or under ```All services > Management & Governance > Cloudwatch```
c.- In `Event Buses` item in the menu go to `Event Buses`.
d.- Under the permissions section click add permission. A `"Add Permission"` dialog box opens up. In the Type text box click the arrow and select Organization. In `Organization ID `select My Organization, your organization Id `"my-org-id-1234"` should be pre-populated. Hit the Add blue button.

***`{poner imagen aqui}
***`
A Resource-based policy for default event bus is automatically generated.
To check the policy go to ```Amazon EventBridge > Event buses > default ```and you check Permissions tab you will see a Resource-based policy like this
The default event bus name is something like this - `arn:aws:events:us-east-1:222222222222:event-bus/default`
**{poner una imagen aqui en donde se ilustre el resulatdo de estos pasos}**
And the resulting Reso policy would look something like this:
```json
{
  "Version": "2012-10-17",
  "Statement": [{. 
    "Sid": "this-is-how-i-pass-events-btwn-accounts-in-my-org",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "events:PutEvents",
    "Resource": "arn:aws:events:us-east-1:222222222222:event-bus/default",
    "Condition": {
      "StringEquals": {
        "aws:PrincipalOrgID": "my-organization-id"
      }
    }
  }]
}
```
{poner imagen aqui}

# 9. Deploy a VPC in *SendingAccount*
Either by console or by AWS CLi SDK for boto3 deploy a Vpc or any resource that you desire.
Using the AWS Console:
a. In *Sender Account,* in us-east-1 go to the resource tab
b. In the services search text box type vpc or under "Networking & Content Delivery" look for VPC. Click VPC
c.- In the menu to the left click "Your VPCs"
d.- In Your VPCs window click "Create VPC" button
{pegar imagen aqui mostrando esto}
e.- In Create VPC > VPC settings > Name tag type test-project or any name you want to.
f.- In IPv4 CIDR block type 10.0.0.0/24, leave the rest of the settings as it is.
g.- Click the "Create VPC" button.
{pegar imagen aqui}
h.- You will be redirected to the newly created vpc window details. under the "Tags" tab click it and check for the tags. 
**{pegar imagen aqui}**
You will see the Following tags; create_at, UserName, Name, and creatorId. 


### Note: To implement the function in different regions, repeat steps 4 to 8 and replace the region values as applicable
