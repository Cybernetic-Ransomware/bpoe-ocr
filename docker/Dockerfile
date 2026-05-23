FROM python:3.14-slim AS builder

WORKDIR /src

RUN pip install uv --break-system-packages

COPY ./pyproject.toml ./uv.lock ./

ENV UV_PYTHON_PREFERENCE=only-system
RUN uv sync --no-cache --no-group dev


FROM python:3.14-slim AS runtime
LABEL authors="aleksander.marszalki"
LABEL name="bpoe-ocr"

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-pol \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

ENV PATH="/src/.venv/bin:/usr/local/bin:$PATH"

WORKDIR /src

COPY --chown=appuser:appgroup ./src .
COPY --from=builder --chown=appuser:appgroup /src/.venv /src/.venv
RUN chmod -R +x /src/.venv/bin/

RUN mkdir /log && chown appuser:appgroup /log

USER appuser

EXPOSE 8080/tcp

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]