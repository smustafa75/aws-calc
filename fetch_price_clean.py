#!/usr/bin/env python3
"""
AWS EC2 Price Fetcher

This script fetches EC2 instance pricing from AWS Pricing API based on
instance types specified in an input file (CSV or Excel).
"""

import argparse
import boto3
import json
import pandas as pd
import sys
import os
from pathlib import Path
import botocore.exceptions


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fetch AWS EC2 pricing information')
    parser.add_argument('-i', '--input', required=True, help='Input file path (CSV or Excel)')
    parser.add_argument('-o', '--output', help='Output file path (CSV or Excel)')
    parser.add_argument('-r', '--region', default='me-south-1', help='AWS region code (default: me-south-1)')
    parser.add_argument('-p', '--profile', default='lab', help='AWS profile name (default: lab)')
    parser.add_argument('-os', '--operating-system', default='Linux', 
                        help='Operating system (default: Linux)')
    parser.add_argument('-t', '--tenancy', default='Shared', 
                        help='Tenancy type (default: Shared)')
    
    # Handle argument parsing errors gracefully
    try:
        args = parser.parse_args()
        return args
    except SystemExit:
        print("\nError: Invalid command line arguments.")
        print("Example usage: python fetch_price_clean.py -i inventory.csv -r us-east-1")
        print("For help, use: python fetch_price_clean.py --help")
        sys.exit(1)


def get_region_name(region_code):
    """Convert AWS region code to region name used by the Pricing API."""
    region_mapping = {
        'us-east-1': 'US East (N. Virginia)',
        'us-east-2': 'US East (Ohio)',
        'us-west-1': 'US West (N. California)',
        'us-west-2': 'US West (Oregon)',
        'af-south-1': 'Africa (Cape Town)',
        'ap-east-1': 'Asia Pacific (Hong Kong)',
        'ap-south-1': 'Asia Pacific (Mumbai)',
        'ap-northeast-1': 'Asia Pacific (Tokyo)',
        'ap-northeast-2': 'Asia Pacific (Seoul)',
        'ap-northeast-3': 'Asia Pacific (Osaka)',
        'ap-southeast-1': 'Asia Pacific (Singapore)',
        'ap-southeast-2': 'Asia Pacific (Sydney)',
        'ap-southeast-3': 'Asia Pacific (Jakarta)',
        'ca-central-1': 'Canada (Central)',
        'eu-central-1': 'EU (Frankfurt)',
        'eu-west-1': 'EU (Ireland)',
        'eu-west-2': 'EU (London)',
        'eu-west-3': 'EU (Paris)',
        'eu-north-1': 'EU (Stockholm)',
        'eu-south-1': 'EU (Milan)',
        'me-south-1': 'Middle East (Bahrain)',
        'sa-east-1': 'South America (Sao Paulo)'
    }
    
    if region_code not in region_mapping:
        print(f"Warning: '{region_code}' is not a recognized AWS region code.")
        print("Available regions: " + ", ".join(region_mapping.keys()))
    
    return region_mapping.get(region_code, f"Unknown region: {region_code}")


def get_ec2_price(pricing_client, region, instance_type, operating_system, tenancy):
    """Get EC2 instance price from AWS Pricing API."""
    try:
        response = pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
                {"Field": "tenancy", "Value": tenancy, "Type": "TERM_MATCH"},
                {"Field": "operatingSystem", "Value": operating_system, "Type": "TERM_MATCH"},
                {"Field": "preInstalledSw", "Value": 'NA', "Type": "TERM_MATCH"},
                {"Field": "instanceType", "Value": instance_type, "Type": "TERM_MATCH"},
                {"Field": "location", "Value": region, "Type": "TERM_MATCH"},
                {"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"}
            ],
            MaxResults=10
        )

        if 'PriceList' not in response or not response['PriceList']:
            print(f"No prices found for: {instance_type} in {region}")
            print(f"This could be because the instance type is not available in this region,")
            print(f"or the operating system ({operating_system}) or tenancy ({tenancy}) is incorrect.")
            return None
        
        for price_item in response['PriceList']:
            price_data = json.loads(price_item)
            try:
                on_demand = price_data['terms']['OnDemand']
                first_key = list(on_demand.keys())[0]
                price_dimensions = on_demand[first_key]['priceDimensions']
                second_key = list(price_dimensions.keys())[0]
                price = float(price_dimensions[second_key]['pricePerUnit']['USD'])
                return price
            except (KeyError, IndexError) as e:
                print(f"Error parsing price for {instance_type}: {e}")
                
        return None
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"AWS API error for {instance_type}: {error_code} - {error_msg}")
        if error_code == 'AccessDeniedException':
            print("Check your AWS credentials and ensure you have pricing:GetProducts permission.")
        return None
    except Exception as e:
        print(f"Unexpected error for {instance_type}: {str(e)}")
        return None


