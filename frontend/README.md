# Frontend — Autéllo Barskiy

Одностраничное приложение заявки для «тёплых клиентов» (React 18, TypeScript, Vite, Tailwind CSS, Zod).

## Стек и структура

- `src/api/` — клиент запросов к `/api/v1/*` (`admin-settings`, `leads`, `behavior`)
- `src/components/` — форма анкеты (`LeadForm`), поля ввода (`Field`), ползунок бюджета (`BudgetSlider`), фоновая анимация (`GoldOrbs`)
- `src/hooks/` — трекер поведенческих метрик (`useBehaviorTracker`)
- `src/pages/` — главная страница (`HomePage`)
- `src/utils/` — схема валидации Zod и форматирование сумм
- `src/types/` — типы API и состояния формы

## Сборка и запуск

Разработка (с проксированием `/api` в Nginx):

```bash
npm install
npm run dev
```

Сборка статики в `dist/` для Nginx:

```bash
npm install
npm run build
```

После сборки из корня проекта обновите контейнер Nginx:

```bash
docker compose up -d nginx
```
