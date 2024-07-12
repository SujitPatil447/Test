
import os
import json
from unittest.mock import patch, MagicMock
import datetime
import requests_mock
from main import make_request_to_model, GenericConstants, delete_temp_dir
from main import concurrent_model_caller, download_payload_files

class TestMain:

    def test_delete_temp_dir_success(self, tmp_path):
        # Given a temporary directory path
        temp_dir = tmp_path / "tempo_dir"
        temp_dir.mkdir()

        # When delete_temp_dir function is called
        delete_temp_dir(str(temp_dir))

        # Then the directory should be deleted
        assert not os.path.exists(temp_dir)

    @patch('main.concurrent.futures.ThreadPoolExecutor')
    @patch('main.make_request_to_model')
    def test_concurrent_model_caller(self, mock_make_request, mock_executor):
        # Given a list of batch requests and request IDs
        batch_requests = ['request1', 'request2', 'request3']
        request_ids = ['id1', 'id2', 'id3']

        # When concurrent_model_caller function is called
        response = concurrent_model_caller(batch_requests, request_ids)

        # Then the requests should be made concurrently
        assert response is not None

    @patch('services.aws.documentdb_operations')
    @patch('services.aws.s3_operations')
    @patch('main.create_request')
    @patch('main.os')
    def test_download_payload_files(self, mock_os, mock_create_request, mock_s3, mock_doc_db):
        # Given a DocumentDB client, S3 client, and temporary directories
        mock_doc_db_instance = mock_doc_db.return_value
        mock_s3_instance = mock_s3.return_value

        # When download_payload_files function is called
        download_payload_files(mock_doc_db_instance, mock_s3_instance, "temp_dir", "temp_req_dir")

        # Then the payload files should be downloaded
        assert mock_s3_instance.download_all_files.call_count == 2

    def test_make_request_to_model_success(self):
        # Given a request ID and request body
        request_id = "test_request_id"
        request_body = '{"key": "value"}'

        # When make_request_to_model function is called
        response = make_request_to_model(request_id, request_body)

        # Then a successful response should be returned
        assert response is not None

    def test_make_request_to_model_failure(self):
        # Given a request ID and request body
        request_id = "test_request_id"
        request_body = '{"key": "value"}'

        # When make_request_to_model function is called with a failed response
        response = make_request_to_model(request_id, request_body)

        # Then a None response should be returned
        assert response is None
