// Mr. Oldverdict Image Worker
// Generates two images per script:
//   hook_image — the modern world, philosophical, cinematic, scroll-stopping
//   main_image — the atmospheric scene, mood and weight

const LEONARDO_API_URL = 'https://cloud.leonardo.ai/api/rest/v1';
const LEONARDO_MODEL_ID = '7b592283-e8a7-4c5a-9ba6-d18c31f258b9';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
};

// ── Hook image style pool ─────────────────────────────────────────────────────
// These govern how the modern world is rendered in the hook image.
// Chosen to feel heavy, timeless, and philosophically loaded.
const HOOK_STYLE_POOL = [
  'dramatic chiaroscuro oil painting, Rembrandt lighting, rich dark tones',
  'surreal symbolic still life, painterly, museum quality, dark background',
  'cinematic wide shot, golden hour light, lone subject in vast environment',
  'ink wash illustration, deep black shadows, strong negative space',
  'hyperrealistic editorial photograph, stark natural light, documentary gravity',
  'baroque still life painting style, candlelight, heavy shadows, classical composition',
  'dreamlike impressionist scene, soft brushwork, melancholic atmosphere',
  'conceptual art poster, bold graphic composition, philosophical weight',
  'vintage engraving style, fine line detail, aged paper tones, timeless feel',
  'cinematic film still, desaturated tones, environmental storytelling',
  'abstract expressionist, bold strokes, emotional intensity, dark palette',
  'architectural photography style, vast interior, single light source, solitude',
];

// ── Main scene style pool ─────────────────────────────────────────────────────
// These govern the atmospheric scene — mood, stillness, age.
const MAIN_STYLE_POOL = [
  'cinematic still, moody atmospheric light, old world gravitas',
  'painterly impressionist landscape, late afternoon light, quiet solitude',
  'surreal oil painting, dreamlike quality, philosophical depth',
  'editorial photography, natural window light, contemplative atmosphere',
  'charcoal and ink illustration, strong shadows, timeless quality',
  'watercolor dreamscape, soft washes, faded memory quality',
  'vintage cinematic still, grain texture, desaturated warmth',
  'expressionist scene, heavy brushwork, emotional weight',
  'symbolic landscape, dramatic clouds, small figure in vast space',
  'museum quality painting, dramatic side lighting, classical stillness',
];

// ── Composition archetypes for hook images ────────────────────────────────────
// Maps script categories to visual storytelling approaches
const HOOK_COMPOSITIONS = {
  A: [ // Modern behavior
    'single modern object isolated on dark surface, extreme close-up, dramatic side lighting',
    'symbolic still life of modern life, objects arranged like a vanitas painting',
    'empty modern interior, traces of human presence but no people, cinematic wide shot',
    'modern object in ancient or natural setting, scale and context create irony',
  ],
  B: [ // Work and ambition
    'empty office chair at vast desk, single desk lamp, night window behind',
    'a towering stack of identical documents or folders, studio lighting, dark background',
    'corporate object rendered as ancient artifact under museum spotlight',
    'long empty conference table, chairs abandoned, fluorescent light overhead',
  ],
  C: [ // Relationships
    'two empty chairs facing different directions, soft evening light, garden setting',
    'a dinner table set for two, one place untouched, candle burning low',
    'a telephone or communication device rendered as ancient relic, dark background',
    'doorway opening to empty room, warm light spilling out, threshold moment',
  ],
  D: [ // Time and meaning
    'hourglass with unusual contents, close-up, dramatic lighting, dark background',
    'calendar or clock in unusual environment, nature reclaiming it, philosophical',
    'old photograph of a place, placed in the actual location now changed',
    'a path splitting in a vast landscape, aerial view, small scale of choice',
  ],
  E: [ // Value reversal
    'two objects on scales — one ancient and simple, one modern and complex',
    'before and after objects side by side, lighting tells the story of value shift',
    'ancient skill or craft shown beside its modern equivalent, dramatic contrast',
    'object of great craftsmanship abandoned beside something mass-produced',
  ],
};

