#!/bin/bash
set -e

mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

mc admin user add local "$MINIO_READER_ACCESS_KEY" "$MINIO_READER_SECRET_KEY" || true
mc admin policy attach local readonly --user "$MINIO_READER_ACCESS_KEY" || true

mc admin user add local "$MINIO_WRITER_ACCESS_KEY" "$MINIO_WRITER_SECRET_KEY" || true
mc admin policy attach local readwrite --user "$MINIO_WRITER_ACCESS_KEY" || true

mc mb --ignore-existing "local/$MINIO_BUCKET_NAME"
