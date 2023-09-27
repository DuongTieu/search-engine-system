#!/bin/sh

echo "Start run entrypoint script..."

echo "Start ingest data to elastic search..."
python elastic_ingest.py

echo "Run app with uvicorn server..."
uvicorn app:app --port 8000 --host 0.0.0.0