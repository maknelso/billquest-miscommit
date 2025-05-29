import { Amplify } from 'aws-amplify';

//*TEST
console.log('Amplify.configure called'); // Add this
console.log('window object:', typeof window); // Add this

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: 'us-east-1_0TZqMTtTP',
      userPoolClientId: '3ak8em99qdsivhg2qka1b3p62f',
      loginWith: {
        oauth: {
          domain: 'us-east-1_0TZqMTtTP.auth.us-east-1.amazoncognito.com',
          scopes: ['email', 'openid', 'profile'],
          redirectSignIn: ['http://localhost:5173/callback'],
          redirectSignOut: ['http://localhost:5173/'],
          responseType: 'code'
        }
      }
    }
  }
});
