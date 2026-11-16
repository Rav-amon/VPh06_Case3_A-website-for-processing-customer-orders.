#!/bin/sh
# Роль приложения: вход в базу заявок без прав суперпользователя.
set -eu

case "$LEADS_APP_USER" in
  *[!A-Za-z0-9_]*)
    echo "Недопустимое имя роли приложения" >&2
    exit 1
    ;;
esac

case "$LEADS_APP_PASSWORD" in
  *[!A-Za-z0-9]*)
    echo "Пароль роли приложения содержит недопустимые символы" >&2
    exit 1
    ;;
esac

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${LEADS_APP_USER}') THEN
    CREATE ROLE ${LEADS_APP_USER} LOGIN PASSWORD '${LEADS_APP_PASSWORD}'
      NOSUPERUSER NOCREATEDB NOCREATEROLE;
  END IF;
END
\$\$;

REVOKE ALL ON DATABASE ${POSTGRES_DB} FROM PUBLIC;
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${LEADS_APP_USER};
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO ${LEADS_APP_USER};
SQL
