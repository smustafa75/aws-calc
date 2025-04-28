# AWS EC2 Price Fetcher

This tool fetches accurate EC2 instance pricing from AWS Pricing API based on instance types specified in an input file (CSV or Excel).

## Project Structure

```
calculator/
└── aws-calc/
    ├── fetch_price_clean.py         # Original script for EC2 pricing
    ├── fetch_price_clean_optimized.py # Optimized version of the script
    ├── inventory.csv                # Basic instance types
    ├── inventory_with_count.csv     # Instances with count
    ├── inventory_with_env.csv       # Instances with environment and count
    ├── inventory_with_errors.csv    # Sample with invalid data
    ├── results.csv                  # Sample output
    ├── results_with_env_totals.csv  # Output with environment totals
    └── README.md                    # This documentation
```

## Features

- Reads instance types from CSV or Excel files
- Fetches current pricing from AWS Pricing API
- Calculates both hourly and monthly estimated costs
- Supports instance count for total cost calculation
- Groups and calculates costs by environment
- Handles invalid data gracefully without crashing
- Outputs results to screen or file (CSV/Excel)
- Configurable region, operating system, and tenancy
- Robust error handling and user-friendly messages

## Script Versions

### Original Script (`fetch_price_clean.py`)
The original implementation with comprehensive functionality and detailed comments.

### Optimized Script (`fetch_price_clean_optimized.py`)
An optimized version that:
- Reduces code length by approximately 25%
- Improves performance with more efficient data structures
- Maintains all original functionality
- Uses more concise Python idioms
- Features improved organization with dedicated helper functions

Both scripts provide identical results and accept the same command-line arguments.

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
# OR using the optimized version
python fetch_price_clean_optimized.py -i inventory.csv
```

Advanced usage:

```bash
python fetch_price_clean_optimized.py -i inventory_with_env.csv -o pricing_results.csv -r us-east-1 -p my_aws_profile -os Windows -t Dedicated
```

## Command Line Arguments

- `-i, --input`: Input file path (CSV or Excel) [required]
- `-o, --output`: Output file path (CSV or Excel) [optional]
- `-r, --region`: AWS region code (default: me-south-1)
- `-p, --profile`: AWS profile name (default: lab)
- `-os, --operating-system`: Operating system (default: Linux)
- `-t, --tenancy`: Tenancy type (default: Shared)

## Input File Format

The script supports several input file formats:

### Basic Format (Required)
The input file must contain a column named `inst_type` with EC2 instance types:
```
inst_type,disk,disk_type
t3.xlarge,500,gp3
m5.xlarge,200,gp3
```

### With Instance Count
Add a `count` column to calculate total costs:
```
inst_type,disk,disk_type,count
t3.xlarge,500,gp3,2
m5.xlarge,200,gp3,3
```

### With Environment Grouping
Add an `environment` column to group costs by environment:
```
inst_type,disk,disk_type,environment,count
t3.xlarge,500,gp3,prod,2
m5.xlarge,200,gp3,dev,3
c6i.large,400,gp3,prod,5
```

## Sample Files

The repository includes several sample files:

- `inventory.csv`: Basic instance types
- `inventory_with_count.csv`: Instances with count
- `inventory_with_env.csv`: Instances with environment and count
- `inventory_with_errors.csv`: Sample with invalid data to test error handling
- `results.csv`: Example output from basic run
- `results_with_env_totals.csv`: Example output with environment totals

## Output

### Console Output
The script displays detailed pricing information in the console:
- Individual instance pricing
- Environment-based subtotals (if environment column exists)
- Grand total across all instances
- Error messages for any problematic rows

### CSV/Excel Output
When saving to a file, the output includes:
- All instance data with pricing information
- Environment totals section (if environment column exists)
- Grand total row
- Format designed for easy import into spreadsheet applications

Example output columns:
- `hourly_price`: The hourly cost of the instance
- `monthly_price`: Estimated monthly cost (hourly price × 24 × 30)
- `total_monthly`: Total monthly cost for all instances (if count is provided)

## Example Results

```
Fetching prices for 5 instance types in Middle East (Bahrain)...
t3.xlarge: $0.2006/hr ($144.43/mo) × 2 = $288.86 [prod]
m5.xlarge: $0.2350/hr ($169.20/mo) × 3 = $507.60 [dev]
c6i.large: $0.1056/hr ($76.03/mo) × 5 = $380.16 [prod]
t3.large: $0.1003/hr ($72.22/mo) × 2 = $144.43 [test]
m5.2xlarge: $0.4710/hr ($339.12/mo) × 1 = $339.12 [dev]

=== Totals by Environment ===
dev: $846.72/month
prod: $669.02/month
test: $144.43/month

Grand Total: $1660.18/month
```

## Error Handling

The script includes comprehensive error handling for common issues:

- **Invalid command line arguments**: Shows usage examples and help information
- **Missing input file**: Checks if the file exists and provides clear error messages
- **Invalid file format**: Validates file format and required columns
- **Invalid data in rows**: Identifies and reports specific errors for each problematic row
- **AWS credential issues**: Detects missing or invalid AWS profiles
- **Invalid region codes**: Warns about unrecognized regions and lists available options
- **API errors**: Provides detailed error messages with troubleshooting suggestions
- **Output file errors**: Handles permission issues and invalid output formats

## Troubleshooting

If you encounter issues:

1. **AWS credentials not found**: Run `aws configure` to set up your credentials
2. **Permission denied**: Ensure you have pricing:GetProducts permission
3. **No prices found**: Verify the instance type is available in the specified region
4. **Invalid region**: Check the region code against the list of available regions
5. **File not found**: Verify the input file path is correct
6. **Invalid data**: Check for empty cells, non-numeric counts, or invalid instance types

## Future Enhancements

Potential future enhancements for this tool:

1. **Reserved Instance Pricing**: Add support for different RI terms and payment options
2. **Spot Instance Pricing**: Include spot instance pricing information
3. **Savings Plans**: Calculate potential savings with AWS Savings Plans
4. **Multi-Region Comparison**: Compare pricing across multiple AWS regions
5. **Storage Pricing**: Add EBS volume pricing calculations
6. **Web Interface**: Create a simple web interface for the tool
7. **Historical Data**: Track pricing changes over time
