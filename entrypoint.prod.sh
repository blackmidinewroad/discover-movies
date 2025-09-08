#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Postgres is not running yet..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 1
    done

    echo "PostgreSQL is running"
fi

python manage.py migrate --noinput

exec "$@"