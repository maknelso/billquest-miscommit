# BillQuest Frontend Deployment Guide

## Production Website

CloudFront website link: https://d2qvugcag2us70.cloudfront.net/

Demo credentials:
- Username: nelmak@xxx.com
- Password: Test123!

- payer_account_id: xxx4118
- invoice_id: EUINFR25-xxx134

## Local Development

To run the application locally:

```bash
npm install
npm run dev
```

This will start the development server at http://localhost:5173

## Production Deployment

### Option 1: Using AWS CDK (Recommended)

The project is configured to deploy automatically using AWS CDK. The CDK stack will:
1. Create an S3 bucket for hosting
2. Set up CloudFront for content delivery
3. Configure Cognito for authentication

To deploy using CDK:

```bash
# From the project root
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
cdk deploy
```

### Option 2: Manual S3 Deployment

If you encounter issues with CDK deployment, you can manually deploy to S3:

```bash
# From the project root
chmod +x frontend/deploy-to-s3.sh
./frontend/deploy-to-s3.sh
```

This script will:
1. Build the Vite application
2. Upload the build files to the S3 bucket
3. (Optional) Create a CloudFront invalidation

## Accessing Your Deployed Application

After deployment:
- If using CDK: The CloudFront URL will be shown in the CDK outputs
- If using manual S3 deployment: Access via the S3 website endpoint or CloudFront URL

## Updating API Endpoints

If deploying to a different environment, update the API endpoints in:
- `src/services/api.ts`
- `src/aws/amplifyConfig.ts`