# Automatization for Tag Creation with the Username ARN and ID:
This is an open-source solution to Deploy AutoTagging using CloudTrail and channel the event invoke through Cloudwatch Events and EventBrigdge across accounts to a Lambda to tag resources at the moment of creation with the arn of who created, the username ID, and the time of creation. Insofar we have the following services sucessfully tested for auto-tag creation; 
all ec2 services, S3, CloudTrail, CloudWatch, System Manager, Code Pipeline, CodeBuild, Sns, Sqs, IAM, and Cloudformation. Each of those services get a tag with Creator ID, the ARN, and Time of Creation.
### PreFlight Check
1. Intermedial level in Python. So you can adapt and customized the .py files to your needs
2. Basic to intermedial Understanding about how to edit json policies in CloudWatch Rules to change the rule filters base on your use cases since we have not cover every single resource in AWS.
3. An existing AWS Organization
2. A Resource Access Manager (RAM) enabled for the organization
3. One account to centralize the receiving of all creation events known as the "Receiver Account", In our case we deploy or AutoTagging Lambda in the central account to do the tagging.
4. In Every other linked/ sender  account included in your organization will need the following
    A. Cloudwatch log group collecting cloudtrail for every region.
    B. Cloudwatch eventbridge for every region for Receiver account and in the linked accounts in order to create a pipeline to pass the create events from the source region in any linked account to the lambda function in us-east-1 in central or receiving account.

## List of Resources Used or Deployed

### IAM Roles
We need the AutoTagging Lambda in receiver account permission to assume a role from a linked account to access resources, such as Ec2, S3, SNS. And  
**AutoTaggingMasterLambda** - Resource Role to give permission to lambda autotagging function in receiver account to assume role in linked account with AWS STS service
More Details about the policies we need in the Steps section of this document.

**AutoTaggingExecuteLambda** - Role we create in every linked account whose policy only has limited permissions to do the tagging of newly deployed resources. This is the role that  AutoTaggingMasterLambda from Receiver Account assumes to make possible the recollection of creation events across accounts.
See AutoTagginPolicy.json
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

### CloudWatch Rule
**EventAutoTagging** - This rule filters create events coming from AWS API Call via CloudTrail that start with the prefix "Create" and "Put". Also RunInstances; which is the one to launch a new EC2 instance, and "AllocateAddress" for creating an Elastic IP Adress. We used Prefix Matching in order to reduce the json code. There are about 650 create events for the different aws services and about 147 put events. So our rule may need little if nothing updating and upgrading to cover new events launched by AWS.

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
We will create a rule for every region in the linked account that we want to include in the Auto Tagging and a matching rule in every matching region in the receiver account
### Sns Topics
**AutoTaggingSNS** - The SNS Topic that are to be deployed in every active region of the Receiver Account.  This SNS Topic helps to centralize collection of creation events across all regions and all accounts we want to do the auto tagging for throughout the organzation. We set it up as target for the rule "EventAutoTagging" in CloudWatch in order to pass the event to lambda. Sns is one of the AWS services that can deliver events across regions, so in order to make our pipeline as scalable as possible we are using SNS Topics.

### Event Buses Permissions
**Add Permission** - Default event bus accepts events from AWS services, PutEvents API calls, and other authorized accounts. Wd manage permissions on the default event bus to authorize the linked account to share their events with the Receiver Account by adding your default event bus as a target to the rules.In CloudWatch, in the Event Buses tab you have to go to permissions and click "Add Permission". Once the Add Permission dialog box opens > select Type: Organization, Organization ID:	My organization (Your organization Id should be preselected). Then click "Add" and sharing events with any account within the organization is enable. We have to repeat the same procedure in the Receiver Account in the matching region. Therefore, if we add the permission in us-east-1 in cloudwatch - linked account, we have to do the same procedure in us-east-1 -CloudWatch - Receiver Account.

### Lambda function

**AutoTagging** - Lambda function we deploy in the Receiver Account in the us-east-1 region. It Auto creates Tags with the creator ID, the ARN, and the time stamp to track who did what and when. This is a highly valuable feature to help keep tracking resources and reduce the time consuming resource management. The lambda  will need to be deployed into the Receiver account in the us-east-region and it is going to be the target point for the SNS Topic "AutoTaggingSNS".

