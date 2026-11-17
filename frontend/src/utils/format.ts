/** Форматирует сумму бюджета для подписи ползунка. */
export function formatBudget(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value) + ' ₽';
}
