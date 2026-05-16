FROM python:3.13-slim

RUN useradd django

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements/ requirements/

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    gettext

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements/local.txt

WORKDIR /app

RUN chown django:django /app

COPY --chown=django:django . .

USER django

RUN python manage.py collectstatic --noinput --clear

CMD ["sh", "-c", "set -xe; python manage.py migrate --noinput && python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000"]
