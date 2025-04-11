FROM python:3.12.10-alpine3.21 AS builder

WORKDIR /src

RUN echo "http://dl-cdn.alpinelinux.org/alpine/v$(cut -d'.' -f1-2 /etc/alpine-release)/community" >> /etc/apk/repositories && \
    apk update

RUN apk add --no-cache build-base cmake ninja

RUN apk add --no-cache \
    nasm \
    zlib-dev \
    libjpeg-turbo-dev \
    libpng-dev \
    libavif-dev \
    tiff-dev \
    openjpeg-dev \
    libwebp-dev \
    openblas-dev \
    gtk+3.0-dev \
    ffmpeg-dev \
    gstreamer-dev \
    gst-plugins-base-dev

RUN python -m pip install --upgrade pip --break-system-packages && \
    pip install uv --break-system-packages

COPY ./pyproject.toml ./uv.lock ./

RUN uv sync --no-cache --no-group dev


FROM python:3.12.10-alpine3.21 AS runtime
LABEL authors="aleksander.marszalki"
LABEL name="bpoe-api-gateway"

RUN apk add --no-cache \
    tesseract-ocr \
    tesseract-ocr-data-pol \
    tesseract-ocr-data-osd \
    zlib \
    libjpeg-turbo \
    libpng \
    libavif \
    tiff \
    openjpeg \
    libwebp \
    openblas \
    gtk+3.0 \
    ffmpeg \
    gstreamer \
    gst-plugins-base

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

ENV PATH="/usr/local/bin:$PATH"
#ENV PATH="/src/.venv/bin:/usr/local/bin:$PATH"

WORKDIR /src

#COPY --from=builder /usr/local /usr/local
#COPY --from=builder /src /src
#COPY --from=builder /src/.venv /src/.venv

#COPY ./src .

COPY --chown=appuser:appgroup ./src .
COPY --from=builder --chown=appuser:appgroup /src/.venv /src/.venv
RUN chmod -R +x /src/.venv/bin/

RUN ls -la /src && ls -la /src/.venv || echo ".venv nie istnieje"

USER appuser

EXPOSE 8080/tcp

CMD ["tail", "-f", "/dev/null"]
#CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
