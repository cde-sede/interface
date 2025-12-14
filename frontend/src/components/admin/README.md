# Admin Panel Component Structure

This directory contains the refactored admin panel components, organized for better maintainability.

## Directory Structure

```
admin/
├── components/          # Shared UI components
│   ├── ToastNotification.tsx
│   ├── ConfirmDialog.tsx
│   ├── LoginForm.tsx
│   └── index.ts
├── pages/              # Page-specific components
│   ├── LogsPage.tsx
│   ├── OverviewPage.tsx (to be created)
│   ├── ServicesPage.tsx (to be created)
│   ├── TasksPage.tsx (to be created)
│   ├── MetricsPage.tsx (to be created)
│   ├── SettingsPage.tsx (to be created)
│   ├── DatabasePage.tsx (to be created)
│   └── index.ts
└── README.md
```

## Components

### Shared Components (`/components`)

#### ToastNotification
Displays temporary notification messages.

**Props:**
- `toasts: Toast[]` - Array of toast notifications
- `onClose: (id: number) => void` - Callback when closing a toast

#### ConfirmDialog
Modal dialog for confirming actions.

**Props:**
- `message: string` - Confirmation message
- `onConfirm: () => void` - Callback when confirmed
- `onCancel: () => void` - Callback when cancelled

#### LoginForm
Admin login form component.

**Props:**
- `authError: string` - Authentication error message
- `loginError: string | null` - Login-specific error
- `isLoggingIn: boolean` - Loading state
- `onLogin: (username: string, password: string) => void` - Login handler

### Page Components (`/pages`)

#### LogsPage
Displays formatted application logs with color-coded log levels.

**Props:**
- `logs?: Log[]` - Array of log entries
- `title?: string` - Page title
- `description?: string` - Page description

## Pattern for Creating New Page Components

Each page component should:
1. Accept page data as props (instead of reading from parent state)
2. Handle its own rendering logic
3. Export a TypeScript interface for its props
4. Be a default export

### Example:

```tsx
interface MyPageProps {
    data: any;
    title?: string;
    description?: string;
    onAction?: () => void;
}

export default function MyPage({ data, title, description, onAction }: MyPageProps) {
    return (
        <div className="page-content">
            <h2>{title}</h2>
            {description && <p className="page-description">{description}</p>}
            {/* Page-specific content */}
        </div>
    );
}
```

## Refactoring Status

- ✅ ToastNotification
- ✅ ConfirmDialog
- ✅ LoginForm
- ✅ LogsPage
- ⏳ OverviewPage (in Admin.tsx, ready to extract)
- ⏳ ServicesPage (in Admin.tsx, ready to extract)
- ⏳ TasksPage (in Admin.tsx, ready to extract)
- ⏳ MetricsPage (in Admin.tsx, ready to extract)
- ⏳ SettingsPage (in Admin.tsx, ready to extract)
- ⏳ DatabasePage (in Admin.tsx, ready to extract)

## Usage in Admin.tsx

```tsx
import { ToastNotification, ConfirmDialog, LoginForm } from './admin/components';
import { LogsPage } from './admin/pages';

// In render:
<ToastNotification
    toasts={toasts}
    onClose={(id) => setToasts(prev => prev.filter(t => t.id !== id))}
/>

{confirmDialog && (
    <ConfirmDialog {...confirmDialog} />
)}

{authError && (
    <LoginForm
        authError={authError}
        loginError={loginError}
        isLoggingIn={isLoggingIn}
        onLogin={handleLogin}
    />
)}

// In switch statement:
case 'logs':
    return <LogsPage logs={pageData?.logs} title={pageData?.title} description={pageData?.description} />;
```
