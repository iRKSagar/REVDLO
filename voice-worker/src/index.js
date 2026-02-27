// Mr. Oldverdict Voice Worker
// Takes a script from Supabase
// Sends lines to ElevenLabs
// Stores audio file in Supabase storage

const ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1";

async function getScript(supabaseUrl, supabaseKey, scriptId) {
  const url = scriptId
    ? `${supabaseUrl}/rest/v1/scripts?id=eq.${scriptId}&limit=1`
    : `${supabaseUrl}/rest/v1/scripts?published=eq.false&order=created_at.asc&limit=1`;

  const response = await fetch(url, {
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`
    }
  });

  if (!response.ok) throw new Error('Failed to fetch script from Supabase');
  const scripts = await response.json();
  if (scripts.length === 0) throw new Error('No unprocessed scripts found');
  return scripts[0];
}

async function generateAudio(elevenLabsKey, voiceId, text) {
  // Mr. Oldverdict voice settings
  // Stability high for consistent dry delivery
  // Similarity boost high to stay true to the voice
  // Style low to avoid over-expression
  // Speaking rate slightly slow for the unhurried pace
  const response = await fetch(`${ELEVENLABS_API_URL}/text-to-speech/${voiceId}`, {
    method: 'POST',
    headers: {
      'xi-api-key': elevenLabsKey,
      'Content-Type': 'application/json',
      'Accept': 'audio/mpeg'
    },
    body: JSON.stringify({
      text: text,
      model_id: 'eleven_monolingual_v1',
      voice_settings: {
        stability: 0.85,
        similarity_boost: 0.90,
        style: 0.10,
        use_speaker_boost: true
      }
    })
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`ElevenLabs API error: ${error}`);
  }

  return await response.arrayBuffer();
}

async function uploadAudioToSupabase(supabaseUrl, supabaseKey, scriptId, audioBuffer) {
  const fileName = `audio/${scriptId}.mp3`;

  const response = await fetch(
    `${supabaseUrl}/storage/v1/object/revdlo-media/${fileName}`,
    {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'audio/mpeg',
        'Cache-Control': '3600'
      },
      body: audioBuffer
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Supabase storage upload failed: ${error}`);
  }

  // Return the public URL
  return `${supabaseUrl}/storage/v1/object/public/revdlo-media/${fileName}`;
}

async function updateVideoRecord(supabaseUrl, supabaseKey, scriptId, audioUrl) {
  // Check if a video record exists for this script
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
    // Update existing record
    await fetch(`${supabaseUrl}/rest/v1/videos?script_id=eq.${scriptId}`, {
      method: 'PATCH',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ voice_file_url: audioUrl })
    });
  } else {
    // Create new video record
    await fetch(`${supabaseUrl}/rest/v1/videos`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        script_id: scriptId,
        voice_file_url: audioUrl
      })
    });
  }
}

function buildFullScript(lines) {
  // Combine all lines into one clean text for ElevenLabs
  // Add natural pause markers using punctuation and spacing
  return lines
    .map((line, index) => {
      let text = line.text;
      // Add pause after line if marked
      if (line.pause_after && index < lines.length - 1) {
        text += '...';
      }
      return text;
    })
    .join(' ');
}

export default {
  async fetch(request, env) {
    if (request.method === 'GET') {
      return new Response(JSON.stringify({ status: 'Voice worker standing by.' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    // Auth check
    const authHeader = request.headers.get('Authorization');
    if (authHeader !== `Bearer ${env.COUNCIL_SECRET}`) {
      return new Response('Unauthorized', { status: 401 });
    }

    try {
      const body = await request.json();
      const scriptId = body.script_id || null;

      // Fetch the script
      const script = await getScript(env.SUPABASE_URL, env.SUPABASE_KEY, scriptId);

      // Build full text from script lines
      const fullText = buildFullScript(script.lines);

      // Generate audio via ElevenLabs
      const audioBuffer = await generateAudio(
        env.ELEVENLABS_API_KEY,
        env.ELEVENLABS_VOICE_ID,
        fullText
      );

      // Upload audio to Supabase storage
      const audioUrl = await uploadAudioToSupabase(
        env.SUPABASE_URL,
        env.SUPABASE_KEY,
        script.id,
        audioBuffer
      );

      // Create or update video record with audio URL
      await updateVideoRecord(env.SUPABASE_URL, env.SUPABASE_KEY, script.id, audioUrl);

      return new Response(JSON.stringify({
        success: true,
        script_id: script.id,
        audio_url: audioUrl,
        text_spoken: fullText
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: error.message
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  },

  // Runs at 7 AM and 6 PM UTC
  // Gives time after ingestion (6 AM) and before publish (11 AM / 8 PM)
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
