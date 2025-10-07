from azure.storage.blob import generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta
import os

AZURE_STORAGE_CONNECTION=os.getenv("STORAGE_KEY")

CHUNK_STORAGE_CONTAINER_NAME="prod-mihai-container"

async def get_blob_link(blob_service_client, blob_name, container_name, page_number):
    account_name = blob_service_client.account_name
    credential = getattr(blob_service_client, "credential", None)
    account_key = None
    if credential is not None:
        # Support both SharedKeyCredential (account_key) and AzureNamedKeyCredential (key)
        account_key = getattr(credential, "account_key", None) or getattr(credential, "key", None)
    if not account_key:
        raise ValueError("Storage account key not available for SAS generation.")

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    if page_number == "N/A":
        blob_url_with_sas = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
    else:
        blob_url_with_sas = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}#page={page_number}"

    return blob_url_with_sas

    