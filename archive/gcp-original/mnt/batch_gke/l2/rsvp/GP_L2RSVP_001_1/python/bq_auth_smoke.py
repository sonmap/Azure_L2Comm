#!/usr/bin/env python3
"""Minimal check: Pod-mounted .oefj key and BigQuery query execution (no table needed)."""
import os
from google.oauth2 import service_account
from google.cloud import bigquery

project = os.getenv("BQ_JOB_PROJECT", "pjt-c-admin")
key_path = os.getenv("SA_KEY_PATH", "/home/jupyter/.oefj")
if not os.path.isfile(key_path):
    raise FileNotFoundError(f"Service Account key missing: {key_path}")
creds = service_account.Credentials.from_service_account_file(
    key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
client = bigquery.Client(project=project, credentials=creds)
rows = client.query("SELECT 'L2COMM' AS program_id, 'SUCCESS' AS result").result()
for row in rows:
    print(f"{row.program_id}: {row.result}")
