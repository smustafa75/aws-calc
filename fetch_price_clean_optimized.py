#!/usr/bin/env python3
"""
AWS EC2 Price Fetcher - Optimized Version

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
    parser.add_argument('-os', '--operating-system', default='Linux', help='Operating system (default: Linux)')
    parser.add_argument('-t', '--tenancy', default='Shared', help='Tenancy type (default: Shared)')
    
    try:
        return parser.parse_args()
    except SystemExit:
        print("\nError: Invalid command line arguments.")
        print("Example usage: python fetch_price_clean.py -i inventory.csv -r us-east-1")
        print("For help, use: python fetch_price_clean.py --help")
        sys.exit(1)


# Region mapping dictionary - moved outside function to avoid recreation on each call
REGION_MAPPING = {
    'us-east-1': 'US East (N. Virginia)', 'us-east-2': 'US East (Ohio)',
    'us-west-1': 'US West (N. California)', 'us-west-2': 'US West (Oregon)',
    'af-south-1': 'Africa (Cape Town)', 'ap-east-1': 'Asia Pacific (Hong Kong)',
    'ap-south-1': 'Asia Pacific (Mumbai)', 'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'ap-northeast-2': 'Asia Pacific (Seoul)', 'ap-northeast-3': 'Asia Pacific (Osaka)',
    'ap-southeast-1': 'Asia Pacific (Singapore)', 'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-southeast-3': 'Asia Pacific (Jakarta)', 'ca-central-1': 'Canada (Central)',
    'eu-central-1': 'EU (Frankfurt)', 'eu-west-1': 'EU (Ireland)',
    'eu-west-2': 'EU (London)', 'eu-west-3': 'EU (Paris)',
    'eu-north-1': 'EU (Stockholm)', 'eu-south-1': 'EU (Milan)',
    'me-south-1': 'Middle East (Bahrain)', 'sa-east-1': 'South America (Sao Paulo)'
}


def get_region_name(region_code):
    """Convert AWS region code to region name used by the Pricing API."""
    if region_code not in REGION_MAPPING:
        print(f"Warning: '{region_code}' is not a recognized AWS region code.")
        print("Available regions: " + ", ".join(REGION_MAPPING.keys()))
    return REGION_MAPPING.get(region_code, f"Unknown region: {region_code}")


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

        if not response.get('PriceList'):
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
                return float(price_dimensions[second_key]['pricePerUnit']['USD'])
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
    if not os.path.exists(file_path):
        print(f"Error: Input file '{file_path}' does not exist.")
        sys.exit(1)
        
    file_ext = Path(file_path).suffix.lower()
    try:
        df = pd.read_csv(file_path) if file_ext == '.csv' else pd.read_excel(file_path) if file_ext in ['.xlsx', '.xls'] else None
        
        if df is None:
            print(f"Error: Unsupported file format: {file_ext}. Supported formats: .csv, .xlsx, .xls")
            sys.exit(1)
            
        if 'inst_type' not in df.columns:
            print(f"Error: Input file must contain an 'inst_type' column.")
            sys.exit(1)
            
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
    output_dir = os.path.dirname(file_path)
    if output_dir and not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return False
        
    file_ext = Path(file_path).suffix.lower()
    try:
        output_df = df.copy()
        
        # Add environment totals and grand total if available
        if env_totals is not None or grand_total is not None:
            # Add empty rows as separator
            empty_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
            output_df = pd.concat([output_df, empty_row, empty_row], ignore_index=True)
            
            # Add environment totals if available
            if env_totals is not None and not env_totals.empty:
                header_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                header_row.iloc[0, 0] = "=== Environment Totals ==="
                output_df = pd.concat([output_df, header_row], ignore_index=True)
                
                for _, row in env_totals.iterrows():
                    env_name = row['environment'] if pd.notna(row['environment']) else 'Unspecified'
                    env_total = row['total_monthly']
                    
                    env_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                    env_row.iloc[0, 0] = env_name
                    
                    total_col_idx = output_df.columns.get_loc('total_monthly') if 'total_monthly' in output_df.columns else -1
                    env_row.iloc[0, total_col_idx] = env_total
                    
                    output_df = pd.concat([output_df, env_row], ignore_index=True)
            
            # Add grand total if available
            if grand_total is not None:
                output_df = pd.concat([output_df, empty_row], ignore_index=True)
                
                total_row = pd.DataFrame({col: [''] for col in output_df.columns}, index=[0])
                total_row.iloc[0, 0] = "GRAND TOTAL"
                
                total_col_idx = output_df.columns.get_loc('total_monthly') if 'total_monthly' in output_df.columns else -1
                total_row.iloc[0, total_col_idx] = grand_total
                
                output_df = pd.concat([output_df, total_row], ignore_index=True)
        
        # Write to file based on extension
        if file_ext == '.csv':
            output_df.to_csv(file_path, index=False)
        elif file_ext in ['.xlsx', '.xls']:
            output_df.to_excel(file_path, index=False)
        else:
            print(f"Error: Unsupported output format: {file_ext}. Supported formats: .csv, .xlsx, .xls")
            return False
        return True
    except PermissionError:
        print(f"Error: Permission denied when writing to '{file_path}'.")
        return False
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False


def process_instance_row(index, row, pricing_client, region_name, operating_system, tenancy):
    """Process a single instance row and return updated values and error message if any."""
    result = {'hourly_price': None, 'monthly_price': None, 'total_monthly': None, 'error': None}
    
    # Validate instance type
    instance_type = row['inst_type']
    if not isinstance(instance_type, str) or not instance_type.strip():
        result['hourly_price'] = result['monthly_price'] = 'Invalid instance type'
        if 'count' in row:
            result['total_monthly'] = 'Invalid instance type'
        result['error'] = f"Row {index+1}: Invalid or empty instance type"
        return result
    
    # Validate count if present
    count = None
    if 'count' in row:
        try:
            count = int(row['count'])
            if count <= 0:
                result['total_monthly'] = 'Invalid count'
                result['error'] = f"Row {index+1}: Count must be a positive integer, found: {row['count']}"
        except (ValueError, TypeError):
            result['total_monthly'] = 'Invalid count'
            result['error'] = f"Row {index+1}: Count must be a number, found: {row['count']}"
            count = 0
    
    # Get price
    price = get_ec2_price(pricing_client, region_name, instance_type, operating_system, tenancy)
    
    if price is not None:
        result['hourly_price'] = price
        monthly = price * 24 * 30  # Approximate monthly cost
        result['monthly_price'] = monthly
        
        # Calculate total if count column exists and count is valid
        if count and count > 0:
            result['total_monthly'] = monthly * count
            
            # Format output message
            env = row.get('environment', '') if pd.notna(row.get('environment', '')) else ''
            env_str = f" [{env}]" if env else ""
            print(f"{instance_type}: ${price:.4f}/hr (${monthly:.2f}/mo) × {count} = ${monthly * count:.2f}{env_str}")
        else:
            print(f"{instance_type}: ${price:.4f}/hr (${monthly:.2f}/mo)")
    else:
        result['hourly_price'] = result['monthly_price'] = 'Not found'
        if 'count' in row:
            result['total_monthly'] = 'Not found'
    
    return result


def main():
    """Main function to fetch EC2 pricing."""
    try:
        args = parse_arguments()
        
        # Initialize AWS session
        try:
            session = boto3.Session(profile_name=args.profile)
            pricing_client = session.client('pricing', region_name='us-east-1')  # Pricing API only in us-east-1
        except botocore.exceptions.ProfileNotFound:
            print(f"Error: AWS profile '{args.profile}' not found.")
            sys.exit(1)
        except botocore.exceptions.NoCredentialsError:
            print("Error: AWS credentials not found.")
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
        
        prices_found = False
        error_rows = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                result = process_instance_row(index, row, pricing_client, region_name, 
                                             args.operating_system, args.tenancy)
                
                # Update DataFrame with results
                df.at[index, 'hourly_price'] = result['hourly_price']
                df.at[index, 'monthly_price'] = result['monthly_price']
                if 'count' in df.columns and result['total_monthly'] is not None:
                    df.at[index, 'total_monthly'] = result['total_monthly']
                
                # Track errors and if prices were found
                if result['error']:
                    error_rows.append(result['error'])
                elif result['hourly_price'] not in (None, 'Not found', 'Invalid instance type', 'Error'):
                    prices_found = True
            except Exception as e:
                df.at[index, 'hourly_price'] = df.at[index, 'monthly_price'] = 'Error'
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
        
        # Calculate totals
        env_totals_df = None
        grand_total = None
        
        if 'count' in df.columns and 'total_monthly' in df.columns:
            # Convert to numeric, coercing errors to NaN
            numeric_df = df.copy()
            numeric_df['total_monthly'] = pd.to_numeric(df['total_monthly'], errors='coerce')
            
            # Calculate grand total
            grand_total = numeric_df['total_monthly'].sum()
            
            # Calculate environment totals if available
            if 'environment' in df.columns:
                print("\n=== Totals by Environment ===")
                env_totals_df = numeric_df.groupby('environment')['total_monthly'].sum().reset_index()
                for _, row in env_totals_df.iterrows():
                    if not pd.isna(row['total_monthly']) and row['total_monthly'] > 0:
                        env_name = row['environment'] if pd.notna(row['environment']) else 'Unspecified'
                        print(f"{env_name}: ${row['total_monthly']:.2f}/month")
            
            # Print grand total
            if not pd.isna(grand_total) and grand_total > 0:
                print(f"\nGrand Total: ${grand_total:.2f}/month")
                print("(Note: Rows with errors are excluded from the totals)")
        
        # Write output file if specified
        if args.output:
            if write_output_file(df, args.output, env_totals_df, grand_total):
                print(f"Results written to {args.output}")
        else:
            # Print summary
            print("\nSummary of EC2 Instance Pricing:")
            cols = ['inst_type']
            if 'environment' in df.columns:
                cols.append('environment')
            cols.extend(['hourly_price', 'monthly_price'])
            if 'count' in df.columns:
                cols.extend(['count', 'total_monthly'])
            print(df[cols])
        
        print("Done!")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
