# AWS Integration

This directory contains utilities for integrating with AWS services, particularly for authentication.

## Files

### auth.ts

Contains functions for AWS Cognito authentication:

- `signUp`: Register a new user
- `signIn`: Authenticate an existing user
- `getCurrentUser`: Get the currently authenticated user
- `signOut`: Sign out the current user

These functions wrap the AWS Amplify v6 authentication API to provide a simpler interface for the application.

### amplifyConfig.ts

Contains the configuration for AWS Amplify, including:

- Cognito User Pool settings
- API Gateway endpoints
- Region configuration

## Usage

```typescript
import { signIn, getCurrentUser, signOut } from './aws/auth';

// Sign in a user
const user = await signIn(email, password);

// Get the current user
const currentUser = await getCurrentUser();

// Sign out
await signOut();
```

## Error Handling

All authentication functions include proper error handling and will throw descriptive errors that can be caught and displayed to the user.