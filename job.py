import logging
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, wait

from services import descriptor_service, proto_buffer_service, schema_service, database_service, state_service
from integrations import s3 as s3_integration

logger = logging.getLogger(__name__)

class ConvertSegmentsParquet:
    def __init__(self, table, jar_path):
        self.table = table
        self.jar_path = jar_path

    def get_completed_segments_urls(self):
        return database_service.get_completed_segments_urls(self.table)

    def download_from_s3(self, url):
        with tempfile.TemporaryDirectory() as tmp_segments, tempfile.TemporaryDirectory() as tmp_parquets:
            future_results = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                for url in urls:
                    file_path = f"{tmp_segments}/{url.split('/')[-1]}.gz"
                    future_results.append(executor.submit(s3_integration.download_from_s3_path, self.table, url, file_path))
                wait(future_results)

                command = f"java -jar {self.jar_path} -dataDir={tmp_segments} -outputDir={tmp_parquets} -overwrite"
                status, response_msg = subprocess.getstatusoutput(command)
                if status != 0:
                    raise Exception(f"{response_msg} with status code {status} on create descriptor.")
                logger.info(f"{self.table}: segments converted.")

class CreateTable:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        try:
            state_service.init(self.payload)
            file = proto_buffer_service.create_from_schema_registry(self.payload.TABLE, self.payload.KAFKA_SCHEMREGISTRY_TOPIC)
            state_service.save_state(self.payload.TABLE, TypeState.RUNNING, msg=f"{self.payload.TABLE}: Proto file created successfully.")

            descriptor_service.create_from_file(file)
            state_service.save_state(self.payload.TABLE, TypeState.RUNNING, msg=f"{self.payload.TABLE}: Descriptor file created successfully.")

            ms, tc = schema_service.create_from_file(self.payload.DOMAIN, self.payload.MODULE, self.payload.TABLE, file, self.payload.CUSTOM_SCHEMA_MODEL_FILE)
            state_service.save_state(self.payload.TABLE, TypeState.RUNNING, msg=f"{self.payload.TABLE}: Schema e table config created successfully.")

            database_service.create_from_configs(self.payload.DOMAIN, self.payload.TABLE, ms, tc)
            state_service.save_state(self.payload.TABLE, TypeState.SUCCESS, msg=f"{self.payload.TABLE}: All steps executed successfully.")
        except StateAlreadyRegisteredException as sarex:
            logger.error(f"{self.payload.TABLE}: {sarex} Exiting...")
            sys.exit(1)
        except Exception as ex:
            print(traceback.format_exc())
            state_service.save_state(self.payload.TABLE, TypeState.ERROR, msg=f"{self.payload.TABLE}: {ex} Stopping...")
            sys.exit(1)

def convert_all_tables_segments_parquet(payload):
    try:
        tables = database_service.get_all_tables()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(ConvertSegmentsParquet(table, payload.JAR_PATH).download_from_s3) for table in tables]
            wait(futures)
    except Exception as ex:
        print(traceback.format_exc())
        sys.exit(1)
