import concurrent
import json
import logging
import os
import shutil
import tempfile
import time
from itertools import islice
from datetime import timezone, datetime
import requests
from requests.adapters import HTTPAdapter, Retry
from environment_variables import S3_BUCKET, REQUEST_CHUNK_SIZE, PAUSE_TIME
from services.aws.documentdb_operations import DocumentDB
from services.aws.s3_operations import S3
from utils.cropwise_oauth import oauth_call
from utils.generic_constants import GenericConstants

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
retries = Retry(total=3, backoff_factor=2)
local_adapter = HTTPAdapter(max_retries=retries, pool_connections=30)
session = requests.Session()
session.mount(GenericConstants.ORCHESTRATION_SERVICE_URL, local_adapter)
header = GenericConstants.headers
header.update({
    'Authorization': f'Bearer {oauth_call(session, local_adapter)}'
})
session.headers = header
CRON_EXPRESSION = None


def delete_temp_dir(current_file_path: str):
    """
    This function deletes a directory at the specified file path.

    :param current_file_path: A string representing the path of the directory to be deleted.
    :type current_file_path: str
    :return: None. This function does not return any value.
    """
    if os.path.exists(current_file_path):
        shutil.rmtree(current_file_path)


def make_request_to_model(request_id: str, request: str):
    """
    Function to make call to Orchestration endpoint.

    :param request: API request as saved in S3
    :type request: str
    :param request_id: md5 hash for corresponding request.
    :type request_id: str
    :returns: response generated from specfic model.
    :rtype: str
    """
    request_data = {
        "md5_hash": request_id,
        "cron_expression": CRON_EXPRESSION,
        "request_body": json.loads(request)
    }
    request_data = json.dumps(request_data)
    logger.info(request_data)
    response_data = session.post(
        url=GenericConstants.ORCHESTRATION_SERVICE_URL,
        headers=session.headers,
        data=request_data
    )
    if response_data.status_code == 200:
        return response_data.text
    logger.error("Unsuccessful request: %s", request)
    logger.error("Returned with error: %s", response_data.text)
    return None


def concurrent_model_caller(batch_requests: list, requests_ids: list):
    """
    Function implementing multithreading to call model.

    :param batch_requests: List of model requests.
    :param requests_ids: md5 hash list for corresponding requests.
    :type requests_ids: list
    :returns: size of response.
    :rtype: int
    """
    response_list = []
    logger.info("Making %s requests to orchestrator", len(batch_requests))
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(make_request_to_model, requests_ids, batch_requests)
        for result in results:
            if result is not None:
                response_list.append(result)
        logger.info("Successfully fired request count: %s", len(response_list))
    return len(response_list)


def create_request(
        temp_str_dir: str, temp_req_str_dir: str, files_name_list: list, request_list: list
):
    """
    Function to perform read operation to S3 request data and calling
    orchestration model.
    :param temp_str_dir: Temporary directory.
    :type temp_str_dir: str
    :param temp_req_str_dir: Temporary directory.
    :type temp_req_str_dir: str
    :param files_name_list: List of filenames containing requests.
    :type files_name_list: list
    :param request_list: List of filenames container md5 hash.
    :type request_list: list
    :return: None
    :rtype: None
    """
    for request_id, file_name in zip(request_list, files_name_list):
        fired_req_count = 0
        current_file_path = os.path.join(temp_str_dir, file_name)
        current_req_path = os.path.join(temp_req_str_dir, request_id)
        with open(current_file_path, "r", encoding="utf-8") as payload, open(
                current_req_path, "r", encoding="utf-8"
        ) as req_id:
            logger.info("Reading requests for file: %s", current_file_path)
            while True:
                batch_requests = [
                    x.rstrip("\n") for x in islice(payload, REQUEST_CHUNK_SIZE)
                ]
                requests_ids = [
                    x.rstrip("\n") for x in islice(req_id, REQUEST_CHUNK_SIZE)
                ]
                if not batch_requests:
                    break
                req_count = concurrent_model_caller(batch_requests, requests_ids)
                fired_req_count += req_count
                logger.info("Total fired requests: %s", fired_req_count)
                time.sleep(PAUSE_TIME)


def download_payload_files(
        doc_db_client: DocumentDB, s3_clt: S3, temp_str_dir: str, temp_req_str_dir: str
):
    """
    Function to download payload files.

    :param doc_db_client: An instance of a DocumentDB client.
    :type doc_db_client: DocumentDB
    :param s3_clt: An instance of an Amazon S3 client.
    :type s3_clt: S3
    :param temp_str_dir: Temp directory.
    :type temp_str_dir: str
    :param temp_req_str_dir: Temp directory.
    :type temp_req_str_dir: str
    :return: None
    :rtype: None
    """
    for doc in doc_db_client.find_documents({'_id': str(os.environ['BATCH_ID'])}):
        if (doc.get("payload_file_location") is not None) and (
                doc.get("request_ids_file_location") is not None and
                (datetime.today() >= doc.get('start_date')) and
                (datetime.today() <= doc.get('end_date')) and
                doc.get('is_valid') is True
        ):
            logger.info("Starting execution for BATCH_ID : %s", os.environ['BATCH_ID'])
            global CRON_EXPRESSION  # pylint: disable= global-statement
            CRON_EXPRESSION = doc.get('cron_expression')
            s3_clt.download_all_files(
                S3_BUCKET, doc.get("payload_file_location"), temp_str_dir
            )
            s3_clt.download_all_files(
                S3_BUCKET, doc.get("request_ids_file_location"), temp_req_str_dir
            )
            downloaded_payload_files = os.listdir(temp_str_dir)
            downloaded_request_files = os.listdir(temp_req_str_dir)
            doc_db_client.update('_id', str(os.environ['BATCH_ID']), {
                'status': GenericConstants.PREPARING_EXECUTION,
                'execution_start_time': datetime.now(timezone.utc),
                'completion_status_time': GenericConstants.INITIAL_COMPLETION_TIME
            })
            create_request(
                temp_str_dir,
                temp_req_str_dir,
                downloaded_payload_files,
                downloaded_request_files,
            )
        else:
            logger.info("No payload file found or batch is not valid for batch ID: %s",
                        doc.get("_id"))


if __name__ == "__main__":
    logger.info("Checking and validating for BATCH_ID : %s", os.environ['BATCH_ID'])
    starting_time = time.perf_counter()
    document_db_client = DocumentDB()
    s3_client = S3()
    temp_storage_dir = tempfile.mkdtemp()
    temp_req_storage_dir = tempfile.mkdtemp()
    download_payload_files(
        document_db_client, s3_client, temp_storage_dir, temp_req_storage_dir
    )
    document_db_client.update('_id', str(os.environ['BATCH_ID']), {
        'status': GenericConstants.IN_PROGRESS,
        "prediction_count": GenericConstants.INITIAL_PREDICTION_COUNT
    })
    delete_temp_dir(temp_storage_dir)
    delete_temp_dir(temp_req_storage_dir)
    ending_time = time.perf_counter()
    logger.info("Total execution time: %s", (ending_time - starting_time))
