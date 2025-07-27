# Cloudflare Worker Deployment

This project supports deployment as a Cloudflare Worker, providing an alternative to GitHub Actions for running the streaming services data collection.

## Features

The Cloudflare Worker provides:

- **Scheduled Execution**: Runs automatically on the same schedule as GitHub Actions (00:00, 08:00, 12:00, 17:00 UTC)
- **HTTP API**: Manual triggering via HTTP endpoints
- **Health Checks**: Status monitoring and health check endpoints
- **Environment Management**: Support for development, staging, and production environments

## Prerequisites

- **Cloudflare Account**: [Sign up for free](https://dash.cloudflare.com/sign-up)
- **Wrangler CLI**: Install with `npm install -g wrangler`
- **GitHub Personal Access Token**: For triggering GitHub Actions (optional)

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Cloudflare

```bash
# Login to Cloudflare
wrangler login

# Set up secrets
wrangler secret put CLIENT_ID
wrangler secret put ACCESS_TOKEN
wrangler secret put REFRESH_TOKEN
wrangler secret put CLIENT_SECRET
wrangler secret put GITHUB_TOKEN  # Optional, for GitHub Actions integration
```

### 3. Deploy

```bash
# Deploy to development
npm run deploy

# Deploy to staging
npm run deploy:staging

# Deploy to production
npm run deploy:production
```

## API Endpoints

Once deployed, the worker provides these endpoints:

- `GET /health` - Health check and status
- `POST /trigger` - Manually trigger data collection
- `GET /` - Worker information and available endpoints

## Environment Variables

The worker uses the same environment variables as the Python script:

- `CLIENT_ID` - Trakt.tv API client ID
- `ACCESS_TOKEN` - Trakt.tv access token
- `REFRESH_TOKEN` - Trakt.tv refresh token
- `CLIENT_SECRET` - Trakt.tv client secret
- `GITHUB_TOKEN` - GitHub personal access token (optional)
- `KIDS_LIST` - Include kids content (true/false)
- `PRINT_LISTS` - Enable debug output (true/false)

## GitHub Actions Integration

The worker can trigger the existing GitHub Actions workflow, maintaining the same Python-based logic while providing Cloudflare's scheduling and HTTP API capabilities.

To set up automatic deployment:

1. Add these secrets to your GitHub repository:
   - `CLOUDFLARE_API_TOKEN` - Cloudflare API token with Workers edit permissions
   - `CLOUDFLARE_ACCOUNT_ID` - Your Cloudflare account ID

2. The worker will automatically deploy when changes are pushed to the `main` branch.

## Local Development

```bash
# Start local development server
npm run dev

# Test the worker locally
curl http://localhost:8787/health
```

## Monitoring

Monitor your worker through the Cloudflare dashboard:

1. Go to **Workers & Pages** in your Cloudflare dashboard
2. Click on `top-streaming-services-portugal`
3. View metrics, logs, and configure alerts

## Cost Considerations

Cloudflare Workers includes:

- **Free Tier**: 100,000 requests per day
- **Scheduled Events**: Included in free tier
- **CPU Time**: 10ms per request on free tier

This project's usage should comfortably fit within the free tier limits.