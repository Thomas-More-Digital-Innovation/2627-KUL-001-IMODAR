import { env } from 'node:process';
import type { RequestHandler } from './$types';

const proxy: RequestHandler = async ({ params, request, url }) => {
  const target = new URL(env.BACKEND_URL ?? 'http://127.0.0.1:8000');
  target.pathname = `/api/${params.path}`;
  target.search = url.search;
  try {
    const response = await fetch(target, {
      method: request.method,
      headers: { 'content-type': request.headers.get('content-type') ?? 'application/json' },
      body: request.method === 'GET' ? undefined : await request.arrayBuffer(),
    });
    return new Response(response.body, {
      status: response.status,
      headers: { 'content-type': response.headers.get('content-type') ?? 'application/json' },
    });
  } catch {
    return Response.json({ detail: 'The IMODAR API is unavailable.' }, { status: 502 });
  }
};

export const GET = proxy;
export const POST = proxy;
