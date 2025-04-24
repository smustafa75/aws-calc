# AWS EC2 Price Fetcher

This tool fetches accurate EC2 instance pricing from AWS Pricing API based on instance types specified in an input file (CSV or Excel).

## Features

- Reads instance types from CSV or Excel files
- Fetches current pricing from AWS Pricing API
- Calculates both hourly and monthly estimated costs
- Supports instance count for total cost calculation
- Outputs results to screen or file (CSV/Excel)
- Configurable region, operating system, and tenancy
- Robust error handling and user-friendly messages

## Requirements

- Python 3.6+
- Required packages: boto3, pandas
- AWS credentials configured with pricing API access

## Installation

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install boto3 pandas
```

Alternatively, you can install the packages system-wide (on macOS):

```bash
# Using pip with user flag
python3 -m pip install boto3 pandas --break-system-packages --user

# Or using Homebrew Python
/opt/homebrew/bin/python3 -m pip install boto3 pandas --break-system-packages --user
```

## Usage

Basic usage:

```bash
python fetch_price_clean.py -i inventory.csv
```

Advanced usage:

```bash
python fetch_price_clean.py -i template.csv -o pricing_results.csv -r us-east-1 -p my_aws_profile -os Windows -t Dedicated
```

## Command Line Arguments

- `-i, --input`: Input file path (CSV or Excel) [required]
- `-o, --output`: Output file path (CSV or Excel) [optional]
- `-r, --region`: AWS region code (default: me-south-1)
- `-p, --profile`: AWS profile name (default: lab)
- `-os, --operating-system`: Operating system (default: Linux)
- `-t, --tenancy`: Tenancy type (default: Shared)

## Input File Format

The input file must contain a column named `inst_type` with EC2 instance types.
If you include a `count` column, the script will calculate total costs.

Example CSV without count:
```
inst_type,disk,disk_type
t3.xlarge,500,gp3
m5.xlarge,200,gp3
```

Example CSV with count:
```
inst_type,disk,disk_type,environment,count
t3.xlarge,500,gp3,prod,2
m5.xlarge,200,gp3,dev,3
```

## Output

The script will add these columns to the data:
- `hourly_price`: The hourly cost of the instance
- `monthly_price`: Estimated monthly cost (hourly price × 24 × 30)
- `total_monthly`: Total monthly cost for all instances (if count is provided)

## Example Results

```
Fetching prices for 8 instance types in Middle East (Bahrain)...
t3.xlarge: $0.2006 per hour ($144.43 per month) × 2 = $288.86
m5.xlarge: $0.2350 per hour ($169.20 per month) × 3 = $507.60
...
Grand Total: $3452.04 per month
```

## Error Handling

The script includes comprehensive error handling for common issues:

- **Invalid command line arguments**: Shows usage examples and help information
- **Missing input file**: Checks if the file exists and provides clear error messages
- **Invalid file format**: Validates file format and required columns
- **AWS credential issues**: Detects missing or invalid AWS profiles
- **Invalid region codes**: Warns about unrecognized regions and lists available options
- **API errors**: Provides detailed error messages with troubleshooting suggestions
- **Output file errors**: Handles permission issues and invalid output formats

## Enhanced Version

An enhanced version of this script (`fetch_price_enhanced.py`) is also available, which provides:

- On-demand pricing
- 1-year reserved instances (no upfront) pricing
- 3-year reserved instances (no upfront) pricing
- Savings calculations compared to on-demand pricing
- Grand totals for each pricing model

Usage is the same as the standard version:

```bash
python fetch_price_enhanced.py -i inventory_with_count.csv
```

## Troubleshooting

If you encounter issues:

1. **AWS credentials not found**: Run `aws configure` to set up your credentials
2. **Permission denied**: Ensure you have pricing:GetProducts permission
3. **No prices found**: Verify the instance type is available in the specified region
4. **Invalid region**: Check the region code against the list of available regions
5. **File not found**: Verify the input file path is correct
