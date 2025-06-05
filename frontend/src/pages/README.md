# Pages

This directory contains React components that represent full pages in the application.

## Available Pages

### Login

`Login.tsx` - The login page for existing users.

Features:
- Email and password input fields
- Form validation
- Error handling for authentication failures
- Link to signup page
- Styled with `Login.css`

### Signup

`Signup.tsx` - The signup page for new users.

Features:
- Username, email, and password input fields
- Password strength requirements
- Form validation
- Error handling
- Redirects to confirmation page on successful signup

### ConfirmSignup

`ConfirmSignup.tsx` - The confirmation page for completing the signup process.

Features:
- Verification code input
- Error handling
- Redirects to login page on successful confirmation

## Routing

These pages are integrated with React Router in the main application. The routing configuration can be found in `main.tsx`.