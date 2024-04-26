import boto3
import json

aws_access_key_id = 'AKIARLCVVW3ZYCH2UL7E'
aws_secret_access_key = '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'
session = boto3.session.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

def get_ec2_prices(region, instance_type, operating_system, tenancy):
    pricing_client = session.client('pricing', region_name='us-east-1')

    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region},
            #{'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            #{'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': operating_system},
            #{'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            #{'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': tenancy},
            #{'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
        ],
        MaxResults=10
    )
    response1=pricing_client.get_products(ServiceCode='AmazonEC2',
                                          Filters=[
                                              {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                                                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region}],
                                          MaxResults=10)

    if 'PriceList' not in response:
        print(f"No prices found for the specified filters: {region}, {instance_type}, {operating_system}, {tenancy}")
        return []
    
    prices = []
    for price_item in response1['PriceList']:
        price_item_json = json.loads(price_item)
        try:
            price = price_item_json['terms']['OnDemand'][list(price_item_json['terms']['OnDemand'].keys())[0]]['priceDimensions'][list(price_item_json['terms']['OnDemand'][list(price_item_json['terms']['OnDemand'].keys())[0]]['priceDimensions'].keys())[0]]['pricePerUnit']['USD']
            prices.append(float(price))
        except (KeyError, IndexError):
            print(f"Error parsing price for item: {price_item}")

    print(prices)
    return prices

def get_s3_prices(region, storage_type):
    pricing_client = session.client('pricing', region_name='us-east-1')

    response = pricing_client.get_products(
        ServiceCode='AmazonS3',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region},
            {'Type': 'TERM_MATCH', 'Field': 'storageClass', 'Value': storage_type}
        ],
        MaxResults=10
    )

    prices = []
    for price_item in response['PriceList']:
        price_item_json = json.loads(price_item)
        price = price_item_json['terms']['OnDemand'][list(price_item_json['terms']['OnDemand'].keys())[0]]['priceDimensions'][list(price_item_json['terms']['OnDemand'][list(price_item_json['terms']['OnDemand'].keys())[0]]['priceDimensions'].keys())[0]]['pricePerUnit']['USD']
        prices.append(float(price))

    return prices

# Specify the AWS region, instance type, operating system, and tenancy for EC2
ec2_region = 'us-east-1'  # Bahrain region
instance_type = 't3.micro'
operating_system = 'Linux'
tenancy = 'Shared'

# Get the prices of EC2 instances
ec2_prices = get_ec2_prices(ec2_region, instance_type, operating_system, tenancy)

# Print the EC2 prices
print(f"Prices of {instance_type} instances with {operating_system} and {tenancy} tenancy in {ec2_region}:")
for price in ec2_prices:
    print(f"${price} per hour")

# Specify the AWS region and storage type for S3
s3_region = 'me-south-1'  # Bahrain region
storage_type = 'Standard'

# Get the prices of S3 storage
s3_prices = get_s3_prices(s3_region, storage_type)

# Print the S3 prices
print(f"\nPrices of {storage_type} storage in {s3_region}:")
for price in s3_prices:
    print(f"${price} per GB-month")