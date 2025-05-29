import {
  signUp as amplifySignUp, // Using an alias to avoid potential naming conflicts
  signIn as amplifySignIn,
  getCurrentUser as amplifyGetCurrentUser,
  SignUpInput, // Type for signUp input
  // If you need signOut or other auth functions, import them here too
  // e.g., signOut as amplifySignOut
} from 'aws-amplify/auth';

export async function signUp(username: string, password: string, email: string) {
  try {
    // The signUp function in v6 expects an object with username, password, and options.
    // The attributes are nested under 'options.userAttributes'.
    const signUpInput: SignUpInput = {
      username,
      password,
      options: {
        userAttributes: {
          email,
        },
        // You can add other options like autoSignIn if needed
        // autoSignIn: true
      },
    };
    const { isSignUpComplete, userId, nextStep } = await amplifySignUp(signUpInput);
    console.log('Sign up successful:', { isSignUpComplete, userId, nextStep });
    return { isSignUpComplete, userId, nextStep };
  } catch (error) {
    console.error('Error signing up:', error);
    throw error;
  }
}

export async function signIn(username: string, password: string) {
  try {
    // The signIn function in v6 expects an object with username and password.
    const { isSignedIn, nextStep } = await amplifySignIn({ username, password });
    console.log('Sign in successful:', { isSignedIn, nextStep });
    // The signIn function in v6 returns an object indicating sign-in status and next steps.
    // It doesn't directly return the "user object" in the same way as v5.
    // To get user details after sign-in, you would typically call getCurrentUser.
    if (isSignedIn) {
      return await amplifyGetCurrentUser(); // Or handle based on nextStep
    }
    return { isSignedIn, nextStep }; // Return the result for further handling
  } catch (error) {
    console.error('Error signing in:', error);
    throw error;
  }
}

export async function getCurrentUser() {
  try {
    // currentAuthenticatedUser() is now getCurrentUser()
    const currentUser = await amplifyGetCurrentUser();
    // The returned object contains attributes like userId, username, signInDetails etc.
    console.log('Current user:', currentUser);
    return currentUser;
  } catch (error) {
    // This error typically means no user is signed in.
    console.warn('Not signed in:', error); // Use console.warn or info for expected states
    return null;
  }
}

// If you need a signOut function:
// import { signOut as amplifySignOut } from 'aws-amplify/auth';
//
// export async function signOut() {
//   try {
//     await amplifySignOut();
//     console.log('Sign out successful');
//   } catch (error) {
//     console.error('Error signing out:', error);
//     throw error;
//   }
// }

// Don't forget to configure Amplify in your app's entry point (e.g., main.tsx or index.tsx)
// import { Amplify } from 'aws-amplify';
// import outputs from '../amplify_outputs.json'; // Or aws-exports.js if you're using an older config
// Amplify.configure(outputs); // or Amplify.configure(awsExports);