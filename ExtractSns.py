import json

def lambda_handler(event, context):
    # next line gets the string from sns and converts it into json format again
    message = json.loads(event['Records'][0]['Sns']['Message'])
    # we print the result in text to see what is coming from the sns topic
    print("JSON: " + json.dumps(message))
    # sets the info to be sent to the create tags lambda function
    return message
