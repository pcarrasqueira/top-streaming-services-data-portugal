# Setup Guide

This comprehensive guide will walk you through setting up the Top Streaming Services Data Portugal project from scratch.

## 📋 Prerequisites

### System Requirements
- **Python 3.13+** (recommended) or Python 3.x compatible
- **Git** for version control
- **GitHub Account** for automated execution
- **Trakt.tv Account** for list management
- **Internet Connection** for Supabase and Trakt API access

### Knowledge Requirements
- Basic command line usage
- Basic understanding of environment variables
- GitHub account and repository management
- Trakt.tv account creation

## 🔧 Step-by-Step Installation

### 1. Repository Setup

#### Clone the Repository
```bash
git clone https://github.com/pcarrasqueira/top-streaming-services-data-portugal.git
cd top-streaming-services-data-portugal
```

#### Fork for Personal Use (Recommended)
1. Go to the [repository page](https://github.com/pcarrasqueira/top-streaming-services-data-portugal)
2. Click "Fork" in the top-right corner
3. Clone your fork:
```bash
git clone https://github.com/YOUR-USERNAME/top-streaming-services-data-portugal.git
cd top-streaming-services-data-portugal
```

### 2. Python Environment Setup

#### Check Python Version
```bash
python --version
# Should be 3.13+ or 3.x compatible
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Verify Installation
```bash
python -c "import requests, bs4, dotenv; print('All dependencies installed successfully!')"
```

### 3. Trakt.tv Setup

#### Create Trakt Account
1. Go to [Trakt.tv](https://trakt.tv/)
2. Sign up for a free account
3. Verify your email address

#### Create a Trakt API app
1. Open [Trakt Developer — My Apps](https://developer.trakt.tv/apps) and create an app.
2. App registration requires a verified GitHub account connected to the developer portal. Trakt's Standard API tier is free; a Trakt VIP subscription is not required.
3. Copy the **Client ID**. A Client Secret and redirect URI are not required for this project's device-code sign-in.

### 4. Connect the Trakt account

The [Authentication guide](https://developer.trakt.tv/docs/authentication-oauth) recommends Device Code Flow for command-line tools and system services. It avoids the HTTPS callback required by the [Authorization Code + PKCE flow](https://developer.trakt.tv/docs/pkce).

1. Create `.env` from `.env.example` if needed, then add the app's Client ID:
   ```env
   CLIENT_ID=your_trakt_client_id
   ```
2. Run the authorization helper:
   ```bash
   python authorize_trakt.py
   ```
3. Open the verification URL printed in the terminal, enter the displayed code, and approve the app. The helper waits for approval, saves the Client ID and tokens to `.env` with owner-only file permissions, then checks the new access token. Token values are never printed.

Access tokens last 7 days. Refresh tokens are single-use: every successful refresh invalidates the previous refresh token and returns a replacement. The GitHub Actions workflow rotates both token secrets before it starts the Trakt sync.

### 5. Environment Configuration

The authorization helper creates or updates `.env` with the Trakt Client ID and tokens. Set optional configuration values in that file as needed:

```env
# Trakt API Credentials (Required)
CLIENT_ID=your_trakt_client_id_here
ACCESS_TOKEN=your_trakt_access_token_here
REFRESH_TOKEN=your_trakt_refresh_token_here

# PeakPlay Supabase (read-only)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_your_key
SUPABASE_COUNTRY_CODE=PT

# Optional Configuration
KIDS_LIST=False         # Set to True to include Netflix kids content
PRINT_LISTS=False       # Set to True to print rankings to console
```

#### Environment File Example
```env
# Example .env file (replace with your actual values)
CLIENT_ID=abc123def456ghi789
ACCESS_TOKEN=token_abcdefghijklmnopqrstuvwxyz123456789
REFRESH_TOKEN=refresh_zyxwvutsrqponmlkjihgfedcba987654321

# Supabase read access for PeakPlay's top10_entries table
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_your_key
SUPABASE_COUNTRY_CODE=PT

# Optional settings
KIDS_LIST=True
PRINT_LISTS=True
```

### 6. Testing Your Setup

#### Basic Functionality Test
```bash
python top_pt_stream_services.py
```

#### Expected Output
```
2024-01-15 10:30:00 - INFO - Trakt access token status: True
2024-01-15 10:30:01 - INFO - Updating list top-portugal-netflix-movies ...
2024-01-15 10:30:02 - INFO - List updated successfully
... (more log entries)
2024-01-15 10:30:15 - INFO - Finished updating lists
```

#### Debug Mode Testing
```bash
PRINT_LISTS=True python top_pt_stream_services.py
```

This will show the rankings loaded from Supabase before they are uploaded to Trakt.

### 7. GitHub Actions Setup (Automation)

#### Repository Secrets Configuration
1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `CLIENT_ID` | Your Trakt client ID | From step 3 |
| `ACCESS_TOKEN` | Your Trakt access token | From step 4 |
| `REFRESH_TOKEN` | Your Trakt refresh token | From step 4 |
| `GH_PAT` | GitHub Personal Access Token | For token updates |
| `SUPABASE_URL` | PeakPlay Supabase project URL | Connect to the project REST API |
| `SUPABASE_PUBLISHABLE_KEY` | Supabase publishable key | Read-only access to PeakPlay rankings |

#### GitHub Personal Access Token (GH_PAT)
1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Configure the token:
   - **Note**: `Top PT Streaming Services - Secret Updates`
   - **Expiration**: 90 days (or your preference)
   - **Scopes**: Select `repo` (Full control of private repositories)
4. Click "Generate token"
5. Copy the token and add it as the `GH_PAT` secret

#### Repository Variables Configuration
1. In the same **Actions** page, go to **Variables** tab
2. Add the following **Repository Variables**:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `SUPABASE_COUNTRY_CODE` | `PT` | Country code to load (defaults to `PT`) |
| `KIDS_LIST` | `true` or `false` | Include kids content |
| `PRINT_LISTS` | `true` or `false` | Enable debug output |

#### Test GitHub Actions
1. Go to **Actions** tab in your repository
2. Click on "Sync Trakt Lists from PeakPlay" workflow
3. Click "Run workflow" to test manual execution
4. Monitor the workflow execution for any errors

### 8. Verification and Troubleshooting

#### Verify Trakt Lists
1. Go to your [Trakt profile](https://trakt.tv/users/me)
2. Check the **Lists** section
3. You should see newly created lists like:
   - Top Portugal Netflix Movies
   - Top Portugal Netflix Shows
   - Top Portugal HBO Movies
   - (etc.)

#### Common Issues and Solutions

##### Authentication Errors
```
Error: Unauthorized (401)
```
**Solution**: Check your CLIENT_ID and ACCESS_TOKEN are correct

##### Token Expired
```
Error: Invalid token
```
**Solution**: GitHub Actions refreshes the token before each Trakt sync. If the refresh step reports `invalid_grant`, run `python authorize_trakt.py` again and replace the `CLIENT_ID`, `ACCESS_TOKEN`, and `REFRESH_TOKEN` repository secrets. For local use, rerun the helper to authorize and store a fresh token pair.

##### Missing Lists
```
Warning: Payload is empty
```
**Solution**: Check that PeakPlay has complete rankings in Supabase and that `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` are configured

##### GitHub Actions Failing
```
Error in workflow execution
```
**Solution**: 
1. Check all secrets are properly configured
2. Verify GH_PAT has correct permissions
3. Check workflow logs for specific errors

#### Debug Commands
```bash
# Test environment loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('CLIENT_ID found:', bool(os.getenv('CLIENT_ID')))"

# Test API connectivity
python -c "import os, requests; from dotenv import load_dotenv; load_dotenv(); key=os.getenv('SUPABASE_PUBLISHABLE_KEY'); r=requests.get(os.getenv('SUPABASE_URL') + '/rest/v1/top10_entries?select=rank&country_code=eq.PT&limit=1', headers={'apikey': key}); print('Supabase accessible:', r.status_code == 200)"

# Test Trakt API
python -c "import requests, os; from dotenv import load_dotenv; load_dotenv(); headers={'Authorization': f'Bearer {os.getenv(\"ACCESS_TOKEN\")}', 'trakt-api-version': '2', 'trakt-api-key': os.getenv('CLIENT_ID')}; print('Trakt API status:', requests.get('https://api.trakt.tv/users/me', headers=headers).status_code)"
```

## 🎯 Next Steps

### Regular Monitoring
1. **Check Lists**: Periodically verify your Trakt lists are updating
2. **Monitor Actions**: Check GitHub Actions for any failures
3. **Update Tokens**: If Trakt rejects a legacy refresh token, reauthorize with `python authorize_trakt.py` and update the three Trakt repository secrets

### Customization Options
1. **Schedule Changes**: Modify `.github/workflows/cron_job.yml` for different timing
2. **Additional Services**: Add support for new streaming platforms
3. **List Customization**: Modify list names and descriptions in the code

### Maintenance
1. **Dependencies**: Keep Python packages updated
2. **API Changes**: Watch for changes in Trakt or Supabase APIs
3. **GitHub Actions**: Update action versions when needed

## 📞 Support

If you encounter issues during setup:

1. **Check the Troubleshooting section** above
2. **Review logs** carefully for error messages
3. **Search existing issues** on GitHub
4. **Create a new issue** with detailed information if needed

### Information to Include in Support Requests
- Python version
- Operating system
- Error messages (with sensitive data removed)
- Steps you've already tried
- Configuration details (without secrets)

---

Congratulations! You should now have a fully functional Top Streaming Services Data Portugal setup. The system will automatically track trending content and keep your Trakt lists updated. 🎉