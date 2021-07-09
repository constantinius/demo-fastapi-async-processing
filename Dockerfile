FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install aioredis==2.0.0a1

COPY ./app /app/app