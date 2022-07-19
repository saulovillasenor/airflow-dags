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

with DAG(
    dag_id=DAG_ID,
    schedule_interval="@once",
    start_date=days_ago(1),
    tags=[CLOUD_PROVIDER, STABILITY_STATE],
) as dag:
    start_workflow = DummyOperator(task_id="start_workflow")
    validate = DummyOperator(task_id="validate")
    prepare = DummyOperator(task_id="prepare")
    load = DummyOperator(task_id="load")
    end_workflow = DummyOperator(task_id="end_workflow")
    
    start_workflow >> validate >> prepare >> load >> end_workflow
