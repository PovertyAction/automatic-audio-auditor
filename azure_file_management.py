
import os
from azure_keys import get_connection_string

from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient

# service = BlobServiceClient(conn_str=get_connection_string())


CONTAINER_NAME = 'mycontainer'

def upload_blob(file_path, blob_name):

    print(f'uploading {file_path}')

    blob = BlobClient.from_connection_string(conn_str=get_connection_string(), container_name=CONTAINER_NAME, blob_name=blob_name)

    with open(file_path, "rb") as data:
        blob.upload_blob(data)

    return True
