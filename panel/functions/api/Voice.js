const TARGET = "https://voice.rkinfoarch.workers.dev/";
const BEARER = "Bearer mroldverdict_xK9mP1978";

export async function onRequestPost(ctx) {
  const body = await ctx.request.text();
  const res = await fetch(TARGET, {
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
