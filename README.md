# Autéllo Barskiy

Закрытый контур приёма заявок для «тёплых клиентов».  
Снаружи открыт только **Nginx** (`:80` сайт и узкий вход `/api/`, `:5000` локальный реестр образов).  
**PostgreSQL**, **pgAdmin** и **FastAPI backend** остаются внутри машины и наружу не публикуются.

## Структура проекта

```text
Autéllo_Barskiy/
├── backend/                 # Приватный FastAPI + asyncpg сервис
│   ├── app/
│   │   ├── core/            # Конфигурация, пул PostgreSQL, схема БД, ошибки, логи
│   │   ├── models/          # SQL-модели в докстрингах + CRUD-классы
│   │   ├── routes/          # Роуты FastAPI и общий api_router
│   │   └── main.py          # Точка входа (/api/v1)
│   ├── tests/               # Модульные тесты без БД
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── api/             # Клиент к /api/v1/*
│   │   ├── components/      # Форма заявки, ползунок бюджета, фоновые сферы
│   │   ├── hooks/           # Сбор поведенческих метрик
│   │   ├── pages/           # Главная страница
│   │   ├── types/           # Типы API и формы
│   │   └── utils/           # Zod-валидация и форматирование
│   ├── index.html
│   └── package.json
├── nginx/
│   ├── nginx.conf           # Глобальные настройки и rate limit
│   ├── conf.d/
│   │   ├── site.conf        # Публичный вход :80 (статика dist + разрешённые /api/)
│   │   ├── backend-proxy.inc
│   │   └── registry.conf    # TLS-прокси локального реестра :5000
│   └── html/                # Резервная заглушка
├── pgadmin/
│   └── servers.json         # Преднастроенное подключение leads-local
├── postgres/
│   └── init/
│       └── 01-app-role.sh   # Создание роли приложения LEADS_APP_USER
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Архитектура и сеть

| Сервис | Образ | Сети Docker | Доступ |
|---|---|---|---|
| `nginx` | `nginx:1.28-alpine` | `edge`, `app`, `registry_net` | `:80` (сайт), `:5000` (реестр) |
| `frontend` | статика `frontend/dist` | — | монтируется в `nginx` (`:ro`) |
| `backend` | `autello-barskiy-backend:latest` | `app`, `data` (`internal`) | без публикации портов (`8000/tcp` внутри) |
| `postgres` | `postgres:17-alpine` | `data` (`internal`) | без публикации портов (`5432/tcp` внутри) |
| `pgadmin` | `dpage/pgadmin4:9.10` | `data`, `admin` | только `127.0.0.1:5050` |
| `registry` | `registry:2` | `registry_net` (`internal`) | через `nginx:5000` |
| `watchtower` | `nickfedor/watchtower:1.24.0` | `host` | обновление помеченных образов раз в сутки |

`postgres` и `backend` исключены из автообновления Watchtower (`com.centurylinklabs.watchtower.enable=false`).

## Переменные окружения

Рабочие секреты хранятся в `.env` (в GitHub не попадает). Образец: `.env.example`.

| Переменная | Назначение |
|---|---|
| `POSTGRES_DB` | Имя базы заявок (по умолчанию `leads`) |
| `POSTGRES_USER` | Суперпользователь Postgres |
| `POSTGRES_PASSWORD` | Пароль администратора и роли `ravil` |
| `LEADS_APP_USER` | Ограниченная роль для backend |
| `LEADS_APP_PASSWORD` | Пароль роли backend |
| `PGADMIN_DEFAULT_EMAIL` | Логин в pgAdmin |
| `PGADMIN_DEFAULT_PASSWORD` | Пароль в pgAdmin |
| `REGISTRY_USER` | Логин `docker login` |
| `REGISTRY_PASSWORD` | Пароль реестра |
| `REGISTRY_HTTP_SECRET` | Секрет реестра |
| `REGISTRY_HOST` | Хост реестра для клиентов |

## Сборка и запуск

Имя проекта в Docker: `autello_barskiy`. Перед запуском Nginx должен существовать каталог `frontend/dist`.

### 1. Сборка фронтенда

```bash
cd frontend
npm install
npm run build
```

*(Если Node.js установлен локально в `~/.local/node/bin`, добавьте его в `PATH`: `export PATH="$HOME/.local/node/bin:$PATH"`.)*

### 2. Настройка `.env` и запуск контейнеров

```bash
cp .env.example .env
# заполните пароли и секреты в .env

