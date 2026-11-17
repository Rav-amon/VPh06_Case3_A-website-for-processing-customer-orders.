import type { ILeadPayload } from '@/types/api';

export type TClientRole = 'сотрудник' | 'руководитель';

export type TLeadFormValues = Omit<ILeadPayload, 'client_role'> & {
  client_role: TClientRole;
};

export type TFieldErrors = Partial<Record<keyof TLeadFormValues, string>>;

export type TSubmitState = 'idle' | 'loading' | 'success' | 'error';
