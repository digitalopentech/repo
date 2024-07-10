from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from dede.core import DedéOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

with DAG('convert_segments_dag', default_args=default_args, schedule_interval='@daily') as dag:
    start_task = DummyOperator(task_id='start_task')

    create_table_task = DedéOperator(
        task_id='create_table',
        job_name='ConvertSegmentsJob',
        params={
            'job_type': 'create_table',
            'table': 'your_table_name',
            'kafka_required_fields': [],
            'module': 'your_module',
            'domain': 'your_domain',
            'custom_schema_model_file': 'your_custom_schema_model_file',
            'custom_table_config_file': 'your_custom_table_config_file',
            'kafka_schemaregistry_topic': 'your_kafka_schemaregistry_topic',
        }
    )

    convert_segments_task = DedéOperator(
        task_id='convert_segments',
        job_name='ConvertSegmentsJob',
        params={
            'job_type': 'convert_segments',
            'table': 'your_table_name',
            'jar_path': 'your_jar_path',
        }
    )

    convert_all_segments_task = DedéOperator(
        task_id='convert_all_segments',
        job_name='ConvertSegmentsJob',
        params={
            'job_type': 'convert_all_segments',
            'jar_path': 'your_jar_path',
        }
    )

    start_task >> create_table_task >> convert_segments_task >> convert_all_segments_task
