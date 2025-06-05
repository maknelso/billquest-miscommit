# Frontend Source Code

This directory contains the source code for the BillQuest frontend application.

## Directory Structure

- `assets/`: Static assets like SVG files
- `aws/`: AWS configuration and authentication utilities
- `components/`: Reusable React components
- `pages/`: Page components for different routes
- `App.tsx`: Main application component
- `main.tsx`: Application entry point

## Key Files

- `aws/auth.ts`: Authentication utilities for AWS Cognito
- `aws/amplifyConfig.ts`: Configuration for AWS Amplify
- `components/Header.tsx`: Header component used across pages
- `pages/Login.tsx`: Login page component
- `pages/Signup.tsx`: Signup page component
- `pages/ConfirmSignup.tsx`: Signup confirmation page component

## State Management

The application uses React's built-in state management with hooks. User authentication state is managed through AWS Amplify's authentication API.

## API Integration

The frontend communicates with backend services through API Gateway endpoints. The main endpoints are:

- Query endpoint: For retrieving billing data
- User accounts endpoint: For retrieving user account information