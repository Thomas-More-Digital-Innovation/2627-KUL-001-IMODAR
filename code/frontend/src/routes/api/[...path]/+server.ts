import { env } from 'node:process';
import { Agent, fetch } from 'undici';
import type { RequestHandler } from './$types';

// The default of 5 minutes is shorter than an analysis with thinking and retries can take.
const LIMIT_MS = 30 * 60_000;
const dispatcher = new Agent({ headersTimeout: LIMIT_MS, bodyTimeout: LIMIT_MS });

const proxy: RequestHandler = async ({ params, request, url }) => {
  const target = new URL(env.BACKEND_URL ?? 'http://127.0.0.1:8000');
  target.pathname = `/api/${params.path}`;
  target.search = url.search;
  try {
    const response = await fetch(target, {
      dispatcher,
      method: request.method,
      headers: {
        'content-type': request.headers.get('content-type') ?? 'application/json',
        cookie: request.headers.get('cookie') ?? '',
      },
      body: request.method === 'GET' ? undefined : await request.arrayBuffer(),
    });
    const headers = new Headers();
    for (const name of ['content-type', 'cache-control']) {
      const value = response.headers.get(name);
      if (value) headers.set(name, value);
    }
    for (const cookie of response.headers.getSetCookie()) headers.append('set-cookie', cookie);
    return new Response(await response.arrayBuffer(), { status: response.status, headers });
  } catch {
    return Response.json({ detail: 'The IMODAR API is unavailable.' }, { status: 502 });
  }
};

export const GET = proxy;
export const POST = proxy;
