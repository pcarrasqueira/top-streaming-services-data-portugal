# Setup Guide

This comprehensive guide will walk you through setting up the Top Streaming Services Data Portugal project from scratch.

## 📋 Prerequisites

### System Requirements
- **Python 3.13+** (recommended) or Python 3.x compatible
- **Git** for version control
- **GitHub Account** for automated execution
- **Trakt.tv Account** for list management
- **Internet Connection** for API access and web scraping

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

#### Create Trakt API Application
1. Navigate to [Trakt API Settings](https://trakt.tv/oauth/applications)
2. Click "New Application"
3. Fill in the application details:
   - **Name**: `Top PT Streaming Services` (or your preferred name)
   - **Description**: `Automated tracking of top streaming content in Portugal`
   - **Redirect URI**: `urn:ietf:wg:oauth:2.0:oob`
   - **Website**: Your GitHub repository URL (optional)
   - **Permissions**: Check all boxes:
     - ✅ Read user profile
     - ✅ Manage user lists
     - ✅ Add/remove items from lists
4. Click "Save App"

#### Get Your API Credentials
After creating the application, you'll see:
- **Client ID**: Copy this value
- **Client Secret**: Copy this value (keep it secure!)

### 4. OAuth Token Generation

#### Manual Token Generation
1. **Authorization URL**: Construct the following URL (replace `YOUR_CLIENT_ID`):
   ```
   https://trakt.tv/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob
   ```

2. **Authorize Application**:
   - Open the URL in your browser
   - Log in to Trakt if prompted
   - Click "Authorize" to grant permissions
   - Copy the authorization code from the page

3. **Exchange Code for Tokens**:
   ```bash
   curl -X POST https://api.trakt.tv/oauth/token \
     -H "Content-Type: application/json" \
     -d '{
       "code": "YOUR_AUTHORIZATION_CODE",
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
       "grant_type": "authorization_code"
     }'
   ```

4. **Save the Response**: You'll receive a JSON response containing:
   - `access_token`: For API requests
   - `refresh_token`: For token renewal
   - `expires_in`: Token expiration time

### 5. Environment Configuration

#### Create Environment File
```bash
touch .env
```

#### Configure Environment Variables
Edit the `.env` file with your credentials:

```env
# Trakt API Credentials (Required)
CLIENT_ID=your_trakt_client_id_here
CLIENT_SECRET=your_trakt_client_secret_here
ACCESS_TOKEN=your_trakt_access_token_here
REFRESH_TOKEN=your_trakt_refresh_token_here

# Optional Configuration
KIDS_LIST=False         # Set to True to include Netflix kids content
PRINT_LISTS=False       # Set to True to print scraped lists to console
```

#### Environment File Example
```env
# Example .env file (replace with your actual values)
CLIENT_ID=abc123def456ghi789
CLIENT_SECRET=xyz789uvw456rst123
ACCESS_TOKEN=token_abcdefghijklmnopqrstuvwxyz123456789
REFRESH_TOKEN=refresh_zyxwvutsrqponmlkjihgfedcba987654321

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

This will show the scraped content before uploading to Trakt.

### 7. GitHub Actions Setup (Automation)

#### Repository Secrets Configuration
1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `CLIENT_ID` | Your Trakt client ID | From step 3 |
| `CLIENT_SECRET` | Your Trakt client secret | From step 3 |
| `ACCESS_TOKEN` | Your Trakt access token | From step 4 |
| `REFRESH_TOKEN` | Your Trakt refresh token | From step 4 |
| `GH_PAT` | GitHub Personal Access Token | For token updates |

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
| `KIDS_LIST` | `true` or `false` | Include kids content |
| `PRINT_LISTS` | `true` or `false` | Enable debug output |

#### Test GitHub Actions
1. Go to **Actions** tab in your repository
2. Click on "Get Top PT Stream Services" workflow
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
**Solution**: Tokens expire. The script auto-refreshes them, but you may need to regenerate manually

##### Missing Lists
```
Warning: Payload is empty
```
**Solution**: Check if FlixPatrol is accessible and the scraping is working correctly

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
python -c "import requests; print('FlixPatrol accessible:', requests.get('https://flixpatrol.com/top10/netflix/portugal/').status_code == 200)"

# Test Trakt API
python -c "import requests, os; from dotenv import load_dotenv; load_dotenv(); headers={'Authorization': f'Bearer {os.getenv(\"ACCESS_TOKEN\")}', 'trakt-api-version': '2', 'trakt-api-key': os.getenv('CLIENT_ID')}; print('Trakt API status:', requests.get('https://api.trakt.tv/users/me', headers=headers).status_code)"
```

## 🎯 Next Steps

### Regular Monitoring
1. **Check Lists**: Periodically verify your Trakt lists are updating
2. **Monitor Actions**: Check GitHub Actions for any failures
3. **Update Tokens**: Refresh tokens when they expire

### Customization Options
1. **Schedule Changes**: Modify `.github/workflows/cron_job.yml` for different timing
2. **Additional Services**: Add support for new streaming platforms
3. **List Customization**: Modify list names and descriptions in the code

### Maintenance
1. **Dependencies**: Keep Python packages updated
2. **API Changes**: Watch for changes in Trakt or FlixPatrol APIs
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