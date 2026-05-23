# OCR for BPOE app
This repository contains an OCR application used to store temporary images, read receipts and write record propositions in database as a part of Be Part Of the Event application.

## Overview
The purpose of this project is to build an OCR microservice.

## Features
- S3 database integration,
- basic OCR via open source Python's libraries,
- modular use to future implementation of AI-based OCR models,
- MongoDB cluster for data persistence,
- accessible only via a gateway connection.

## Requirements
- Python 3.13.2 with UV package manager
- Docker Desktop / Docker + Compose

## Getting Started (Windows)
### Deploy
1. Clone the repository:
      ```powershell
      git clone https://github.com/Cybernetic-Ransomware/bpoe-ocr.git
      ```
2. Set .env file based on the template.
3. Run using Docker:
      ```powershell
      docker-compose -f .\docker\docker-compose.yml up --build -d
      ```
### Dev-instance
1. Clone the repository:
      ```powershell
      git clone https://github.com/Cybernetic-Ransomware/bpoe-ocr.git
      ```
2. Set .env file based on the template.
3. Create a directory: `/temp/minio_data`
4. Provide access to a MiniO/S3 instance with a bucket and writer/reader users that match the [.env.template](docker/.env.template) file.
   - *writer* should have both polices: *readwrite* and *writeonly*
5. Provide access to a Mongodb instance that match the [.env.template](docker/.env.template) file.
6. Install UV:
      ```powershell
      pip install uv
      ```
7. Install dependencies:
      ```powershell
      uv sync
      ```
8. Install pre-commit hooks:
      ```powershell
      uv run pre-commit install
      uv run pre-commit autoupdate
      uv run pre-commit run --all-files
      ```
9. Run the application locally:
      ```powershell
      uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
      ```

## Testing
#### Postman
- The repository will include a Postman collection with ready-to-import webhook mockers

#### Pytest
```powershell
uv sync --extra dev
uv run pytest
```

#### Ruff
```powershell
uv sync --extra dev
uv run ruff check
```
or as a standalone tool:
```powershell
uvx ruff check
```

#### Mypy
```powershell
uv sync --extra dev
uv run mypy .\src\
```
or as a standalone tool:
```powershell
uvx mypy .\src\
```

#### Quick MiniIO Instance:
```powershell
docker run -p 9000:9000 -p 9001:9001 \
quay.io/minio/minio server /data --console-address ":9001"
```
- mounted by default on WSL, e.g. `docker-desktop ` -> `/var/lib/docker/volumes/minio_minio_data/_data`

#### Database Access:
To connect to the MongoDB cluster with MongoDB Compass:
1. Open MongoDB Compass
2. Use the connection string, by default: `mongodb://localhost:27017/`
3. Click "Connect"

To verify if sharding is enabled for a collection:
1. Open the MongoDB Shell in Compass and check the sharding status:
   ```bash
   sh.status()
   ```
2. Look for information about a sharded collection, for example:
   ```bash
   sh.shardCollection("ocr.ocr_images", { _id: 1 })
   ```
3. If the collections section is empty, the collection is not sharded yet:
   ```bash
   "ocr": {
   primary: 'rs-shard02',
   collections: {}
   }
   ```
4. To enable sharding, run the following commands:
   ```bash
   sh.enableSharding("ocr")
   sh.shardCollection("ocr.ocr_images", { _id: 1 })
   ```

## Useful links and documentation
- Boto3 examples: [Amazon doc](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html)
- MiniIO docker image: [DockerHub](https://hub.docker.com/r/minio/minio)
- AsyncBoto3 for further refactorings: [PyPi](https://pypi.org/project/aioboto3/)
- Pytesseract configs: [pyimagesearch](https://pyimagesearch.com/2021/11/15/tesseract-page-segmentation-modes-psms-explained-how-to-improve-your-ocr-accuracy/)
- Mongo Compass winget command [winget](https://winget.run/pkg/MongoDB/Compass.Full)
---
- API Gateway microservice: [GitHub](https://github.com/Cybernetic-Ransomware/bpoe-api-gateway.git)
- Databases handler microservice: [GitHub](https://github.com/Cybernetic-Ransomware/bpoe_events_db_handler)
- OCR microservice: [GitHub](https://github.com/Cybernetic-Ransomware/bpoe-ocr)
- Reports microservice: [GitHub](https://github.com/Cybernetic-Ransomware/bpoe_events_reports)
