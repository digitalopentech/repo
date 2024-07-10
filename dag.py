from datetime import datetime
from interairflow.dags.inter_dag import InterDag
from airflow.operators.dummy import DummyOperator
from interairflow.operator.dede import DedeSparkOperator

PROJECT_NAME = "convert_segments_project"
INSTANCE = "prod"

dag_args = {
    "owner": "data-engineering",
    "start_date": datetime(2023, 1, 1),
    "retries": 3,
}

custom_args = {
    "env": "prd",
    "table": "example_table",
    "jar_path": "/path/to/jarfile.jar",
}

with InterDag(
    dag_id=PROJECT_NAME,
    description="Convert segments to Parquet",
    domain="DATA",
    schedule_interval="0 * * * *",
    default_args=dag_args,
    sns_target_arn="arn:aws:sns:region:account:topic",
    max_active_tasks=4,
    max_active_runs=1,
    catchup=False,
    tags=["data", "conversion"],
) as dag:
    start_task = DummyOperator(task_id="start_task")

    convert_segments = DedeSparkOperator(
        task_id="convert_segments",
        job_name=f"{PROJECT_NAME}.convert_segments",
        resource_size="MEDIUM",
        num_executors=4,
        retries=3,
        dynamic_allocation=False,
        custom_args=custom_args,
        spark_configs={"spark.sql.sources.partitionOverwriteMode": "dynamic"},
        dede_version="0.16.5"
    )

    start_task >> convert_segments
