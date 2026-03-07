const RENDER  = "https://revdlo.onrender.com";
const BEARER  = "Bearer mroldverdict_xK9mP1978";

export async function onRequestGet(ctx) {
  // Wake call
  const res = await fetch(`${RENDER}/`, { headers: { "Authorization": BEARER } });
  return new Response(JSON.stringify({ ok: true, status: res.status }), {
    headers: { "Content-Type": "application/json" },
  });
}

export async function onRequestPost(ctx) {
  const body = await ctx.request.text();
  const res = await fetch(`${RENDER}/assemble`, {
    method: "POST",
    headers: { "Authorization": BEARER, "Content-Type": "application/json" },
    body,
  });
  const data = await res.text();
  return new Response(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
