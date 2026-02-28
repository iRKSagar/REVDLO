/**
 * Mr. Oldverdict - Orchestration Worker
 * Fires at 7:30 AM and 6:30 PM UTC
 * Wakes Render, fires /run-pipeline, returns immediately
 * Render handles the full pipeline in background
 */

const RENDER_URL = 'https://revdlo.onrender.com';
const BEARER = 'mroldverdict_xK9mP1978';

async function runPipeline(ctx) {
  try {
    // Step 1: Wake Render (free tier sleeps after 15 min)
    console.log('Waking Render...');
    const wakeRes = await fetch(`${RENDER_URL}/`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${BEARER}` }
    });
    console.log(`Render wake status: ${wakeRes.status}`);

    // Step 2: Fire pipeline - Render handles the rest in background
    console.log('Firing pipeline...');
    const pipeRes = await fetch(`${RENDER_URL}/run-pipeline`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${BEARER}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    });

    const pipeData = await pipeRes.json();
    console.log(`Pipeline triggered: ${JSON.stringify(pipeData)}`);

  } catch (err) {
    console.error(`Orchestration error: ${err.message}`);
  }
}

export default {
  // Cron handler - fires at 7:30 AM and 6:30 PM UTC
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runPipeline(ctx));
  },

  // Manual trigger via POST for testing
  async fetch(request, env, ctx) {
    const auth = request.headers.get('Authorization') || '';
    if (auth !== `Bearer ${BEARER}`) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (request.method === 'POST') {
      ctx.waitUntil(runPipeline(ctx));
      return new Response(JSON.stringify({
        status: 'Pipeline triggered',
        message: 'Council → Voice + Image → Assembly running on Render'
      }), {
        status: 202,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify({ status: 'Orchestration worker standing by.' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
};
