from dede.core import Job
from concurrent.futures import ThreadPoolExecutor, wait
import tempfile
import subprocess
import logging
import integrations.s3 as s3_integration
import services.database as database_service
import services.descriptor as descriptor_service
import services.protobuf as protobuffer_service
import services.schema as schema_service
import services.state as state_service
from states.domains import TypeState, StateAlreadyRegisteredException
from params import CreateTableParams, ConvertSegmentsParquetParams
import sys
import traceback

class ConvertSegmentsJob(Job):
    def run(self):
        # Configurações do logger
        logger = logging.getLogger(__name__)
        logger.info("Starting conversion of segments to Parquet")

        def _save_state(table, type, msg):
            state_service.save(table, type, msg)
            if type == TypeState.ERROR:
                logger.error(msg)
            else:
                logger.info(msg)

        def create_table(payload: CreateTableParams):
            topic_name = payload.TABLE
            try:
                state_service.init(payload)
                file = protobuffer_service.create_from_schema_registry(payload.TABLE, payload.KAFKA_SCHEMREGISTRY_TOPIC)
                _save_state(topic_name, TypeState.RUNNING, msg=f"{topic_name}: Proto file created successfully.")
                descriptor_service.create_from_file(file)
                _save_state(topic_name, TypeState.RUNNING, msg=f"{topic_name}: Descriptor file created successfully.")
                ms, tc = schema_service.create_from_file(payload.DOMAIN, payload.MODULE, payload.TABLE, payload.CUSTOM_SCHEMA_MODEL_FILE)
                _save_state(topic_name, TypeState.RUNNING, msg=f"{topic_name}: Schema e table config created successfully.")
                database_service.create_from_configs(payload.DOMAIN, payload.TABLE, ms, tc)
                _save_state(topic_name, TypeState.SUCCESS, msg=f"{topic_name}: All steps executed successfully.")
            except StateAlreadyRegisteredException as sarex:
                logger.error(f"{topic_name}: {sarex} Exiting...")
                sys.exit(1)
            except Exception as ex:
                print(traceback.format_exc())
                _save_state(topic_name, TypeState.ERROR, msg=f"{topic_name}: {ex} Stopping...")
                sys.exit(1)

        def _convert_segments_parquet(table: str, jar_path: str):
            urls = database_service.get_completed_segments_urls(table)
            if not urls:
                logger.info(f"{table}: No segments completed. Stopping...")
                return

            with tempfile.TemporaryDirectory() as tmp_segments, tempfile.TemporaryDirectory() as tmp_parquets:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future_results = []
                    for url in urls:
                        file_path = f"{tmp_segments}/{url.split('/')[-1]}.gz"
                        future_results.append(executor.submit(s3_integration.download_file_from_s3, table, url, file_path))
                    wait(future_results)

                    # Executa comando Java para conversão
                    logger.info(f"{table}: Converting segments...")
                    optional_args = "--add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-exports=java.base/jdk.internal.ref=ALL-UNNAMED"
                    cmd = f"java {optional_args} -jar {jar_path} -dataDir={tmp_segments} -outputDir={tmp_parquets} -overwrite"
                    status, response_msg = subprocess.getstatusoutput(cmd)
                    if status != 0:
                        raise Exception(f"{response_msg} with status code {status} on create descriptor.")
                    logger.info(f"{table}: Segments converted.")

        def convert_all_tables_segments_parquet(payload: ConvertSegmentsParquetParams):
            try:
                tables = database_service.get_all_tables()
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [executor.submit(_convert_segments_parquet, table, payload.JAR_PATH) for table in tables]
                    wait(futures)
            except Exception as ex:
                print(traceback.format_exc())
                sys.exit(1)

        # Parâmetros de entrada
        job_type = self.params.get("job_type")
        if job_type == "create_table":
            create_table(self.params)
        elif job_type == "convert_segments":
            _convert_segments_parquet(self.params.get("table"), self.params.get("jar_path"))
        elif job_type == "convert_all_segments":
            convert_all_tables_segments_parquet(self.params)
