import concurrent.futures
import logging
import sys
import traceback
import tempfile
import subprocess

from integrations.s3 import s3_integration
from services import descriptor_service, protobuf_service, schema_service, database_service, state_service
from states.domains import TypeState, StateAlreadyRegisteredException
from params import ConvertSegmentsParquetParams, CreateTableParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _save_state(topic_name: str, state_type: TypeState, msg: str):
    """Save the current state with appropriate logging."""
    state_service.save(topic_name, state_type, msg)
    if state_type == TypeState.ERROR:
        logger.error(msg)
    else:
        logger.info(msg)

def _convert_segments_to_parquet(table: str, jar_path: str):
    """Convert database segments to Parquet format."""
    urls = database_service.get_completed_segments_urls(table)
    if not urls:
        logger.info(f"{table}: No completed segments found. Stopping...")
        return

    with tempfile.TemporaryDirectory() as tmp_segments, tempfile.TemporaryDirectory() as tmp_parquets:
        with ThreadPoolExecutor(max_workers=4) as executor:
            download_futures = [
                executor.submit(s3_integration.download_from_s3, url, f"{tmp_segments}/{url.split('/')[-1]}.gz")
                for url in urls
            ]
            concurrent.futures.wait(download_futures)

        logger.info(f"{table}: Converting segments to Parquet.")
        optional_args = "--add-exports=java.base/jdk.internal.ref=ALL-UNNAMED --add-exports=java.base/sun.nio.ch=ALL-UNNAMED"
        command = f"java {optional_args} -jar {jar_path} -dataDir={tmp_segments} -outputDir={tmp_parquets} -overwrite"
        status, response_msg = subprocess.getstatusoutput(command)

        if status > 0:
            raise Exception(f"{response_msg} with status code {status} on creating descriptor.")
        logger.info(f"{table}: Segments converted to Parquet.")
        # Placeholder for S3 upload logic

def convert_all_tables_to_parquet(payload: ConvertSegmentsParquetParams):
    """Convert segments of all tables to Parquet format."""
    try:
        tables = database_service.get_all_tables()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_convert_segments_to_parquet, table, payload.JAR_PATH): table for table in tables}
            concurrent.futures.wait(futures)
    except Exception as ex:
        logger.error("Error converting all tables to Parquet", exc_info=True)
        sys.exit(1)

def create_table(payload: CreateTableParams):
    """Create a table and its schema based on provided parameters."""
    topic_name = payload.TABLE
    try:
        descriptor_service.init(payload)
        proto_file = protobuf_service.create_from_schema_registry(payload.TABLE, payload.KAFKA_SCHEMAREGISTRY_TOPIC)
        _save_state(topic_name, TypeState.RUNNING, f"{topic_name}: Proto file created successfully.")

        descriptor_service.create_from_file(proto_file)
        _save_state(topic_name, TypeState.RUNNING, f"{topic_name}: Descriptor file created successfully.")

        ms, tc = schema_service.create_from_file(payload.DOMAIN, payload.MODULE, payload.TABLE, payload.CUSTOM_SCHEMA_MODEL_FILE)
        _save_state(topic_name, TypeState.RUNNING, f"{topic_name}: Schema & table config created successfully.")

        database_service.create_from_configs(payload.DOMAIN, payload.TABLE, ms, tc)
        _save_state(topic_name, TypeState.SUCCESS, f"{topic_name}: All steps executed successfully.")
    except StateAlreadyRegisteredException as sarex:
        logger.error(f"{topic_name}: {sarex} Exiting...")
        _save_state(topic_name, TypeState.ERROR, f"{topic_name}: {sarex} Stopping...")
        sys.exit(1)
    except Exception as ex:
        logger.error(f"{topic_name}: {ex} Stopping...", exc_info=True)
        _save_state(topic_name, TypeState.ERROR, f"{topic_name}: {ex} Stopping...")
        sys.exit(1)
