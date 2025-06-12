#!/bin/bash

# Build the Vite app
cd frontend && npm run build

# Set your S3 bucket name - using the same name from your CDK stack
S3_BUCKET="billquestmiscommitstack-websitebucket-nelmak"

# Upload to S3
aws s3 sync dist/ s3://$S3_BUCKET/ --delete

# Create CloudFront invalidation
CLOUDFRONT_DISTRIBUTION_ID="E1JKSAR8RH0400"
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"

echo "Deployment complete!"
echo "Your website is available at: https://d2qvugcag2us70.cloudfront.net"