const NEGATIVE_PROMPT = `
human face, person, portrait, selfie, close-up face, old man, narrator character,
text overlay, logo, watermark, caption, subtitle,
cartoon, anime, childish, cheerful, bright colors,
low quality, blurry, deformed, distorted, ugly,
modern digital art style, neon, flat design
`;

function pickFrom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function buildHookImagePrompt(script) {
  const hookScene  = script.hook_scene || `A symbolic representation of: ${script.setup}. No people. Dramatic lighting.`;
  const style      = pickFrom(HOOK_STYLE_POOL);
  const category   = script.category || 'A';
  const comps      = HOOK_COMPOSITIONS[category] || HOOK_COMPOSITIONS['A'];
  const composition = pickFrom(comps);

  return [
    style,
    hookScene,
    composition,
    'no people, no faces, no text',
    'vertical 9:16 composition',
    'cinematic depth of field',
    'single strong light source',
    'philosophically weighted',
    'scroll-stopping visual impact',
  ].join(', ');
}

function buildMainImagePrompt(script) {
  const scene = (script.scene || 'A timeless atmospheric environment, quiet and heavy with age.')
    .replace(/Mr\.?\s*Oldverdict/gi, '')
    .trim();

  const style = pickFrom(MAIN_STYLE_POOL);

  const moods = [
    'quiet contemplative atmosphere',
    'heavy with unspoken weight',
    'stillness that precedes a verdict',
    'the calm of someone who has seen everything',
    'timeless and unhurried',
  ];

  return [
    style,
    scene,
    pickFrom(moods),
    'no people, no faces, no text',
    'vertical 9:16 composition',
    'old world visual language',
    'painterly or cinematic quality',
    'deep atmospheric detail',
  ].join(', ');
}

async function getScript(supabaseUrl, supabaseKey, scriptId) {
  const url = scriptId
    ? `${supabaseUrl}/rest/v1/scripts?id=eq.${scriptId}&limit=1`
    : `${supabaseUrl}/rest/v1/videos?image_url=is.null&order=created_at.asc&limit=1&select=script_id,scripts(*)`;

  const response = await fetch(url, {
    headers: { 'apikey': supabaseKey, 'Authorization': `Bearer ${supabaseKey}` }
  });

  if (!response.ok) throw new Error('Failed to fetch script from Supabase');
  const data = await response.json();
  if (!data.length) throw new Error('No script found');
  return scriptId ? data[0] : data[0].scripts;
}

async function generateImage(leonardoKey, prompt, label) {
  console.log(`[image-worker] Generating ${label} image...`);

  const initRes = await fetch(`${LEONARDO_API_URL}/generations`, {
    method: 'POST',
    headers: {
      'authorization': `Bearer ${leonardoKey}`,
      'content-type':  'application/json'
    },
    body: JSON.stringify({
      modelId:             LEONARDO_MODEL_ID,
      prompt,
      negative_prompt:     NEGATIVE_PROMPT,
      num_images:          1,
      width:               576,
      height:              1024,
      guidance_scale:      7,
      num_inference_steps: 30,
      public:              false
    })
  });

  if (!initRes.ok) {
    const err = await initRes.text();
    throw new Error(`Leonardo ${label} generation failed: ${err}`);
  }

  const initData    = await initRes.json();
  const generationId = initData.sdGenerationJob.generationId;

  // Poll for completion
  for (let attempt = 0; attempt < 20; attempt++) {
    await new Promise(r => setTimeout(r, 3000));

    const pollRes = await fetch(`${LEONARDO_API_URL}/generations/${generationId}`, {
      headers: {
        'authorization': `Bearer ${leonardoKey}`,
        'content-type':  'application/json'
      }
    });

    if (!pollRes.ok) continue;

    const pollData   = await pollRes.json();
    const generation = pollData.generations_by_pk;

    if (generation?.status === 'COMPLETE') {
      const imageUrl = generation.generated_images?.[0]?.url;
      if (imageUrl) {
        console.log(`[image-worker] ${label} image complete`);
        return imageUrl;
      }
    }
    if (generation?.status === 'FAILED') {
      throw new Error(`Leonardo ${label} generation failed`);
    }
  }

  throw new Error(`${label} image generation timed out`);
}

