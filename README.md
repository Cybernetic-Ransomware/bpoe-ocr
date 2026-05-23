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
- Python 3.14+ with UV package manager
- Docker Desktop / Docker + Compose
- [just](https://github.com/casey/just) task runner (optional, but recommended)

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

#### just (recommended)
Common tasks are available via the `just` task runner:
```powershell
just test              # unit tests
just test-integration  # integration tests (requires Docker)
just lint              # ruff + ty + codespell + bandit
just format            # ruff format
just up / just down    # Docker stack
```

#### Pytest
```powershell
uv sync
uv run pytest
```

#### Ruff + ty
```powershell
uv sync
uv run ruff check src/
uv run ty check src/
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

## TODO / Known limitations

- **Orphaned Mongo records after S3 delete failure** — when `process_ocr` succeeds but the subsequent S3 cleanup fails, the Mongo record is retained and the file remains in the bucket. A scheduled cleanup job (or a TTL index on the collection) should identify and remove records whose corresponding S3 objects no longer exist, or vice versa.
- **Readiness probe** — `GET /healthz` is a liveness check only (process is alive). A `/readyz` endpoint performing lightweight Mongo + S3 pings is needed for orchestrators to distinguish a live-but-not-ready container from a healthy one.
- **Inter-service authorization** — endpoints are currently accessible to any caller that can reach the service. Requests from the API gateway should be authenticated (e.g. shared secret header, mTLS, or a service token) to prevent unauthorized access to OCR and storage operations.

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
