import concurrent.futures
import logging
import sys
import traceback
import tempfile
import subprocess

from integrations.s3 import s3_integration
from services import (
    descriptor_service, 
    protobuf_service, 
    schema_service, 
    database_service, 
    state_service
)
from states.domains import TypeState, StateAlreadyRegisteredException
from params import ConvertSegmentsParquetParams, CreateTableParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StateSaver:
    """Utility class to handle state saving and logging."""

    @staticmethod
    def save_state(topic_name: str, state_type: TypeState, msg: str):
        state_service.save(topic_name, state_type, msg)
        if state_type == TypeState.ERROR:
            logger.error(msg)
        else:
            logger.info(msg)

class SegmentConverter:
    """Class responsible for converting database segments to Parquet format."""

    def __init__(self, jar_path: str):
        self.jar_path = jar_path

    def convert(self, table: str):
        urls = database_service.get_completed_segments_urls(table)
        if not urls:
            logger.info(f"{table}: No completed segments found. Stopping...")
            return

        with tempfile.TemporaryDirectory() as tmp_segments, tempfile.TemporaryDirectory() as tmp_parquets:
            self._download_segments(urls, tmp_segments)
            self._convert_segments_to_parquet(table, tmp_segments, tmp_parquets)
            self._upload_parquets_to_s3(table, tmp_parquets)

    def _download_segments(self, urls, tmp_segments):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            download_futures = [
                executor.submit(s3_integration.download_from_s3, url, f"{tmp_segments}/{url.split('/')[-1]}.gz")
                for url in urls
            ]
            concurrent.futures.wait(download_futures)

    def _convert_segments_to_parquet(self, table, tmp_segments, tmp_parquets):
        logger.info(f"{table}: Converting segments to Parquet.")
        optional_args = "--add-exports=java.base/jdk.internal.ref=ALL-UNNAMED --add-exports=java.base/sun.nio.ch=ALL-UNNAMED"
        command = f"java {optional_args} -jar {self.jar_path} -dataDir={tmp_segments} -outputDir={tmp_parquets} -overwrite"
        status, response_msg = subprocess.getstatusoutput(command)

        if status > 0:
            raise Exception(f"{response_msg} with status code {status} on creating descriptor.")
        logger.info(f"{table}: Segments converted to Parquet.")

    def _upload_parquets_to_s3(self, table, tmp_parquets):
        logger.info(f"{table}: Uploading Parquet files to S3.")
        # Placeholder for S3 upload logic

def convert_all_tables_to_parquet(payload: ConvertSegmentsParquetParams):
    """Convert segments of all tables to Parquet format."""
    try:
        tables = database_service.get_all_tables()
        segment_converter = SegmentConverter(payload.JAR_PATH)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(segment_converter.convert, table) for table in tables]
            concurrent.futures.wait(futures)
    except Exception as ex:
        logger.error("Error converting all tables to Parquet", exc_info=True)
        sys.exit(1)

class TableCreator:
    """Class responsible for creating tables and their schemas."""

    def create_table(self, payload: CreateTableParams):
        topic_name = payload.TABLE
        try:
            descriptor_service.init(payload)
            proto_file = protobuf_service.create_from_schema_registry(payload.TABLE, payload.KAFKA_SCHEMAREGISTRY_TOPIC)
            StateSaver.save_state(topic_name, TypeState.RUNNING, f"{topic_name}: Proto file created successfully.")

            descriptor_service.create_from_file(proto_file)
            StateSaver.save_state(topic_name, TypeState.RUNNING, f"{topic_name}: Descriptor file created successfully.")

            ms, tc = schema_service.create_from_file(payload.DOMAIN, payload.MODULE, payload.TABLE, payload.CUSTOM_SCHEMA_MODEL_FILE)
            StateSaver.save_state(topic_name, TypeState.RUNNING, f"{topic_name}: Schema & table config created successfully.")

            database_service.create_from_configs(payload.DOMAIN, payload.TABLE, ms, tc)
            StateSaver.save_state(topic_name, TypeState.SUCCESS, f"{topic_name}: All steps executed successfully.")
        except StateAlreadyRegisteredException as sarex:
            logger.error(f"{topic_name}: {sarex} Exiting...")
            StateSaver.save_state(topic_name, TypeState.ERROR, f"{topic_name}: {sarex} Stopping...")
            sys.exit(1)
        except Exception as ex:
            logger.error(f"{topic_name}: {ex} Stopping...", exc_info=True)
            StateSaver.save_state(topic_name, TypeState.ERROR, f"{topic_name}: {ex} Stopping...")
            sys.exit(1)


from src.main import SegmentConverter, TableCreator, ConvertSegmentsParquetParams, CreateTableParams

def main():
    # Testando SegmentConverter
    jar_path = "/path/to/jar"
    segment_converter = SegmentConverter(jar_path)
    
    # Testar conversão de segmentos para uma tabela de exemplo
    try:
        segment_converter.convert('test_table')
        print("Segment conversion successful.")
    except Exception as e:
        print(f"Segment conversion failed: {e}")

    # Testando TableCreator
    table_creator = TableCreator()
    
    # Criar parâmetros de teste para criar uma tabela
    create_table_params = CreateTableParams(
        TABLE='test_table',
        DOMAIN='test_domain',
        MODULE='test_module',
        KAFKA_SCHEMAREGISTRY_TOPIC='test_topic',
        CUSTOM_SCHEMA_MODEL_FILE='schema_model_file'
    )

    # Testar criação de tabela
    try:
        table_creator.create_table(create_table_params)
        print("Table creation successful.")
    except Exception as e:
        print(f"Table creation failed: {e}")

if __name__ == "__main__":
    main()
