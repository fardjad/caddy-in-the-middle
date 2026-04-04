FROM python:3-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen

COPY app.py /app/app.py

EXPOSE 8080

CMD ["uv", "run", "opentelemetry-instrument", "python", "/app/app.py"]