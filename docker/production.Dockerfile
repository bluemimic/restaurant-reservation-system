FROM python:3.14-slim

RUN useradd django

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements/ requirements/

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    gettext

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/base.txt

WORKDIR /app

RUN chown django:django /app

COPY --chown=django:django . .

USER django

RUN python manage.py collectstatic --noinput --clear

CMD ["sh", "-c", "set -xe; python manage.py migrate --noinput; gunicorn config.wsgi:application --bind 0.0.0.0:8000"]