docker compose build backend
docker compose up -d
docker compose ps
```

### 3. Обновление после правок

Обновить фронтенд:

```bash
cd frontend && npm run build && cd ..
docker compose up -d nginx
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

## Модели данных (PostgreSQL)

SQL создания каждой таблицы хранится в докстринге соответствующего класса в `backend/app/models/` и автоматически применяется при старте приложения:

1. **`Lead` (`leads`)** — анкета «тёплого клиента»: ФИО, телефон/почта (обязательно хотя бы одно), информация о бизнесе, ниша, размер компании, размер бизнеса, объём, объём потребности, задачи, роль (`сотрудник` / `руководитель`), срок, тип задачи, интересующий продукт, бюджет (строкой с ползунка), способ связи, удобное время, комментарий.
2. **`LeadBehavior` (`lead_behavior`)** — метрики поведения на странице (`lead_id` как `PRIMARY KEY REFERENCES leads(id) ON DELETE CASCADE`, связь `1:1`): время на странице, клики кнопок, точки задержки курсора, количество возвратов и технические параметры браузера.
3. **`AdminSettings` (`admin_settings`)** — единственная строка настроек (`id = 1`): список услуг (`code`, `title`, `description`, `price_min`, `price_max`, `is_active`) и границы ползунка (`budget_min`, `budget_max`, `budget_step`).

## API и разграничение доступа

Все ответы приходят в формате `{ "data": ..., "error": ..., "message": "..." }`.

Через внешний порт `:80` Nginx пропускает **только** маршруты, необходимые форме на сайте:

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/api/v1/health` | Проверка доступности backend и БД |
| `GET` | `/api/v1/admin-settings` | Получение услуг и границ бюджета |
| `POST` | `/api/v1/leads` | Отправка анкеты клиента |
| `POST` | `/api/v1/behavior` | Отправка поведенческих метрик для заявки |

Полный CRUD (`GET` списков/записей, `PUT`, `DELETE`, включая управление услугами в `/api/v1/admin-settings`) доступен только внутри сети Docker на `backend:8000` (для администрирования с самой машины):

```bash
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/leads').read().decode())"
```

## Тестирование backend

Модульные тесты проверяют валидацию анкеты, метрик, цен услуг, SQL-докстринги моделей и роутинг (без подключения к БД):

```bash
docker run --rm --entrypoint python -u 0 \
  -v "$(pwd)/backend:/src:ro" -w /src -e PYTHONPATH=/src \
  autello-barskiy-backend:latest -m unittest tests.test_payloads
```

## Доступ к pgAdmin

pgAdmin слушает только `127.0.0.1:5050` на сервере. С локальной машины откройте SSH-туннель (при занятом локальном `5050` используйте `15050`):

```powershell
ssh -i $env:USERPROFILE\.ssh\Bromum -N -L 15050:127.0.0.1:5050 root@185.182.110.184
```

Затем откройте в браузере `http://127.0.0.1:15050/` (сервер `leads-local`, база `leads`).

## Реестр образов

Сертификат центра лежит в `certs/ca.crt` (ключи из `certs/` в GitHub не отправляются). Для работы с локальным реестром на порту `:5000`:

```powershell
docker login 185.182.110.184:5000
docker tag autello-barskiy-backend:latest 185.182.110.184:5000/autello-barskiy-backend:latest
docker push 185.182.110.184:5000/autello-barskiy-backend:latest
```

## Подготовка к GitHub

В `.gitignore` исключены `.env`, `.env.*` (кроме `.env.example`), `certs/`, `registry/htpasswd`, `frontend/node_modules/`, `frontend/dist/`, `__pycache__/`, `.venv/`.

Перед публикацией убедитесь, что секреты и артефакты сборки не попали в индекс:

```bash
git status
```
