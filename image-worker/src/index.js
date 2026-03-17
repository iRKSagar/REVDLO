// Mr. Oldverdict Image Worker (Scene-Based with Style Variation)

const LEONARDO_API_URL = "https://cloud.leonardo.ai/api/rest/v1";
const LEONARDO_MODEL_ID = "7b592283-e8a7-4c5a-9ba6-d18c31f258b9";

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
};
const STYLE_POOL = [
  "surreal oil painting",
  "ink wash illustration",
  "watercolor dreamscape",
  "charcoal sketch illustration",
  "paper cut collage artwork",
  "impressionist painting",
  "minimalist graphic poster",
  "abstract conceptual art",
  "vintage illustration",
  "dreamlike cinematic still",
  "storybook illustration",
  "symbolic surreal art"
];
const STYLE_HINTS = [
  "cinematic lighting",
  "dramatic contrast",
  "minimalist composition",
  "documentary photography style",
  "symbolic illustration",
  "moody atmosphere",
  "high contrast lighting",
  "editorial photography",
  "conceptual visual metaphor",
  "dramatic shadows"
];

const NEGATIVE_PROMPT = `
old man,
elderly narrator,
wise man,
talking character,
portrait,
close up face,
text,
logo,
watermark,
cartoon,
anime,
childish,
low quality,
blurry,
deformed
`;

function randomStyle() {
  return STYLE_HINTS[Math.floor(Math.random() * STYLE_HINTS.length)];
}

async function getScriptForImage(supabaseUrl, supabaseKey, scriptId) {

  const url = scriptId
    ? `${supabaseUrl}/rest/v1/scripts?id=eq.${scriptId}&limit=1`
    : `${supabaseUrl}/rest/v1/videos?image_url=is.null&order=created_at.asc&limit=1&select=script_id,scripts(*)`;

  const response = await fetch(url, {
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`
    }
  });

  if (!response.ok) throw new Error('Failed to fetch from Supabase');

  const data = await response.json();
  if (data.length === 0) throw new Error('No scripts pending image generation');

  if (scriptId) return data[0];
  return data[0].scripts;
}

function buildImagePrompt(script) {

  const style = STYLE_POOL[Math.floor(Math.random() * STYLE_POOL.length)];
  const styleHint = STYLE_HINTS[Math.floor(Math.random() * STYLE_HINTS.length)];

  const sceneDirection = script.scene
    .replace('Mr. Oldverdict', '')
    .replace('Mr Oldverdict', '')
    .trim();

  return `
${style},
${styleHint},
symbolic artistic interpretation,
dreamlike atmosphere,
visual metaphor,
conceptual imagery inspired by: ${sceneDirection},
no identifiable characters,
no portraits,
no narrator figure,
artistic composition,
soft cinematic lighting,
depth and texture,
vertical composition,
9:16 frame
`;
}
Scene:
${scene}

Create a strong visual metaphor representing this situation.

${style}

high quality image,
detailed environment,
clear storytelling,
vertical composition,
9:16 frame
`;
}

async function initiateImageGeneration(leonardoKey, prompt) {

  const body = {
    modelId: LEONARDO_MODEL_ID,
    prompt: prompt,
    negative_prompt: NEGATIVE_PROMPT,
    num_images: 1,
    width: 576,
    height: 1024,
    guidance_scale: 7,
    num_inference_steps: 30,
    public: false
  };

  const response = await fetch(`${LEONARDO_API_URL}/generations`, {
    method: 'POST',
    headers: {
      'authorization': `Bearer ${leonardoKey}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Leonardo generation initiation failed: ${error}`);
  }

  const data = await response.json();
  return data.sdGenerationJob.generationId;
}

async function pollForImage(leonardoKey, generationId, maxAttempts = 20) {

  for (let attempt = 0; attempt < maxAttempts; attempt++) {

    await new Promise(resolve => setTimeout(resolve, 3000));

    const response = await fetch(`${LEONARDO_API_URL}/generations/${generationId}`, {
      headers: {
        'authorization': `Bearer ${leonardoKey}`,
        'content-type': 'application/json'
      }
    });

    if (!response.ok) continue;

    const data = await response.json();
    const generation = data.generations_by_pk;

    if (generation?.status === 'COMPLETE') {
      const imageUrl = generation.generated_images?.[0]?.url;
      if (imageUrl) return imageUrl;
    }

    if (generation?.status === 'FAILED') {
      throw new Error('Leonardo image generation failed');
    }
  }

  throw new Error('Image generation timed out');
}

async function downloadAndUploadImage(supabaseUrl, supabaseKey, scriptId, leonardoImageUrl) {

  const imageResponse = await fetch(leonardoImageUrl);
  if (!imageResponse.ok) throw new Error('Failed to download image');

  const imageBuffer = await imageResponse.arrayBuffer();
  const fileName = `images/${scriptId}.jpg`;

  const uploadResponse = await fetch(
    `${supabaseUrl}/storage/v1/object/revdlo-media/${fileName}`,
    {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'image/jpeg',
        'Cache-Control': '3600'
      },
      body: imageBuffer
    }
  );

  if (!uploadResponse.ok) {
    const error = await uploadResponse.text();
    throw new Error(`Supabase image upload failed: ${error}`);
  }

  return `${supabaseUrl}/storage/v1/object/public/revdlo-media/${fileName}`;
}

async function updateVideoWithImage(supabaseUrl, supabaseKey, scriptId, imageUrl) {

  const checkResponse = await fetch(
    `${supabaseUrl}/rest/v1/videos?script_id=eq.${scriptId}&limit=1`,
    {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      }
    }
  );

  const existing = await checkResponse.json();

  if (existing.length > 0) {

    await fetch(`${supabaseUrl}/rest/v1/videos?script_id=eq.${scriptId}`, {
      method: 'PATCH',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image_url: imageUrl })
    });

  } else {

    await fetch(`${supabaseUrl}/rest/v1/videos`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ script_id: scriptId, image_url: imageUrl })
    });

  }
}

