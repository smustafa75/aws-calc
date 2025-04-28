# AWS EC2 Price Fetcher

A tool that fetches EC2 instance pricing from AWS Pricing API based on instance types in a CSV/Excel file.

## Scripts
- `fetch_price_clean.py`: Original script with detailed comments
- `fetch_price_clean_optimized.py`: 25% shorter code with identical functionality

## Features
- Fetches current EC2 pricing from AWS API
- Calculates hourly and monthly costs
- Supports instance count for total cost calculation
- Groups and calculates costs by environment
- Outputs to console or file (CSV/Excel)
- Configurable region, OS, and tenancy

## Requirements
- Python 3.6+
- Packages: boto3, pandas
- AWS credentials with pricing API access

## Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install boto3 pandas
```

## Usage
```bash
# Basic usage
python fetch_price_clean.py -i inventory.csv

# Advanced usage
python fetch_price_clean_optimized.py -i inventory_with_env.csv -o results.csv -r us-east-1 -p my_profile -os Linux -t Shared
```

## Arguments
- `-i, --input`: Input file path [required]
- `-o, --output`: Output file path [optional]
- `-r, --region`: AWS region (default: me-south-1)
- `-p, --profile`: AWS profile (default: lab)
- `-os, --operating-system`: OS (default: Linux)
- `-t, --tenancy`: Tenancy type (default: Shared)

## Input Formats
### Basic (Required)
```
inst_type,disk,disk_type
t3.xlarge,500,gp3
```

### With Count
```
inst_type,disk,disk_type,count
t3.xlarge,500,gp3,2
```

### With Environment
```
inst_type,disk,disk_type,environment,count
t3.xlarge,500,gp3,prod,2
```

## Sample Files
- `inventory.csv`: Basic instance types
- `inventory_with_count.csv`: Instances with count
- `inventory_with_env.csv`: Instances with environment
- `inventory_with_errors.csv`: Invalid data examples
- `results.csv`: Example output

## Output Example
```
Fetching prices for 5 instance types in Middle East (Bahrain)...
t3.xlarge: $0.2006/hr ($144.43/mo) × 2 = $288.86 [prod]
m5.xlarge: $0.2350/hr ($169.20/mo) × 3 = $507.60 [dev]

=== Totals by Environment ===
dev: $846.72/month
prod: $669.02/month

Grand Total: $1660.18/month
```

## Troubleshooting
1. **AWS credentials**: Run `aws configure`
2. **Permission denied**: Check pricing:GetProducts permission
3. **No prices found**: Verify instance type availability in region
4. **Invalid region**: Check region code
5. **File not found**: Verify input file path
6. **Invalid data**: Check for empty cells or invalid values

## Future Enhancements
- Reserved Instance & Spot pricing
- Savings Plans calculations
- Multi-region comparison
- Storage pricing
- Web interface
