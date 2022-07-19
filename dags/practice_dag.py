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

# General constants
DAG_ID = "gcs_to_postgres_ingestion_workflow"
STABILITY_STATE = "unstable"
CLOUD_PROVIDER = "gcp"

# GCP constants
GCP_CONN_ID = "google_cloud_default"
GCS_BUCKET_NAME = "wizeline-project-bucket"
GCS_KEY_NAME = "user_purchase.csv"

# Postgres constants
POSTGRES_CONN_ID = "ml_conn"


with DAG(
    dag_id=DAG_ID,
    schedule_interval="@once",
    start_date=days_ago(1),
    tags=[CLOUD_PROVIDER, STABILITY_STATE],
) as dag:
    start_workflow = DummyOperator(task_id="start_workflow")
    
    
    validate = DummyOperator(task_id="validate")
    
    
    create_table_entity = PostgresOperator(
        task_id="create_table_entity",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"""
            CREATE SCHEMA IF NOT EXISTS capstone_project;
            CREATE TABLE IF NOT EXISTS capstone_project.user_purchase (
                invoice_number varchar(10),
                stock_code varchar(20),
                detail varchar(1000),
                quantity int,
                invoice_date timestamp,
                unit_price numeric(8,3),
                customer_id int,
                country varchar(20)
            )
        """,
    )
    
    
    load = DummyOperator(task_id="load")
    
    
    end_workflow = DummyOperator(task_id="end_workflow")
    
    start_workflow >> validate >> create_table_entity >> load >> end_workflow
