import type { CurrentUser } from '#lib/api/auth.ts';

declare global {
  namespace App {
    interface PageData {
      user: CurrentUser | null;
    }
  }
}

export {};
