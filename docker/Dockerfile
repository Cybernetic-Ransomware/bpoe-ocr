FROM python:3.12.7-alpine3.20 as builder

WORKDIR /src

RUN python -m pip install --upgrade pip --break-system-packages && \
    pip install uv --break-system-packages

COPY ./pyproject.toml ./uv.lock ./

RUN uv sync --frozen

FROM python:3.12.7-alpine3.20 as runtime
LABEL authors="aleksander.marszalki"
LABEL name="bpoe-api-gateway"

WORKDIR ./src

ENV PATH="/usr/local/bin:$PATH"

COPY --from=builder /usr/local /usr/local
COPY --from=builder /src /src

COPY ./src .

EXPOSE 8080/tcp

CMD ["tail", "-f", "/dev/null"]
#CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
