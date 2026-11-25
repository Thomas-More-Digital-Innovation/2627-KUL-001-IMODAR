import { error, redirect } from '@sveltejs/kit';
import { currentUser, type CurrentUser } from '#lib/api/auth.ts';
import { ApiError } from '#lib/api/http.ts';
import type { LayoutLoad } from './$types';

// Analyses live in module state, which would be shared between users if it were rendered on the server.
export const ssr = false;

export const load: LayoutLoad = async ({ fetch, url }): Promise<{ user: CurrentUser | null }> => {
  if (url.pathname === '/login') return { user: null };
  try {
    return { user: await currentUser(fetch) };
  } catch (cause) {
    if (!(cause instanceof ApiError)) throw cause;
    if (cause.status === 401) redirect(307, '/login');
    error(cause.status, cause.message);
  }
};
