# CDK Infrastructure

This directory contains the AWS Cloud Development Kit (CDK) code that defines the infrastructure for the BillQuest application.

## Files

### app.py

The entry point for the CDK application. This file creates an instance of the CDK app and adds the BillQuestMiscommitStack to it.

### bill_quest_miscommit_stack.py

Defines the main infrastructure stack for the application, including:

- DynamoDB tables for storing billing data and user information
- S3 buckets for file uploads and website hosting
- Lambda functions for data processing and API endpoints
- API Gateway for exposing Lambda functions as REST APIs
- CloudFront distribution for serving the frontend
- Cognito User Pool for authentication

## Deployment

To deploy the infrastructure:

```bash
# From the project root
cd backend
cdk deploy
```

To view the generated CloudFormation template without deploying:

```bash
cdk synth
```

## Configuration

The stack uses configuration values from `backend/config/config.py` to allow for environment-specific settings.

## Outputs

After deployment, the CDK stack outputs several important values:

- API Gateway endpoints
- CloudFront distribution domain
- Cognito User Pool ID and Client ID
- S3 bucket names