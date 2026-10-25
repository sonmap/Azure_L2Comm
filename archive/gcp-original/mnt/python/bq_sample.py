#!/usr/bin/env python3
import os

from google.cloud import bigquery
from google.oauth2 import service_account

JOB_PROJECT = os.getenv("BQ_JOB_PROJECT", "gcp-prod-edp-edge-509423")
TABLE = os.getenv(
    "BQ_SAMPLE_TABLE",
    "pjt-c-admin.dlk_sample.gcp_region_inventory",
)
LIMIT = int(os.getenv("BQ_SAMPLE_LIMIT", "10"))
SA_KEY_PATH = os.getenv("SA_KEY_PATH", "/home/jupyter/.oefj")


def main() -> None:
    if not os.path.isfile(SA_KEY_PATH):
        raise FileNotFoundError(f"Service Account Key not found: {SA_KEY_PATH}")
    credentials = service_account.Credentials.from_service_account_file(
        SA_KEY_PATH, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    print(f"[INFO] Credential source     : {SA_KEY_PATH}")
    print(f"[INFO] Service account       : {credentials.service_account_email}")
    client = bigquery.Client(project=JOB_PROJECT, credentials=credentials)

    sql = f"""
    SELECT
      region_name,
      status,
      description,
      loaded_at
    FROM `{TABLE}`
    ORDER BY region_name
    LIMIT {LIMIT}
    """

    print(f"[INFO] BigQuery job project : {JOB_PROJECT}")
    print(f"[INFO] Sample table         : {TABLE}")
    print(f"[INFO] Limit                : {LIMIT}")
    print()

    rows = list(client.query(sql).result())

    print(f"[INFO] rows={len(rows)}")
    for row in rows:
        print(
            f"{row.region_name}\t"
            f"{row.status}\t"
            f"{row.description}\t"
            f"{row.loaded_at}"
        )


if __name__ == "__main__":
    main()
