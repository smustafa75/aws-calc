import boto3
import json
from pkg_resources import resource_filename
import csv
import pandas as pd


#session = boto3.session.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
session = boto3.Session(profile_name="personal")
credentials = session.get_credentials()

def get_ec2_prices(region, instance_type, operating_system, tenancy):
    pricing_client = session.client('pricing', region_name='us-east-1')

    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
 
    Filters=[
      {"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"},
      {"Field": "operatingSystem", "Value": operating_system, "Type": "TERM_MATCH"},
      {"Field": "preInstalledSw", "Value": 'NA', "Type": "TERM_MATCH"},
      {"Field": "instanceType", "Value": instance_type, "Type": "TERM_MATCH"},
      {"Field": "location", "Value": region, "Type": "TERM_MATCH"},
      {"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}
],
MaxResults=10
    )

    if 'PriceList' not in response:
        print(f"No prices found for the specified filters: {region}, {instance_type}, {operating_system}, {tenancy}")
        return []
    
    prices = []
    for price_item in response['PriceList']:
        price_item_json = json.loads(price_item)
        try:
            price = price_item_json['terms']['OnDemand'][list(price_item_json['terms']['OnDemand'].keys())[0]]['priceDimensions'][list(price_item_json['terms']['OnDemand'][list(price_item_json['terms']['OnDemand'].keys())[0]]['priceDimensions'].keys())[0]]['pricePerUnit']['USD']
            prices.append(float(price))
        except (KeyError, IndexError):
            print(f"Error parsing price for item: {price_item}")

    print(prices)
    return prices


def get_region_name(region_code):
    default_region = 'US East (N. Virginia)'
    endpoint_file = resource_filename('botocore', 'data/endpoints.json')
    try:
        with open(endpoint_file, 'r') as f:
            data = json.load(f)
        # Botocore is using Europe while Pricing API using EU...sigh...
        return data['partitions'][0]['regions'][region_code]['description'].replace('Europe', 'EU')
    except IOError:
        return default_region


# Specify the AWS region, instance type, operating system, and tenancy for EC2
# Specify the AWS region, instance type, operating system, and tenancy for EC2
target_region = "me-south-1"
ec2_region = get_region_name(target_region)  # Bahrain region
instance_type = 't3.large'
operating_system = 'Linux'
tenancy = 'Shared'

# Get the prices of EC2 instances
ec2_prices = get_ec2_prices(ec2_region, instance_type, operating_system, tenancy)

# Print the EC2 prices
print(f"Prices of {instance_type} instances with {operating_system} and {tenancy} tenancy in {ec2_region}:")
for price in ec2_prices:
    print(f"${price} per hour")


inst_list= pd.read_csv('inventory.csv')

print(inst_list)