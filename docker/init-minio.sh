#!/bin/sh

/minio/minio server /data --console-address ":9001" &
sleep 5

mc alias set myminio http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

mc mb myminio/toocu

mc admin user add myminio reader reader123
mc admin policy set myminio readwrite-policy user=reader

mc admin user add myminio writer writer123
mc admin policy set myminio readwrite-policy user=writer
