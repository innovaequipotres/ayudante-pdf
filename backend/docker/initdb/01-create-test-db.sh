#!/usr/bin/env bash
# Crea la base de test separada a partir de POSTGRES_DB.
#
# Los scripts de /docker-entrypoint-initdb.d solo se ejecutan la primera vez
# que se inicializa el volumen. Si el volumen ya existía, este script no corre;
# creá la base a mano con:
#
#   docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
#     -c "CREATE DATABASE \"${POSTGRES_DB}_test\" OWNER \"$POSTGRES_USER\";"'
#
# El entrypoint puede ejecutar este archivo con source, así que no se usa -u.
set -e

psql -v ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  -c "CREATE DATABASE \"${POSTGRES_DB}_test\" OWNER \"$POSTGRES_USER\";"
