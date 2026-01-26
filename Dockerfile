FROM python:3.12-slim AS builder

WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --only main --no-interaction --no-ansi

FROM gcr.io/distroless/python3-debian12

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ /app/src/

ENV PYTHONPATH="/app:/app/.venv/lib/python3.12/site-packages"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/usr/bin/python3", "-m", "src.adapters.ucp_firewall"]
