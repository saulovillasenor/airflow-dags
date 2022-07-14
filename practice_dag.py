#Steps for creating a DAG in Airflow

#Step 1. Import the modules
from datetime import timedelta
from airflow import DAG
from airflow.providers.google.cloud.operators.gcs import GCSListObjectsOperator

#Step 2. Set the default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2022, 7, 6),
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

#Step 3. Instantiate a DAG
dag = DAG(
    'gcs_dag',
    default_args=default_args,
    description='DAG to check the files in GCS',
    schedule_interval=timedelta(days=1),
)

#Step 4. Tasks creation
gcs_files = GCSListObjectsOperator(
                task_id='gcs_files',
                bucket='data',
                delimiter='.csv',
                gcp_conn_id=google_cloud_conn_id,
                dag=dag
            )

gcs_files

#Step 5. Set up the dependencies
#In this case we have no depencies since our DAG only has 1 task, but an example of this would be:
#task1 >> task2 >> [task3, task4, task5] >> task6
#where the task within thw list would run in parallel  