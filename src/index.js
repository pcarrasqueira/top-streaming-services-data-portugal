/**
 * Cloudflare Worker for Top Streaming Services Data Portugal
 * 
 * This worker provides an HTTP endpoint to trigger the streaming services data collection
 * and can also run on a scheduled basis using Cloudflare's cron triggers.
 */

export default {
  async fetch(request, env, ctx) {
    try {
      // Handle CORS preflight requests
      if (request.method === 'OPTIONS') {
        return new Response(null, {
          status: 200,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          },
        });
      }

      const url = new URL(request.url);
      
      // Health check endpoint
      if (url.pathname === '/health') {
        return new Response(JSON.stringify({ 
          status: 'healthy', 
          timestamp: new Date().toISOString(),
          environment: env.ENVIRONMENT || 'unknown'
        }), {
          headers: { 'Content-Type': 'application/json' },
        });
      }

      // Trigger endpoint for manual execution
      if (url.pathname === '/trigger' && request.method === 'POST') {
        const result = await executeStreamingServicesScript(env);
        return new Response(JSON.stringify(result), {
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          },
        });
      }

      // Default response
      return new Response(JSON.stringify({
        message: 'Top Streaming Services Data Portugal Worker',
        endpoints: {
          health: '/health',
          trigger: 'POST /trigger'
        },
        timestamp: new Date().toISOString()
      }), {
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
      });

    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({
        error: 'Internal server error',
        message: error.message,
        timestamp: new Date().toISOString()
      }), {
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
      });
    }
  },

  async scheduled(event, env, ctx) {
    console.log('Scheduled event triggered:', event.cron);
    
    try {
      const result = await executeStreamingServicesScript(env);
      console.log('Scheduled execution completed:', result);
    } catch (error) {
      console.error('Scheduled execution failed:', error);
    }
  },
};

/**
 * Execute the streaming services data collection
 * This function calls the GitHub Actions workflow to trigger the Python script
 */
async function executeStreamingServicesScript(env) {
  const startTime = Date.now();
  
  try {
    // For now, we'll call the GitHub Actions workflow
    // In a future version, we could port the Python logic to JavaScript
    const response = await fetch('https://api.github.com/repos/pcarrasqueira/top-streaming-services-data-portugal/actions/workflows/cron_job.yml/dispatches', {
      method: 'POST',
      headers: {
        'Authorization': `token ${env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'Cloudflare-Worker'
      },
      body: JSON.stringify({
        ref: 'main'
      })
    });

    const executionTime = Date.now() - startTime;

    if (response.ok) {
      return {
        success: true,
        message: 'GitHub Actions workflow triggered successfully',
        executionTime: `${executionTime}ms`,
        timestamp: new Date().toISOString(),
        environment: env.ENVIRONMENT || 'unknown'
      };
    } else {
      const errorText = await response.text();
      throw new Error(`GitHub API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

  } catch (error) {
    const executionTime = Date.now() - startTime;
    
    return {
      success: false,
      error: error.message,
      executionTime: `${executionTime}ms`,
      timestamp: new Date().toISOString(),
      environment: env.ENVIRONMENT || 'unknown'
    };
  }
}