async function uploadToSupabase(supabaseUrl, supabaseKey, leonardoUrl, path) {
  const imgRes = await fetch(leonardoUrl);
  if (!imgRes.ok) throw new Error(`Failed to download image from Leonardo: ${leonardoUrl}`);

  const buffer = await imgRes.arrayBuffer();

  const uploadRes = await fetch(
    `${supabaseUrl}/storage/v1/object/revdlo-media/${path}`,
    {
      method:  'POST',
      headers: {
        'apikey':        supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type':  'image/jpeg',
        'Cache-Control': '3600',
        'x-upsert':      'true'
      },
      body: buffer
    }
  );

  if (!uploadRes.ok) {
    const err = await uploadRes.text();
    throw new Error(`Supabase upload failed for ${path}: ${err}`);
  }

  return `${supabaseUrl}/storage/v1/object/public/revdlo-media/${path}`;
}

async function saveUrls(supabaseUrl, supabaseKey, scriptId, imageUrl, hookImageUrl) {
  // Check if videos row exists
  const checkRes = await fetch(
    `${supabaseUrl}/rest/v1/videos?script_id=eq.${scriptId}&limit=1`,
    { headers: { 'apikey': supabaseKey, 'Authorization': `Bearer ${supabaseKey}` } }
  );
  const existing = await checkRes.json();

  const payload = {
    image_url:      imageUrl,
    hook_image_url: hookImageUrl,
  };

  if (existing.length > 0) {
    await fetch(`${supabaseUrl}/rest/v1/videos?script_id=eq.${scriptId}`, {
      method:  'PATCH',
      headers: {
        'apikey':        supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type':  'application/json'
      },
      body: JSON.stringify(payload)
    });
  } else {
    await fetch(`${supabaseUrl}/rest/v1/videos`, {
      method:  'POST',
      headers: {
        'apikey':        supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type':  'application/json'
      },
      body: JSON.stringify({ script_id: scriptId, ...payload })
    });
  }
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }
    if (request.method === 'GET') {
      return new Response(JSON.stringify({ status: 'Image worker ready. Two images per script.' }), {
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
      const body     = await request.json();
      const scriptId = body.script_id || null;

      const script = await getScript(env.SUPABASE_URL, env.SUPABASE_KEY, scriptId);

      // Build prompts
      const hookPrompt = buildHookImagePrompt(script);
      const mainPrompt = buildMainImagePrompt(script);

      console.log(`[image-worker] script=${script.id} category=${script.category}`);
      console.log(`[image-worker] hook_prompt=${hookPrompt.slice(0, 120)}...`);
      console.log(`[image-worker] main_prompt=${mainPrompt.slice(0, 120)}...`);

      // Generate both images — hook first (more important), then main
      const hookLeonardoUrl = await generateImage(env.LEONARDO_API_KEY, hookPrompt, 'hook');
      const mainLeonardoUrl = await generateImage(env.LEONARDO_API_KEY, mainPrompt, 'main');

      // Upload both to Supabase storage
      const hookImageUrl = await uploadToSupabase(
        env.SUPABASE_URL, env.SUPABASE_KEY,
        hookLeonardoUrl,
        `images/${script.id}_hook.jpg`
      );
      const mainImageUrl = await uploadToSupabase(
        env.SUPABASE_URL, env.SUPABASE_KEY,
        mainLeonardoUrl,
        `images/${script.id}.jpg`
      );

      // Save both URLs to videos table
      await saveUrls(
        env.SUPABASE_URL, env.SUPABASE_KEY,
        script.id, mainImageUrl, hookImageUrl
      );

      return new Response(JSON.stringify({
        success:        true,
        script_id:      script.id,
        image_url:      mainImageUrl,
        hook_image_url: hookImageUrl,
      }), {
        headers: { 'Content-Type': 'application/json', ...CORS_HEADERS }
      });

    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status:  500,
        headers: { 'Content-Type': 'application/json', ...CORS_HEADERS }
      });
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      fetch(`https://${env.WORKER_DOMAIN}/`, {
        method:  'POST',
        headers: {
          'Authorization': `Bearer ${env.COUNCIL_SECRET}`,
          'Content-Type':  'application/json'
        },
        body: JSON.stringify({})
      })
    );
  }
};
