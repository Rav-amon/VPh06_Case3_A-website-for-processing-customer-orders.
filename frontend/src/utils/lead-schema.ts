import { z } from 'zod';

const REQUIRED_MESSAGE = 'Заполните поле';
const MAX_NAME = 100;
const MAX_SHORT = 200;
const MAX_LONG = 4000;

const requiredText = (max: number) =>
  z.string().trim().min(1, REQUIRED_MESSAGE).max(max, `Не длиннее ${max} символов`);

const optionalText = (max: number) =>
  z.string().trim().max(max, `Не длиннее ${max} символов`);

export const leadSchema = z
  .object({
    first_name: requiredText(MAX_NAME),
    last_name: requiredText(MAX_NAME),
    middle_name: optionalText(MAX_NAME),
    phone: optionalText(32),
    email: optionalText(254),
    business_info: requiredText(MAX_LONG),
    niche: requiredText(MAX_SHORT),
    company_size: requiredText(MAX_SHORT),
    business_size: requiredText(MAX_SHORT),
    company_volume: requiredText(MAX_SHORT),
    demand_volume: requiredText(MAX_SHORT),
    tasks: requiredText(MAX_LONG),
    client_role: z.enum(['сотрудник', 'руководитель'], {
      errorMap: () => ({ message: 'Выберите роль' }),
    }),
    deadline: requiredText(MAX_SHORT),
    task_type: requiredText(MAX_SHORT),
    product_interest: requiredText(MAX_SHORT),
    budget: requiredText(MAX_SHORT),
    contact_method: requiredText(MAX_SHORT),
    convenient_time: requiredText(MAX_SHORT),
    comment: optionalText(MAX_LONG),
  })
  .superRefine((value, context) => {
    if (value.phone === '' && value.email === '') {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Укажите телефон или почту',
        path: ['phone'],
      });
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Укажите телефон или почту',
        path: ['email'],
      });
    }
    if (value.email !== '' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.email)) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Проверьте формат почты',
        path: ['email'],
      });
    }
  });

export type TLeadSchema = z.infer<typeof leadSchema>;

/**
 * Проверяет одно поле на blur. Пустое необязательное поле пропускает.
 */
export function validateField(
  name: keyof TLeadSchema,
  values: TLeadSchema,
): string | undefined {
  const result = leadSchema.safeParse(values);
  if (result.success) {
    return undefined;
  }
  const issue = result.error.issues.find((item) => item.path[0] === name);
  return issue?.message;
}
