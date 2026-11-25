import { json, request } from './http.ts';
import type { components } from './schema';

type Schemas = components['schemas'];
export type CurrentUser = Schemas['CurrentUser'];

async function call<T>(path: string, init: RequestInit = { method: 'POST' }): Promise<T> {
  const response = await request(`/api/auth/${path}`, 'The request was not accepted.', init);
  return response.status === 204 ? (undefined as T) : response.json();
}

/** Sign-in and account security. */
export const auth = {
  login: (body: Schemas['LoginRequest']) => call<Schemas['LoginResponse']>('login', json(body)),
  enrol: () => call<Schemas['EnrolmentResponse']>('2fa/enrol'),
  confirm: (code: string) => call<Schemas['RecoveryCodesResponse']>('2fa/confirm', json({ code })),
  verify: (code: string) => call<void>('2fa/verify', json({ code })),
  changePassword: (body: Schemas['ChangePasswordRequest']) => call<void>('password', json(body)),
  revokeOthers: () => call<void>('sessions/revoke-others'),
  logout: () => call<void>('logout'),
};

export async function currentUser(fetcher: typeof fetch): Promise<CurrentUser> {
  return (await request('/api/auth/me', 'Your account is unavailable.', {}, fetcher)).json();
}
