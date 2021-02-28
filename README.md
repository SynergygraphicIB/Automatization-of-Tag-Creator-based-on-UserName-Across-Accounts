# Username-Tag-Creator

We must assume there is and AWS organization set in place with all the proper permissions to ensure that events and sns are to be passed between the accounts.

This Lambda function creates labels with the creator ID to track who did what. The lambda function fires when any AWS resource is deployed either by using the console or the AWS SDK for Python (Boto3). Once the resource is implemented, Cloudwatch sends the event to a Topic SNS that will later be sent to the lambda function allowing it to be executed from any account and region within the organization. In our proyect our Tag-Creator sequence of Lambda Functions are set in Account A and any account from the organization, let is say from Account B we deploy a VPC. This event is filtered when it arrives to Account A based on the event type; any create event, runInstances event or Allocation event. If validated it is sent to the Tag-Creator lambda function so to ensure that any resource being deployed by authorized users gets tagged.

In this case we will implement the lambda functions in account A in us-east-1 to to tag deployment events executed from account B in the organization

# 1. Create Lambda Functions in Account A
First, We set our lambda functions in virginia region, us-east-1. Any deployment event from any region and any account from the organization is sent in form of sns message here.

Then, We create a role with sufficient permissions to deploy AWS resources and attach them to using the lambda function to create labels.

Create lambda functions:

1. ExtractSns: Allows to extract the SNS message and return the cloudwatch event

2. ReturnAccesKey: It Validates the account id and add the values aws_access_key_id and aws_secret_access_key to the event (edit values 1111111 for your account access)

3. CreateTagCreatorID: It runs only resource creation events using rescursivity. It extracts all the creation id of the event to later place the tag of who executed that event regardless of whether it was an access role (Remember we are using Access Roles to jump to any account in the organization from the master account) or an IAM user

# 2. Bind lambda functions through target

When the ExtractSNS function is executed correctly, it must invoke and return the information to the ReturnAccesKeys function and when it is executed correctly it must return the information that later passes it to the CreateTagCreatorID function.

# 3. Create SNS Topic and Subscribe Lambda Function in Account A

Create Topic Sns in account A with the necessary permissions to publish messages in the Lambda function and subscribe to the ExtractSNS lambda function. CloudWatch enable us publish events to any region. Since our lambda functions are base in Virgina (us-east-1) we must ensure that deployments from any region are sent to the lambda function sequence in Account A.

# 4. Create event bus in Account A
 Create an event bus that allows account A to receive all events from the accounts in the organization

# 5 Create CloudWatch event Rule and link to the SNS topic in Account A
 Create event pattern that captures all creation events using AWS API Call via CloudTrail and select the previously created Topic SNS as destination

# 6  Create CloudWatch event Rule and link to event Bus in Account B
  Create an event pattern the same as the previous one and select as Target Event bus in another AWS accountfrom the organization here, provide the id of account A and create a role for the execution of the event bus

# 7 Check the tags
We check for the tag managment of the resources newly deployed and verify that a tag with the user ID is present


# Note: If you want to implement the function in different regions, repeat steps 3 to 7



