# OAuth Credentials Explained

This document explains the different OAuth credential files used by `google-gmail-tool` and when you need each one.

## Two Types of Credential Files

### 1. Client Secret File (Downloaded from Google Cloud Console)

**Purpose**: Contains your OAuth 2.0 Client ID configuration that identifies your application to Google.

**File name**: Usually `client_secret_*.json` or similar (you download this from Google Cloud Console)

**What's inside**:
```json
{
  "installed": {
    "client_id": "....apps.googleusercontent.com",
    "project_id": "....",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "....",
    "redirect_uris": ["http://localhost"]
  }
}
```

**Key fields**:
- `client_id` - Identifies your app to Google
- `client_secret` - Secret key for your app (like a password)
- `redirect_uris` - Where Google sends users after authorization

**When you need it**:
- Only for the initial OAuth flow (running `google-gmail-tool auth login`)
- One-time use to authorize your app

**Security**: Keep this file private - the `client_secret` should not be shared publicly

---

### 2. Authorized User Credentials (Created After OAuth Flow)

**Purpose**: Contains your personal access tokens after you complete the OAuth authorization flow.

**File name**: `credentials.json` or `authorized_user.json` (created by `auth login` command)

**What's inside**:
```json
{
  "type": "authorized_user",
  "client_id": "....apps.googleusercontent.com",
  "client_secret": "...",
  "refresh_token": "..."
}
```

**Key fields**:
- `client_id` - Same as client secret file
- `client_secret` - Same as client secret file
- `refresh_token` - **This is the most important part!** Allows the tool to automatically get new access tokens without requiring you to re-authorize

**When you need it**:
- Every time you use the tool
- Set via `GOOGLE_GMAIL_TOOL_CREDENTIALS` environment variable

**Security**: Keep this file very private - the `refresh_token` grants access to your Google data

---

## Complete Workflow

### Step 1: Download Client Secret (One-Time Setup)

1. Visit [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. Create a new project (or select existing)
3. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
4. Choose "Desktop application" as application type
5. Download the JSON file (this is your **client secret file**)

### Step 2: Add Test Users (For Unverified Apps)

If your app hasn't completed Google's verification process:

1. Go to [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. Scroll to "Test users" section
3. Click "Add Users"
4. Add your Gmail address
5. Click "Save"

### Step 3: Complete OAuth Flow

Run the login command with your client secret file:

```bash
google-gmail-tool auth login ~/Downloads/client_secret_*.json
```

This will:
1. Read your client secret file
2. Open your browser for OAuth authorization
3. Ask you to sign in with Google
4. Ask you to grant permissions (Gmail, Calendar, Drive read-only)
5. Save the **authorized user credentials** to `~/.config/google-gmail-tool/credentials.json`

The authorized user credentials file now contains your `refresh_token`!

### Step 4: Use the Tool

Set the environment variable to point to your authorized credentials:

```bash
export GOOGLE_GMAIL_TOOL_CREDENTIALS=~/.config/google-gmail-tool/credentials.json
```

Now you can use all commands:

```bash
# Verify authentication and API access
google-gmail-tool auth check

# Future commands (coming soon)
google-gmail-tool mail list
google-gmail-tool calendar events
google-gmail-tool drive list
```

---

## What Happens Behind the Scenes

### During `auth login`:

1. Tool reads `client_id` and `client_secret` from client secret file
2. Opens browser to Google's OAuth authorization page
3. You sign in and grant permissions
4. Google returns an authorization code
5. Tool exchanges code for:
   - `access_token` (expires in ~1 hour)
   - `refresh_token` (long-lived, can get new access tokens)
6. Tool saves `client_id`, `client_secret`, and `refresh_token` to authorized credentials file

### During normal tool usage:

1. Tool reads authorized credentials file
2. Checks if `access_token` is expired
3. If expired, automatically uses `refresh_token` to get a new `access_token`
4. Makes API calls with valid `access_token`

This is why the `refresh_token` is so important - it allows the tool to work indefinitely without requiring you to re-authorize!

---

## FAQ

### Q: Can I delete the client secret file after running `auth login`?

**A**: Yes! After you have the authorized credentials file with a `refresh_token`, you don't need the client secret file anymore. Archive it somewhere safe in case you need to re-authorize in the future.

### Q: What if my refresh token expires or is revoked?

**A**: Run `google-gmail-tool auth login` again with your client secret file to complete a new OAuth flow and get a new refresh token.

### Q: Where should I store these files?

**A**:
- Client secret file: `~/Downloads/` or archive safely
- Authorized credentials: `~/.config/google-gmail-tool/credentials.json` (default location)

### Q: What OAuth scopes does the tool request?

**A**: The tool requests these scopes:
- `https://www.googleapis.com/auth/gmail.readonly` (read-only)
- `https://www.googleapis.com/auth/gmail.send` (send emails)
- `https://www.googleapis.com/auth/calendar` (full access)
- `https://www.googleapis.com/auth/tasks` (full access)
- `https://www.googleapis.com/auth/drive` (full access)

### Q: How do I revoke access?

**A**: Visit [Google Account Permissions](https://myaccount.google.com/permissions) and remove the app. Then delete your authorized credentials file.

---

## Troubleshooting

### Error: "Access blocked: App has not completed Google verification"

**Solution**: Add yourself as a test user in the OAuth Consent Screen (see Step 2 above).

### Error: "Missing fields client_secret, refresh_token, client_id"

**Solution**: You're using the client secret file instead of authorized credentials. Run `auth login` first to create the authorized credentials.

### Error: "Invalid grant" or "Token has been expired or revoked"

**Solution**: Your refresh token is invalid. Run `auth login` again to get a new one.

---

**Generated with AI**

This documentation was created with assistance from Claude Code to help users understand OAuth credential management for `google-gmail-tool`.