export default {
  async fetch(request, env) {

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (request.method === 'GET') {
      return new Response(JSON.stringify({ status: 'Scene image worker ready.' }), {
        headers: { 'Content-Type': 'application/json', ...CORS_HEADERS }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: CORS_HEADERS });
    }

    const authHeader = request.headers.get('Authorization');
    if (authHeader !== `Bearer ${env.COUNCIL_SECRET}`) {
      return new Response('Unauthorized', { status: 401, headers: CORS_HEADERS });
    }

    try {

      const body = await request.json();
      const scriptId = body.script_id || null;

      const script = await getScriptForImage(env.SUPABASE_URL, env.SUPABASE_KEY, scriptId);

      const imagePrompt = buildImagePrompt(script);

      const generationId = await initiateImageGeneration(env.LEONARDO_API_KEY, imagePrompt);

      const leonardoImageUrl = await pollForImage(env.LEONARDO_API_KEY, generationId);

      const supabaseImageUrl = await downloadAndUploadImage(
        env.SUPABASE_URL,
        env.SUPABASE_KEY,
        script.id,
        leonardoImageUrl
      );

      await updateVideoWithImage(
        env.SUPABASE_URL,
        env.SUPABASE_KEY,
        script.id,
        supabaseImageUrl
      );

      return new Response(JSON.stringify({
        success: true,
        script_id: script.id,
        image_url: supabaseImageUrl,
        prompt_used: imagePrompt
      }), {
        headers: { 'Content-Type': 'application/json', ...CORS_HEADERS }
      });

    } catch (error) {

      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...CORS_HEADERS }
      });

    }
  },

  async scheduled(event, env, ctx) {

    ctx.waitUntil(
      fetch(`https://${env.WORKER_DOMAIN}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.COUNCIL_SECRET}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
    );

  }
};
