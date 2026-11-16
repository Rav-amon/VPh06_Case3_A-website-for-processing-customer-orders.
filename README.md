# Autéllo Barskiy

Контур сайта для заявок. Nginx принимает внешние запросы. PostgreSQL, pgAdmin и будущий backend остаются на этой машине. Образы backend публикуются в локальный реестр.

Каталог проекта: `/root/Autéllo_Barskiy`.

Имя проекта в Docker: `autello_barskiy`. Движок Docker принимает в именах сетей и томов только строчные латинские буквы, цифры, дефис и подчёркивание.

## Состав

| Сервис | Образ | Доступ |
|---|---|---|
| nginx | `nginx:1.28-alpine` | `80` сайт, `5000` реестр |
| postgres | `postgres:17-alpine` | только сеть `autello_barskiy_data` |
| pgadmin | `dpage/pgadmin4:9.10` | `127.0.0.1:5050` |
| registry | `registry:2` | через Nginx, порт `5000` |
| watchtower | `nickfedor/watchtower:1.24.0` | обновление образов раз в сутки |

Postgres в автоматическое обновление не входит.

Backend и frontend в `docker-compose.yml` оставлены комментарием. Их порты наружу не публикуются.

## Запуск

```bash
cd /root/Autéllo_Barskiy
cp .env.example .env
docker compose up -d
docker compose ps
```

Остановка контейнеров с сохранением данных:

```bash
docker compose down
```

Данные лежат в томах `autello_barskiy_postgres_data`, `autello_barskiy_pgadmin_data` и `autello_barskiy_registry_data`.

## Переменные

Рабочие значения хранятся в `.env`. Файл в GitHub не отправляется. Образец без паролей: `.env.example`.

| Переменная | Назначение |
|---|---|
| `POSTGRES_DB` | База заявок, по умолчанию `leads` |
| `POSTGRES_USER` | Администратор базы |
| `POSTGRES_PASSWORD` | Пароль администратора |
| `LEADS_APP_USER` | Роль будущего backend |
| `LEADS_APP_PASSWORD` | Пароль роли backend |
| `PGADMIN_DEFAULT_EMAIL` | Вход в pgAdmin |
| `PGADMIN_DEFAULT_PASSWORD` | Пароль pgAdmin |
| `REGISTRY_USER` | Логин `docker login` |
| `REGISTRY_PASSWORD` | Пароль реестра |
| `REGISTRY_HTTP_SECRET` | Внутренний секрет реестра |
| `REGISTRY_HOST` | Адрес сервера для клиентов |

Роль `ravil` создана в базе для pgAdmin. Её пароль совпадает с `POSTGRES_PASSWORD`.

## Проверка в браузере

Сайт:

```text
http://185.182.110.184
```

Реестр запрашивает логин из `REGISTRY_USER`:

```text
https://185.182.110.184:5000/v2/
```

pgAdmin открывается через туннель SSH. Окно с этой командой нужно оставить открытым:

```powershell
ssh -i $env:USERPROFILE\.ssh\Bromum -L 5050:127.0.0.1:5050 root@185.182.110.184
```

После этого в браузере: `http://127.0.0.1:5050`.

В списке серверов pgAdmin уже есть `leads-local`: хост `postgres`, порт `5432`, база `leads`, пользователь `ravil`.

## Реестр образов

Сертификат центра лежит в `certs/ca.crt`. Закрытые ключи лежат в `certs/` и в GitHub не отправляются. На Windows сертификат устанавливается в доверенные корневые центры, после чего Docker Desktop перезапускается.

```powershell
docker login 185.182.110.184:5000
docker tag autello-barskiy-backend:latest 185.182.110.184:5000/autello-barskiy-backend:latest
docker push 185.182.110.184:5000/autello-barskiy-backend:latest
```

## GitHub

Перед отправкой проверьте, что секреты не стоят в индексе:

```bash
git status
```

В репозиторий попадают compose-файл, конфигурация Nginx, скрипт роли базы, пример `.env.example` и этот README. Файл `.env`, каталог `certs/` и `registry/htpasswd` исключены через `.gitignore`.
