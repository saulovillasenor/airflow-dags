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

def ingest_data_from_gcs():
    """read data from an GCS bucket.
    """
    gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
    psql_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    
    file = gcs_hook.download(bucket_name=GCS_BUCKET_NAME,
                             object_name="user_purchase.csv",
    )
    
    #reading and checking the file
    df = pd.read_csv(io.StringIO(file.decode('utf-8')))
    print(df.info(), '\n\n') 
    print(df.head(), '\n\n') 
    print(f'The shape of the df is: {df.shape}', '\n\n')

    #transforming data into a readable format for Postgres
    df['CustomerID'] = df['CustomerID'].fillna(0.0).astype(int)
    df['CustomerID'] = df['CustomerID'].replace(to_replace =0, value =r'\N')
    df['Description'] = df['Description'].str.replace(',','')
    
    #reading and checking the file again
    print('A total of ', len(df[df['CustomerID'] == r'\N']), ' values were filled in the CustomerID table \n\n')
    print(df.info(), '\n\n') 
    print(df.head(), '\n\n') 
    print(f'The shape of the df is: {df.shape}')
    
    #saving the file
    df.to_csv('user_purchase.csv', sep='\t', na_rep=r'\N', header=False, index=False)
    
    #loading the file to Postgres
    psql_hook.bulk_load(table=POSTGRES_TABLE_NAME, tmp_file='user_purchase.csv')
        
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
    
    create_table_entity = PostgresOperator(
        task_id="create_table_entity",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"""
            CREATE SCHEMA IF NOT EXISTS capstone_project;
            CREATE TABLE IF NOT EXISTS {POSTGRES_TABLE_NAME} (
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
    
    clear_table = PostgresOperator(
        task_id="clear_table",
        postgres_conn_id=POSTGRES_CONN_ID,
        sql=f"DELETE FROM {POSTGRES_TABLE_NAME}",
    )
    continue_process = DummyOperator(task_id="continue_process")
    
    ingest_data = PythonOperator(
        task_id="ingest_data",
        python_callable=ingest_data_from_gcs,
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )
    
    validate_data = BranchSQLOperator(
        task_id="validate_data",
        conn_id=POSTGRES_CONN_ID,
        sql=f"SELECT COUNT(*) AS total_rows FROM {POSTGRES_TABLE_NAME}",
        follow_task_ids_if_false=[continue_process.task_id],
        follow_task_ids_if_true=[clear_table.task_id],
    )
    
    end_workflow = DummyOperator(task_id="end_workflow")
    
    (
        start_workflow
        >> [verify_key_existence_1, verify_key_existence_2, verify_key_existence_3]
        >> create_table_entity
        >> validate_data
    )
    validate_data >> [clear_table, continue_process] >> ingest_data
    ingest_data >> end_workflow

    dag.doc_md = __doc__
