"""Database Ingestion Workflow
Author: Enrique Olivares <enrique.olivares@wizeline.com>
Forked by: Saulo Villaseñor
Description: Ingests the data from a GCS bucket into a postgres table.
"""

from airflow.models import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.sql import BranchSQLOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
import pandas as pd
import io

# General constants
DAG_ID = "gcs_to_postgres_ingestion_workflow"
STABILITY_STATE = "unstable"
CLOUD_PROVIDER = "gcp"

# GCP constants
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "wizeline-project-bucket"

# Postgres constants
POSTGRES_CONN_ID = "ml_conn"
POSTGRES_TABLE_NAME = "capstone_project.user_purchase"

def read_data_from_gcs():
    """read data from an GCS bucket.
    """
    gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
    file = gcs_hook.download(bucket_name=GCS_BUCKET_NAME,
                             object_name="user_purchase.csv",
    )
    df = pd.read_csv(io.StringIO(file.decode('utf-8')))
    print(df.head())

with DAG(
    dag_id=DAG_ID,
    schedule_interval="@once",
    start_date=days_ago(1),
    tags=[CLOUD_PROVIDER, STABILITY_STATE],
) as dag:
    
    start_workflow = DummyOperator(task_id="start_workflow")
    
    verify_key_existence_1 = GCSObjectExistenceSensor(
        task_id="verify_key_existence_1",
        google_cloud_conn_id=GCP_CONN_ID,
        bucket=GCS_BUCKET_NAME,
        object="user_purchase.csv",
    )    
    
    verify_key_existence_2 = GCSObjectExistenceSensor(
        task_id="verify_key_existence_2",
        google_cloud_conn_id=GCP_CONN_ID,
        bucket=GCS_BUCKET_NAME,
        object="movie_review.csv",
    )
    
    verify_key_existence_3 = GCSObjectExistenceSensor(
        task_id="verify_key_existence_3",
        google_cloud_conn_id=GCP_CONN_ID,
        bucket=GCS_BUCKET_NAME,
        object="log_reviews.csv",
    )
    
    read_data = PythonOperator(
        task_id="read_data",
        python_callable=read_data_from_gcs,
    )
    
    end_workflow = DummyOperator(task_id="end_workflow")
    
    (
        start_workflow 
        >> [verify_key_existence_1, verify_key_existence_2, verify_key_existence_3] 
        >> read_data >> end_workflow
    )

    dag.doc_md = __doc__
