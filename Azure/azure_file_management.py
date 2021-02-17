
import os
from .azure_keys import get_connection_string

from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient

# service = BlobServiceClient(conn_str=get_connection_string())


def upload_blob(file_path, container_name, blob_name):

    print(f'uploading {file_path}')

    blob = BlobClient.from_connection_string(conn_str=get_connection_string(), container_name=container_name, blob_name=blob_name)

    with open(file_path, "rb") as data:
        blob.upload_blob(data)

    return True


def delete_blob(container_name, blob_name):

    print(f'deleting {blob_name}')

    blob = BlobClient.from_connection_string(conn_str=get_connection_string(), container_name=container_name, blob_name=blob_name)

    blob.delete_blob()

    return True
