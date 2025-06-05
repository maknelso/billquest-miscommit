# Components

This directory contains reusable React components used throughout the application.

## Components

### Header

`Header.tsx` - The application header component that appears on all pages after login.

Features:
- Displays the application name
- Shows the currently logged-in user's email
- Provides a sign-out button
- Styled with `Header.css`

Usage:
```tsx
import Header from './components/Header';

function MyPage() {
  return (
    <div>
      <Header />
      {/* Page content */}
    </div>
  );
}
```

## Adding New Components

When adding new components:

1. Create a new file with a `.tsx` extension
2. Export the component as the default export
3. Create a separate CSS file if needed
4. Document the component's props and usage