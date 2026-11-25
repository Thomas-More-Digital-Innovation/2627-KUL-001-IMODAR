import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

// Navigation only: every admin endpoint must enforce the role itself.
export const load: LayoutLoad = async ({ parent }) => {
  const { user } = await parent();
  if (user?.role !== 'admin') redirect(307, '/');
};
