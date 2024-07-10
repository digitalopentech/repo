from dede.core import Job
from concurrent.futures import ThreadPoolExecutor, wait
import tempfile
import subprocess
import logging
import integrations.s3 as s3_integration
import services.database as database_service

class ConvertSegmentsJob(Job):
    def run(self):
        # Configurações do logger
        logger = logging.getLogger(__name__)
        logger.info("Starting conversion of segments to Parquet")

        # Parâmetros de entrada
        table = self.params.get("table")
        jar_path = self.params.get("jar_path")

        # Função para converter segmentos
        def _convert_segments_parquet(table, jar_path):
            urls = database_service.get_completed_segments_urls(table)
            if not urls:
                logger.info(f"{table}: No segments completed. Stopping...")
                return

            with tempfile.TemporaryDirectory() as tmp_segments, \
                 tempfile.TemporaryDirectory() as tmp_parquets:
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
                    response_msg = subprocess.getstatusoutput(cmd)[1]
                    if response_msg:
                        raise Exception(f"{response_msg} with status code {status} on create descriptor.")
                    logger.info(f"{table}: Segments converted.")

        _convert_segments_parquet(table, jar_path)