def read_input_file(file_path):
    """Read input file (CSV or Excel) and return a DataFrame."""
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: Input file '{file_path}' does not exist.")
        print("Please provide a valid file path.")
        sys.exit(1)
        
    file_ext = Path(file_path).suffix.lower()
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            print(f"Error: Unsupported file format: {file_ext}")
            print("Supported formats: .csv, .xlsx, .xls")
            sys.exit(1)
            
        # Validate that the file has the required columns
        if 'inst_type' not in df.columns:
            print(f"Error: Input file '{file_path}' must contain an 'inst_type' column.")
            print("Please check your file format.")
            sys.exit(1)
            
        # Check if the file has any data
        if len(df) == 0:
            print(f"Warning: Input file '{file_path}' is empty.")
            
        return df
    except pd.errors.EmptyDataError:
        print(f"Error: Input file '{file_path}' is empty or has no valid data.")
        sys.exit(1)
    except pd.errors.ParserError:
        print(f"Error: Unable to parse '{file_path}'. The file may be corrupted or in an invalid format.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)


def write_output_file(df, file_path, env_totals=None, grand_total=None):
    """Write DataFrame to output file (CSV or Excel)."""
    # Check if directory exists
    output_dir = os.path.dirname(file_path)
    if output_dir and not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        print("Please provide a valid output directory.")
        return False
        
    file_ext = Path(file_path).suffix.lower()
    try:
        # Create a copy of the dataframe to avoid modifying the original
        output_df = df.copy()
        
        # Add environment totals and grand total if available
        if env_totals is not None or grand_total is not None:
            # Add a few empty rows as separator
            empty_rows = 2
            for _ in range(empty_rows):
                empty_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                output_df = pd.concat([output_df, empty_row], ignore_index=True)
            
            # Add environment totals if available
            if env_totals is not None and not env_totals.empty:
                # Add header row for environment totals
                header_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                header_row.iloc[0, 0] = "=== Environment Totals ==="
                output_df = pd.concat([output_df, header_row], ignore_index=True)
                
                # Add each environment total
                for _, row in env_totals.iterrows():
                    env_name = row['environment'] if pd.notna(row['environment']) else 'Unspecified'
                    env_total = row['total_monthly']
                    
                    env_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                    env_row.iloc[0, 0] = env_name  # First column for environment name
                    
                    # Find the total_monthly column index
                    if 'total_monthly' in output_df.columns:
                        total_col_idx = output_df.columns.get_loc('total_monthly')
                        env_row.iloc[0, total_col_idx] = env_total
                    else:
                        # If total_monthly doesn't exist, use the last column
                        env_row.iloc[0, -1] = env_total
                    
                    output_df = pd.concat([output_df, env_row], ignore_index=True)
            
            # Add grand total if available
            if grand_total is not None:
                # Add empty row as separator
                empty_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                output_df = pd.concat([output_df, empty_row], ignore_index=True)
                
                # Add grand total row
                total_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                total_row.iloc[0, 0] = "GRAND TOTAL"
                
                # Find the total_monthly column index
                if 'total_monthly' in output_df.columns:
                    total_col_idx = output_df.columns.get_loc('total_monthly')
                    total_row.iloc[0, total_col_idx] = grand_total
                else:
                    # If total_monthly doesn't exist, use the last column
                    total_row.iloc[0, -1] = grand_total
                
                output_df = pd.concat([output_df, total_row], ignore_index=True)
        
        # Write to file
        if file_ext == '.csv':
            output_df.to_csv(file_path, index=False)
        elif file_ext in ['.xlsx', '.xls']:
            output_df.to_excel(file_path, index=False)
        else:
            print(f"Error: Unsupported output format: {file_ext}")
            print("Supported formats: .csv, .xlsx, .xls")
            return False
        return True
    except PermissionError:
        print(f"Error: Permission denied when writing to '{file_path}'.")
        print("Please check file permissions or choose a different location.")
        return False
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False


def main():
    """Main function to fetch EC2 pricing."""
    try:
        args = parse_arguments()
        
        # Initialize AWS session
        try:
            session = boto3.Session(profile_name=args.profile)
            pricing_client = session.client('pricing', region_name='us-east-1')  # Pricing API only available in us-east-1
        except botocore.exceptions.ProfileNotFound:
            print(f"Error: AWS profile '{args.profile}' not found.")
            print("Check your AWS credentials file (~/.aws/credentials) or specify a different profile with -p/--profile.")
            sys.exit(1)
        except botocore.exceptions.NoCredentialsError:
            print("Error: AWS credentials not found.")
            print("Please configure your AWS credentials using 'aws configure' or specify a profile with -p/--profile.")
            sys.exit(1)
        except Exception as e:
            print(f"Error initializing AWS session: {e}")
            sys.exit(1)
        
        # Get region name for pricing API
        region_name = get_region_name(args.region)
        if region_name.startswith("Unknown region"):
            print("Continuing with unknown region, but pricing information may not be available.")
        
        # Read input file
        df = read_input_file(args.input)
        
        # Add price columns to DataFrame
        df['hourly_price'] = None
        df['monthly_price'] = None
        if 'count' in df.columns:
            df['total_monthly'] = None
        
        # Fetch prices for each instance type
        print(f"Fetching prices for {len(df)} instance types in {region_name}...")
        
        # Track if any prices were found
        prices_found = False
        error_rows = []
        
        for index, row in df.iterrows():
            try:
                # Validate instance type
                instance_type = row['inst_type']
                if not isinstance(instance_type, str) or not instance_type.strip():
                    df.at[index, 'hourly_price'] = 'Invalid instance type'
                    df.at[index, 'monthly_price'] = 'Invalid instance type'
                    if 'count' in df.columns:
                        df.at[index, 'total_monthly'] = 'Invalid instance type'
                    error_rows.append(f"Row {index+1}: Invalid or empty instance type")
                    continue
                
                # Validate count if present
                if 'count' in df.columns:
                    try:
                        count = int(row['count'])
                        if count <= 0:
                            df.at[index, 'total_monthly'] = 'Invalid count'
                            error_rows.append(f"Row {index+1}: Count must be a positive integer, found: {row['count']}")
                    except (ValueError, TypeError):
                        df.at[index, 'total_monthly'] = 'Invalid count'
                        error_rows.append(f"Row {index+1}: Count must be a number, found: {row['count']}")
                        count = 0  # Set to 0 to skip total calculation
                
                # Get price
                price = get_ec2_price(pricing_client, region_name, instance_type, 
                                    args.operating_system, args.tenancy)
                
                if price is not None:
                    prices_found = True
                    df.at[index, 'hourly_price'] = price
                    monthly = price * 24 * 30  # Approximate monthly cost
                    df.at[index, 'monthly_price'] = monthly
                    
                    # Calculate total if count column exists and count is valid
                    if 'count' in df.columns and isinstance(row['count'], (int, float)) and row['count'] > 0:
                        count = row['count']
                        df.at[index, 'total_monthly'] = monthly * count
                        
                        # Include environment in output if available
                        if 'environment' in df.columns and pd.notna(row['environment']):
                            env = row['environment']
                            print(f"{instance_type}: ${price:.4f}/hr (${monthly:.2f}/mo) × {count} = ${monthly * count:.2f} [{env}]")
                        else:
                            print(f"{instance_type}: ${price:.4f}/hr (${monthly:.2f}/mo) × {count} = ${monthly * count:.2f}")
                    else:
                        print(f"{instance_type}: ${price:.4f}/hr (${monthly:.2f}/mo)")
                else:
                    df.at[index, 'hourly_price'] = 'Not found'
                    df.at[index, 'monthly_price'] = 'Not found'
                    if 'count' in df.columns:
                        df.at[index, 'total_monthly'] = 'Not found'
            except Exception as e:
                # Handle any unexpected errors for this row
                df.at[index, 'hourly_price'] = 'Error'
                df.at[index, 'monthly_price'] = 'Error'
                if 'count' in df.columns:
                    df.at[index, 'total_monthly'] = 'Error'
                error_rows.append(f"Row {index+1}: Unexpected error: {str(e)}")
        
        # Display any row errors
        if error_rows:
            print("\nThe following rows had errors:")
            for error in error_rows:
                print(f"  - {error}")
        
        if not prices_found and not error_rows:
            print("\nWarning: No pricing information was found for any instance type.")
            print("Please check your region, instance types, operating system, and tenancy settings.")
        
        # Initialize variables for totals
        env_totals_df = None
        grand_total = None
        
        # Add grand total if count column exists
        if 'count' in df.columns and 'total_monthly' in df.columns:
            # Filter out non-numeric values
            numeric_df = df.copy()
            numeric_df['total_monthly'] = pd.to_numeric(df['total_monthly'], errors='coerce')
            
            # Calculate overall grand total
            grand_total = numeric_df['total_monthly'].sum()
            
            # Calculate totals by environment if environment column exists
            if 'environment' in df.columns:
                print("\n=== Totals by Environment ===")
                env_totals_df = numeric_df.groupby('environment')['total_monthly'].sum().reset_index()
                for _, row in env_totals_df.iterrows():
                    if not pd.isna(row['total_monthly']) and row['total_monthly'] > 0:
                        env_name = row['environment'] if pd.notna(row['environment']) else 'Unspecified'
                        env_total = row['total_monthly']
                        print(f"{env_name}: ${env_total:.2f}/month")
            
            # Print overall grand total
            if not pd.isna(grand_total) and grand_total > 0:
                print(f"\nGrand Total: ${grand_total:.2f}/month")
                print("(Note: Rows with errors are excluded from the totals)")
        
        # Write output file if specified
        if args.output:
            success = write_output_file(df, args.output, env_totals_df, grand_total)
            if success:
                print(f"Results written to {args.output}")
        else:
            # Print summary
            print("\nSummary of EC2 Instance Pricing:")
            if 'count' in df.columns and 'environment' in df.columns:
                print(df[['inst_type', 'environment', 'hourly_price', 'monthly_price', 'count', 'total_monthly']])
            elif 'count' in df.columns:
                print(df[['inst_type', 'hourly_price', 'monthly_price', 'count', 'total_monthly']])
            elif 'environment' in df.columns:
                print(df[['inst_type', 'environment', 'hourly_price', 'monthly_price']])
            else:
                print(df[['inst_type', 'hourly_price', 'monthly_price']])
        
        print("Done!")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
