FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY royalemind /app/royalemind
COPY coach_static /app/coach_static
ENV PYTHONUNBUFFERED=1 ROYALEMIND_PUBLIC=1 ROYALEMIND_COACH_DATA=/tmp/royalemind-coach
EXPOSE 10000
CMD ["python","-m","royalemind.coach_web"]
