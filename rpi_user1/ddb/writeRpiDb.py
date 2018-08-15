import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rpiDb')

table.put_item(
   Item={
	'id': '1',
	'timestamp': '1748240218',
	'flowtemp': '50',
	'waterpressure': '1',
	'IonisationVolt': '85',
	'fanspeed': '200',
    }
)
