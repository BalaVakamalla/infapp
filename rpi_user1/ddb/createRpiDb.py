#Run this script only for the first time
import boto3

dynamodb = boto3.resource('dynamodb')

table = dynamodb.create_table(
    TableName='rpiDb',
    KeySchema=[
        {
            'AttributeName': 'id', 
            'KeyType': 'HASH'
        },
	{
            'AttributeName': 'timestamp', 
            'KeyType': 'RANGE'
        },
    ], 
    AttributeDefinitions=[
	{
            'AttributeName': 'id', 
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'timestamp', 
            'AttributeType': 'S'
        },
    ], 
    ProvisionedThroughput={
        'ReadCapacityUnits': 2, 
        'WriteCapacityUnits': 2
    }
)

table.meta.client.get_waiter('table_exists').wait(TableName='users')            
print(table.item_count)
