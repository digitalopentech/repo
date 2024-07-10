from interaflow.dags.inter_dag import InterDag
from interaflow.operator.inter import DedeSparkOperator, DedePythonOperator

dag_args = {
    'owner': 'data-team',
    'start_date': datetime(2023, 1, 1),
    'retries': 3,
}

custom_args = {
    'env': 'prd',
    'env_upper': 'PRD',
    'account': '81212',
    'region': 'sa-east-1',
    'kafka_url': 'kafka://broker:9092',
    'instance': 'instance_name',
    'reference_date': '{{ ds }}',
}

with InterDag(
    dag_id='convert_segments_job',
    description='Convert segments and create table',
    schedule_interval='0 0 * * *',
    default_args=dag_args,
    custom_args=custom_args,
    max_active_tasks=4,
    max_active_runs=1,
    catchup=False
) as dag:
    
    convert_segments_task = DedeSparkOperator(
        task_id='convert_segments_parquet',
        job_name='convert_segments_parquet',
        resource_size='MEDIUM',
        num_executors=3,
        custom_args=custom_args,
        spark_conf=SPARK_CONFIGS,
        dede_version='0.16.5'
    )

    create_table_task = DedePythonOperator(
        task_id='create_table',
        script='create_table.py',
        parameters={
            'TABLE': 'table_name',
            'KAFKA_REQUIRED_FIELDS': ['field1', 'field2'],
            'MODULE': 'module_name',
            'DOMAIN': 'domain_name',
            'CUSTOM_SCHEMA_MODEL_FILE': '/path/to/schema/model',
            'CUSTOM_TABLE_CONFIG_FILE': '/path/to/table/config',
            'KAFKA_SCHEMREGISTRY_TOPIC': 'kafka_topic'
        },
    )

    convert_segments_task >> create_table_task
