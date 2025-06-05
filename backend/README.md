# BillQuest Backend

This directory contains the backend code for the BillQuest application.

## Directory Structure

- `cdk/`: Contains AWS CDK infrastructure code
- `config/`: Contains configuration settings for different environments
- `lambda/`: Contains Lambda function code
  - `get_user_accounts/`: Lambda for retrieving user account information
  - `ingest_data/`: Lambda for ingesting data from S3 to DynamoDB
  - `query_data/`: Lambda for querying data from DynamoDB
  - `update_user_info/`: Lambda for updating user information from CSV files
- `tests/`: Contains test code

## Configuration

The application uses a centralized configuration system in the `config/` directory:

- `config.py`: Contains all configuration settings with environment-specific overrides

To switch between environments, set the `ENVIRONMENT` environment variable:

```bash
# For development (default)
export ENVIRONMENT=dev

# For production
export ENVIRONMENT=prod
```

## Deployment

To deploy the application:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deploy the stack
cdk deploy
```

## Linting

To lint the CloudFormation templates:

```bash
cd backend
npm run lint:cfn
```