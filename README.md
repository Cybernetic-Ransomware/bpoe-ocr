# OCR for BPOE app
This repository contains an OCR application used to store temporary images, read receipts and write record propositions in database as a part of Be Part Of the Event application.

## Overview
The purpose of this project is to build an OCR microservice.

## Features
- S3 database integration,
- basic OCR via open source Python's libraries,
- modular use to future implementation of AI-based OCR models
- accessible only via a gateway connection,

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
      docker-compose -f ./docker/docker-compose.yml up --build
      ```
### Dev-instance   
1. Clone the repository:
      ```powershell
      git clone https://github.com/Cybernetic-Ransomware/bpoe-ocr.git
      ```
2. Set .env file based on the template.
3. Install UV:
      ```powershell
      pip install uv
      ```
4. Install dependencies:
      ```powershell
      uv sync
      ```
5. Run locally:
      ```powershell
      uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
      ```

## Testing
#### Postman
- The repository will include a Postman collection with ready-to-import webhook mockers

#### Pytest
```powershell
uv sync
uv run pytest
```

#### Ruff
- Ruff is included for linting. Run the tool with the command: `uvx ruff check`


## Useful links and documentation
- Will be described.
