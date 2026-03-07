const TARGET = "https://revdlo1.rkinfoarch.workers.dev/";
const BEARER = "Bearer mroldverdict_xK9mP1978";

export async function onRequestPost(ctx) {
  try {
    const body = await ctx.request.text();
    const res = await fetch(TARGET, {
      method: "POST",
      headers: { "Authorization": BEARER, "Content-Type": "application/json" },
      body,
    });
    const text = await res.text();
    const safe = text?.trim() || JSON.stringify({ error: `Empty response (HTTP ${res.status})` });
    return new Response(safe, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
