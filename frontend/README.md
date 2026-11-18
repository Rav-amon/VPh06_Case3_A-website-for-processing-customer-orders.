# Frontend — Autéllo Barskiy

Одностраничное приложение заявки для «тёплых клиентов» (React 18, TypeScript, Vite, Tailwind CSS, Zod).

## Стек и структура

- `src/api/` — клиент `/api/v1/*` (`auth`, `admin-settings`, `stats`, `leads`, `behavior`)
- `src/components/` — форма анкеты, поля, ползунок, админ-редактор услуг и статистика
- `src/hooks/` — трекер поведения и сессия администратора (`useAuth`)
- `src/pages/` — главная и админ-панель (`/admin`, `/admin/login`)
- `src/utils/` — Zod, форматирование, хранение JWT
- `src/types/` — типы API и состояния формы

Админка: `/admin` (JWT). Пока нет ни одного администратора, на `/admin/login` видна кнопка регистрации.

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