## How does it work this pipeline? 
We are going to make a school registration analogy. John Doe enters a school in Fort lauderdale, but the admin office is in Boca Raton, FL. Regardless to what school any student enters all registration tags with most of the student info are done and printed in Boca Raton. Hence, the moment of registration John files a sheet his social security number of FloridaID, Age, Grade which he is going to attend, Date of registration, and who was the school officer who did the registration. John entering is the creation event, and all the data info related to his registration is the metadata that has to be carried from the origin school in Ft. Lauderdale to the Admin Office in Boca. The different stages in between are the steps in the pipeline to make possible to create the tags for John to have in his shirt and to be easily identifiable by the teachers and other staff of the school.
At the Ft. Lauderdale School of Receiver Account we will deploy a resource (John´s entering the school) in us-east-1, let`s say a Vpc in the AWS environment, hence a creation event is generated. 
In every school there is long-timer in charge of recording everything that happens, who did what? and that is  Mr. Snoopy - AWs CloudTrail is a the service that records API activity in your AWS account and logs the creation event - CreateVpc. (or John Entering the school and filing his info). CloudTrail trail detects and respond to AWS resource creation API events and it is required for this auto-tagging solution just like anything that happens at the school escapes to Mr. Snoopy . The Amazon EC2 CreateVpc API CloudTrail event provides a lot of tagging information. For example, you can extract:
User ID of the entity that created the resource from the principalId key
The IAM role the entity assumed during resource creation from the arn key.
The date/time of resource creation from the eventTime key.
The Vpc ID and other metadata contained in the event. This info is akin to John´s metadata we talked about, his age, when he entered the school, who did the registration, etc.
Then at the school there is an officer whose role is to monitor which event are to be filtered and sent to the relevant parts. In our school that is Mr. Cloudwatch with a cousin service in AWS with the same name AWS CloudWatch. For Mr. CloudWatch just like his cousing in AWS need a rule to follow to see what kind of events he is looking for and where he is going to send it for further processing. So, John after being done with Mr. Snoopy shows up at Mr. CloudWatch with a shiny sheet with all his info and Mr. CloudWatch must decide what action he must do base of set of give rules he has at hand. Well, John  is a new student and he needs a  tag with certain info printed on. 
Damn, tags are not done at the school. Mr. CloudWatch must send John with registration info to Boca Raton so he gets issued a tag with the necessary information required by the school. Following a set of pre-established rules named "EventAutoTagging" Mr. Cloudwatch matches the event and he knows that he has to put John a.k.a CreateVpc and all metadata in the school bus wich has the necessary settings to go from Ft Lauderdale to the Admin Office in Boca Raton to the the tagging (event bus) on route to Boca Raton admin office (Receiver Account) wherein the tags are created (us-east-1 in Receiver Account where our Autotag lambda is parked)
In Aws terms - EventAutoTagging rule matches the event base on the prefix "Create" and the rule is triggered on the Amazon EC2 CreateVpc API action. The event metadata is sent to the Event Bus which passes the event to the event bus in us-east-1 in ReceiverAccount. 
Jonh arrives to Boca Raton to the admin office at the reception. At Boca Raton there is another Mr. CloudWatch with the same functions than our Mr. CloudWatch from Ft. Lauderdale and exactly the same "EventAutoTagging" rule that the former has. he takes a look at John and his file and decides - base on the "EventAutoTagging" rule he directs Jonh the the right office for tagging. For scalability purposes that office is Mr.SNSToAutoTaggingMasterLambdaNV who also has a cousin with a matching name in AWS. SNS topic SNSToAutoTaggingMasterLambdaNV. Why this step? Mr. SNSToAutoTaggingMasterLambdaNV or his AWS Cousin has the capability to work from across regions and he helps us to bring another Johns (or Creation events) across regions. In our practical case with another new students we can replicate the same settings for another schools in Florida- a Mr. CloudWatch and a Mr.SNSToAutoTaggingMasterLambda in every school that wants to get the benefits of the tagging department in Boca Raton. In AWS Terms a Cloudwatch Rule with and SNS topic as target in every region we are to include in the autotagging lambda function.
Insofar, John or - CreateVpc is in the Receiver account in us-east-1 passing thru SNS topic SNSToAutoTaggingMasterLambdaNV. The endpoint for this topic is the lambda function - AutoTagging. 
The AutoTagging lambda function is the office of destination for John and his file with all the registration info or the CreationVpc event with the metadata. It is noteworthy that by passing the event thru SNS topics the event arrives to the lambda function in a form of string. Yet our lambda function firstly converts the string into a json readable format.
The purpose of this pipeline is to centralize the control and tagging of resources being deployed in any linked account of the organization - or using our analogy to standardize the registration and tagging of new students no matter from what school from Florida they are coming from.
As a result The lambda "AutoTagging" function is fired by SNS topic SNSToAutoTaggingMasterLambdaNV when any AWS resource is deployed by Sender or linked account either by using the console or the AWS SDK for Python (Boto3). The newly deployed resource get three tags: User Name, Creator ID, and Create at. which are the basis for any good resource cost control and managment. 
Following this procedure we can repeat the same process for the other regions or any other linked accounts within the organization that we want to include in the autotagging. 
By using as intermedial step in the pipeline allow us to modify this function to even use it in a single account with very little modifications. We have a separate Git where we explain how you can do the autotagging in a single account.

# 1. Log in into you account designated as Receiver Account 
This is the account we are going to use to centralized the Autotagging for any linked Account. 
Be sure you are in US East (N. Virginia)us-east-1 for most of the purposes of this project, though some AWS Services are global, among those Identity and Access Management (IAM).

# 2. Create a Role "AutoTaggingMasterLambda" in Receiver Account

We create a "AutoTaggingMasterLambda" role in ReceiverAccount with enough permissions to execute lambnda, to assume role in the linked accounts and security token services in order to do the auto-tagging. Here we have defined the policies in json with least priviledge access to allow the lambda function to perform its functions:
1.- AWSLambdaExecute (AWS Managed policy) This is the basic execution policy for any role created along with a lambda function.
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::*"
        }
    ]
}

2.- AutoTaggingMasterLambda (Manage Policy)
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::*:role/AutoTaggingExecuteLambda"
    }
}

This is a least privledge AWS STS  policy. Notice the "*" in the resource arn, instead typing the linked account number we do the asterisk wildcard in order to enable any linked account in the organization as long as we always use the same role name "AutoTaggingExecuteLambda" en each linked account.
a. Click the Services tab and look for Identity and Access Management (IAM) or just type it in the text box IAM and Click IAM Manage access to AWS resources.
 ¨{insertar imagen aqui iam-1)
b.-  On the Menu on the left go to Roles and when it opens Click the "Create role" button.
{insertar imagen iam-2 aqui}
c.-

