# Username-Tag-Creator

A Lambda function to create labels with the creator ID to track who did what. The lambda function fires when any AWS resource is deployed using the console or the AWS SDK for Python (Boto3). Once the resource resource is implemented, Cloudwatch sends the event to a Topic SNS that will later be sent to the lambda function allowing it to be executed from any account and region within the organization.

In this case we will implement the function in account A to be executed from account B of the organization

# 1. Create Lambda Functions in Account A
We first create a role with sufficient permissions to deploy AWS resources and attach them to using the lambda function to create labels.

Create lambda functions:

ExtractSns: Allows to extract the SNS message and return the cloudwatch event

ReturnAccesKey: Validate the account id and add the values aws_access_key_id and aws_secret_access_key to the event (edit values 1111111 for your account access
)

CreateTagCreatorID: Using rescursivity it extracts all the creation id of the event to later place the tag of who executed that event regardless of whether it was a role or an IAM user

# 2. Bind lambda functions through target

When the ExtractSNS function is executed correctly, it must invoke and return the information to the ReturnAccesKeys function and when it is executed correctly it must return the information to the CreateTagCreatorID function.

# 3. Create SNS Topic and Subscribe Lambda Function in Account A

Create Topic Sns in account A with the necessary permissions to publish messages in the Lambda function and subscribe to the ExtractSNS lambda function

# 4. Create event bus in Account A
 Create an event bus that allows account A to receive all events from the accounts in the organization

# 5 Create CloudWatch event Rule and link to the SNS topic in Account A
 Create event pattern that captures all creation events using AWS API Call via CloudTrail and select the previously created Topic SNS as destination

# 6  Create CloudWatch event Rule and link to event Bus in Account B
  Create an event pattern the same as the previous one and select as Target Event bus inanotherAWS account here, provide the id of account A and create a role for the execution of the event bus

# 7 Check the tags
We check for the tag managment of the resources newly deployed and verify that a tag with the user ID is present


