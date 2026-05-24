#!/bin/bash
set -e

: "${MINIO_ROOT_USER:?required}"
: "${MINIO_ROOT_PASSWORD:?required}"
: "${MINIO_READER_ACCESS_KEY:?required}"
: "${MINIO_READER_SECRET_KEY:?required}"
: "${MINIO_WRITER_ACCESS_KEY:?required}"
: "${MINIO_WRITER_SECRET_KEY:?required}"
: "${MINIO_BUCKET_NAME:?required}"

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

mc admin user info local "$MINIO_READER_ACCESS_KEY" >/dev/null 2>&1 \
    || mc admin user add local "$MINIO_READER_ACCESS_KEY" "$MINIO_READER_SECRET_KEY"
# || true: attaching an already-attached policy returns a non-zero exit code; desired state is already met
mc admin policy attach local readonly --user "$MINIO_READER_ACCESS_KEY" || true

mc admin user info local "$MINIO_WRITER_ACCESS_KEY" >/dev/null 2>&1 \
    || mc admin user add local "$MINIO_WRITER_ACCESS_KEY" "$MINIO_WRITER_SECRET_KEY"
mc admin policy attach local readwrite --user "$MINIO_WRITER_ACCESS_KEY" || true

mc mb --ignore-existing "local/$MINIO_BUCKET_NAME"