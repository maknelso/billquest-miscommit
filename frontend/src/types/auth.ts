// Authentication Types

export interface SignUpParams {
  username: string;
  password: string;
  email: string;
}

export interface SignInParams {
  username: string;
  password: string;
}

export interface ConfirmSignUpParams {
  username: string;
  confirmationCode: string;
}

export interface UserAttributes {
  email?: string;
  email_verified?: boolean;
  name?: string;
  [key: string]: any;
}

export interface AuthUser {
  username: string;
  userId: string;
  signInDetails?: {
    loginId?: string;
  };
  [key: string]: any;
}

export interface AuthError {
  name: string;
  message: string;
  code?: string;
}