# Autéllo Barskiy

Закрытый контур приёма заявок для «тёплых клиентов» с анализом приоритетности лидов, сбором живых поведенческих метрик и защищённой панелью администратора.

Снаружи открыт только **Nginx** на порту **`:80`** (статика фронтенда и узкий прокси `/api/`).  
**FastAPI backend** (`:8000`) и **PostgreSQL** (`:5432`) изолированы во внутренних сетях Docker и наружу не публикуются.  
Сервисы **pgAdmin** и **registry** вынесены в профиль `tools` и по умолчанию отключены.

---

## Структура проекта

```text
Autéllo_Barskiy/
├── backend/                     # Приватный FastAPI + asyncpg сервис
│   ├── app/
│   │   ├── core/                # Конфигурация, пул БД, схема, JWT/bcrypt, скоринг лидов, логи
│   │   ├── models/              # SQL-модели в докстрингах + CRUD и агрегаты статистики
│   │   ├── routes/              # Роуты FastAPI (/api/v1/* и /api/*)
│   │   └── main.py              # Точка входа и lifespan-инициализация схемы
│   ├── tests/                   # Модульные тесты без БД
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── api/                 # Клиенты к API (auth, admin, applications, leads, behavior-metrics)
│   │   ├── components/
│   │   │   ├── admin/           # Таблица заявок, карточка лида, редактор услуг, статистика, хитмап
│   │   │   └── ...              # Форма заявки, ползунок бюджета, поля, фоновые сферы
│   │   ├── hooks/               # Авторизация (useAuth) и трекеры поведения (useLiveMetrics)
│   │   ├── pages/               # Главная страница и страницы админ-панели (/admin, /admin/login)
│   │   ├── types/               # TypeScript-интерфейсы API и форм
│   │   └── utils/               # Zod-валидация, хранение JWT, агрегация хитмапа и времени
│   ├── index.html
│   └── package.json
├── nginx/
│   ├── nginx.conf               # Глобальные настройки и rate limit (zone=site)
│   ├── conf.d/
│   │   ├── site.conf            # Публичный вход :80 (статика dist + разрешённые /api/)
│   │   ├── backend-proxy.inc    # Проксирование в http://backend:8000
│   │   └── registry.conf.disabled
│   └── html/                    # Резервная заглушка
├── pgadmin/
│   └── servers.json             # Преднастроенное подключение leads-local (для профиля tools)
├── postgres/
│   ├── init/
│   │   └── 01-app-role.sh       # Создание ограниченной роли LEADS_APP_USER
│   └── seed/
│       └── 10-test-leads.sql    # 10 тестовых заявок (4 hot, 3 warm, 3 cold)
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## Архитектура и сеть

| Сервис | Образ | Сети Docker | Доступ |
|---|---|---|---|
| `nginx` | `nginx:1.28-alpine` | `edge`, `app` | `:80` (сайт и разрешённые `/api/*`) |
| `frontend` | статика `frontend/dist` | — | монтируется в `nginx` (`:ro`) |
| `backend` | `autello-barskiy-backend:latest` | `app`, `data` (`internal`) | только внутри сети `app` (`8000/tcp`) |
| `postgres` | `postgres:17-alpine` | `data` (`internal`) | только внутри сети `data` (`5432/tcp`) |
| `watchtower` | `nickfedor/watchtower:1.24.0` | `host` | автообновление помеченных образов раз в сутки |
| `pgadmin` | `dpage/pgadmin4:9.10` | `data`, `admin` | **отключён** (профиль `tools`, `127.0.0.1:5050`) |
| `registry` | `registry:2` | `registry_net` (`internal`) | **отключён** (профиль `tools`) |

`postgres` и `backend` исключены из автообновления Watchtower (`com.centurylinklabs.watchtower.enable=false`).

---

## Переменные окружения

Рабочие секреты хранятся в `.env` (в GitHub не попадает). Образец: `.env.example`.

| Переменная | Назначение |
|---|---|
| `POSTGRES_DB` | Имя базы заявок (по умолчанию `leads`) |
| `POSTGRES_USER` | Суперпользователь Postgres |
| `POSTGRES_PASSWORD` | Пароль суперпользователя Postgres |
| `LEADS_APP_USER` | Ограниченная роль приложения для backend |
| `LEADS_APP_PASSWORD` | Пароль роли приложения |
| `JWT_SECRET` | Секрет подписи JWT админ-панели (32–256 символов) |
| `JWT_EXPIRE_MINUTES` | Срок жизни JWT в минутах (по умолчанию `720`) |
| `PGADMIN_DEFAULT_EMAIL` | Логин в pgAdmin (если включён профиль `tools`) |
| `PGADMIN_DEFAULT_PASSWORD` | Пароль в pgAdmin |
| `REGISTRY_USER` | Логин локального реестра (если включён профиль `tools`) |
| `REGISTRY_PASSWORD` | Пароль локального реестра |
| `REGISTRY_HTTP_SECRET` | Секрет реестра |
| `REGISTRY_HOST` | Хост реестра |

---

## Сборка и запуск

Имя проекта в Docker: `autello_barskiy`. Перед запуском Nginx должен существовать каталог `frontend/dist`.

### 1. Сборка фронтенда

```bash
cd frontend
npm install
npm run build
```

*(Если Node.js установлен локально в `~/.local/node/bin`, добавьте его в `PATH`: `export PATH="$HOME/.local/node/bin:$PATH"`.)*

### 2. Настройка `.env` и запуск контура

```bash
cp .env.example .env
# заполните пароли и JWT_SECRET в .env

docker compose build backend
docker compose up -d
docker compose ps
```

### 3. Обновление после правок

Обновить фронтенд:

```bash
cd frontend && npm run build && cd ..
docker compose exec nginx nginx -s reload
```

Обновить бэкенд:

```bash
docker compose build backend && docker compose up -d backend
```

Остановить контур с сохранением томов:

```bash
docker compose down
```

Данные сохраняются в томах `autello_barskiy_postgres_data`, `autello_barskiy_pgadmin_data`, `autello_barskiy_registry_data`.

---

## Модели данных (PostgreSQL)

SQL создания каждой таблицы хранится в докстринге соответствующего класса в `backend/app/models/` и автоматически применяется при старте приложения:

1. **`Lead` (`leads`)** — анкета клиента: ФИО, телефон/почта (обязательно хотя бы одно), информация о бизнесе, ниша, размер компании, размер бизнеса, объём, объём потребности, задачи, роль (`сотрудник` / `руководитель`), срок, тип задачи, интересующий продукт, бюджет, способ связи, удобное время, комментарий.
2. **`LeadBehavior` (`lead_behavior`)** — итоговые метрики поведения при отправке заявки (`lead_id` как `PRIMARY KEY REFERENCES leads(id) ON DELETE CASCADE`, связь `1:1`).
3. **`BehaviorMetrics` (`behavior_metrics`)** — посекундные снимки живых метрик главной страницы (`application_id`, `time_on_page` в секундах, `buttons_clicked`, `cursor_positions`, `return_frequency`).
4. **`AdminSettings` (`admin_settings`)** — единственная строка настроек (`id = 1`): список услуг (`code`, `title`, `description`, `price_min`, `price_max`, `is_active`) и границы ползунка бюджета (`budget_min`, `budget_max`, `budget_step`).
5. **`Admin` (`admins`)** — учётные записи администраторов (`login`, `password_hash` в bcrypt). Регистрация через API открыта только пока таблица пуста.

---

## Функциональность

### Главная страница (`/`)
- Форма заявки с Zod-валидацией, загрузкой активных услуг и границ ползунка бюджета из `/api/v1/admin-settings`.
- Сбор поведенческих метрик: каждую секунду фиксируется время на странице (в секундах), клики по кнопкам и координаты курсора (`pageX`, `pageY`), данные отправляются на `POST /api/behavior-metrics/`.

### Панель администратора (`/admin`, `/admin/login`)
- **JWT-авторизация**: при отсутствии или невалидности токена выполняется переход на `/admin/login`.
- **Одноразовая регистрация**: пока в `admins` нет ни одного пользователя, на странице входа доступна кнопка **«Зарегистрироваться»**. После создания первого администратора регистрация автоматически закрывается (`403`).
- **Вкладка «Заявки»**:
  - Интеллектуальный скоринг (`backend/app/core/lead_intelligence.py`) оценивает заявку (0–100) по роли, сроку, бюджету, масштабу компании, объёму задач, нише и типу задачи.
  - Определяет температуру (`Горячий`, `Тёплый`, `Холодный`), необходимость персонального менеджера, целесообразность приоритета и рекомендуемый отдел (`Enterprise`, `Маркетинг`, `Поддержка`, `Продажи`, `Квалификация`).
  - Очередь автоматически сортируется: горячие заявки поднимаются вверх.
  - По кнопке **«Открыть»** доступна полная карточка лида с аргументацией скоринга и быстрыми ссылками `tel:` / `mailto:`.
- **Вкладка «Услуги»**:
  - Таблица услуг (`id` и название услуги) с автоматической нумерацией `id` (`1, 2, 3…`).
  - Поле ввода названия услуги и три операции: **Добавить**, **Редактировать**, **Удалить** (сохранение через `PUT /api/v1/admin-settings`).
- **Вкладка «Статистика»**:
  - Сводка по заявкам: общее количество, распределение по ролям, продуктам и дням, среднее время и последние заявки.
  - Кнопка **«Хитмап и время»** открывает окно со средним/максимальным временем визитов за день/неделю/месяц и 2D-хитмапом позиций курсора по данным `/api/behavior-metrics/`.

---

## API и разграничение доступа

Все ответы возвращаются в конверте `{ "data": ..., "error": ..., "message": "..." }`.  
Через внешний порт `:80` Nginx пропускает только разрешённые маршруты и HTTP-методы:

| Метод | Путь | Назначение | Auth |
|---|---|---|---|
| `GET` | `/api/v1/health` | Проверка доступности backend и БД | нет |
| `GET` | `/api/v1/admin-settings` | Получение услуг и границ бюджета | нет |
| `POST` / `PUT` / `DELETE` | `/api/v1/admin-settings` | Управление услугами и бюджетом | JWT |
| `POST` | `/api/v1/leads` | Отправка анкеты клиента | нет |
| `GET` | `/api/v1/leads` | Список заявок (без скоринга) | JWT |
| `GET` / `PUT` / `DELETE` | `/api/v1/leads/{id}` | Операции над конкретной заявкой | JWT |
| `GET` | `/api/applications/` | Очередь заявок со скорингом (`?skip=&limit=`) | JWT |
| `GET` | `/api/applications/{id}` | Одна заявка со скорингом | JWT |
| `POST` | `/api/v1/behavior` | Сохранение метрик при отправке заявки | нет |
| `POST` | `/api/behavior-metrics/` | Приём посекундных снимков метрик | нет |
| `GET` | `/api/behavior-metrics/` | Чтение снимков для хитмапа (`?skip=&limit=`) | JWT |
| `GET` | `/api/v1/auth/bootstrap-status` | Проверка, открыта ли регистрация | нет |
| `POST` | `/api/v1/auth/register` | Создание первого администратора | нет* |
| `POST` | `/api/v1/auth/login` | Вход по логину и паролю, выдача JWT | нет |
| `GET` | `/api/v1/auth/me` | Текущий администратор по JWT | JWT |
| `GET` | `/api/v1/stats` | Агрегированная статистика | JWT |

\* `register` возвращает `403`, если в таблице `admins` уже есть хотя бы одна запись.

---

## Тестирование и тестовые данные

Запуск модульных тестов backend (проверяют валидацию, скоринг, SQL-докстринги моделей и роутинг без БД):

```bash
docker run --rm --entrypoint python -u 0 \
  -v "$(pwd)/backend:/src:ro" -w /src -e PYTHONPATH=/src \
  -e JWT_SECRET=test-secret-test-secret-test-secret-12 \
  -e JWT_EXPIRE_MINUTES=60 \
  -e LEADS_APP_USER=leads_app \
  -e LEADS_APP_PASSWORD=changeme123 \
  -e POSTGRES_DB=leads \
  autello-barskiy-backend:latest -m unittest tests.test_payloads
```

Загрузка 10 тестовых заявок (4 горячих, 3 тёплых, 3 холодных) для проверки очереди:

```bash
docker compose exec -T postgres psql -U postgres -d leads < postgres/seed/10-test-leads.sql
```

---

## Сервисный профиль `tools` (pgAdmin и registry)

По умолчанию `pgadmin` и `registry` отключены. Если понадобится временно запустить pgAdmin локально на сервере:

```bash
docker compose --profile tools up -d pgadmin
```

И открыть SSH-туннель с локальной машины:

```powershell
ssh -i $env:USERPROFILE\.ssh\Bromum -N -L 15050:127.0.0.1:5050 root@185.182.110.184
```

После работы остановить сервисы профиля `tools`:

```bash
docker compose --profile tools stop pgadmin registry
```

---

## Подготовка к GitHub

В `.gitignore` исключены `.env`, `.env.*` (кроме `.env.example`), `certs/`, `registry/htpasswd`, `frontend/node_modules/`, `frontend/dist/`, `__pycache__/`, `.venv/`.

Перед публикацией убедитесь, что секреты и артефакты сборки не попали в индекс:

```bash
git status
```
