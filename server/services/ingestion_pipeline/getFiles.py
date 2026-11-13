from services.repository import Repository
import base64
import requests
from loguru import logger

def getCodeFiles(repository: Repository):
    url = repository.url
    headers = repository.headers
    root_folder = repository.root_folder

    try:
        tree_blobs = getRepoTree(url, headers)
        code_files = {}
        
        for tree_blob in tree_blobs:
            codefile_path = tree_blob.get("path", "")
            if codefile_path.startswith(root_folder) and codefile_path.endswith(".py"):
                source_code = getRawCode(tree_blob, headers)
                code_files[codefile_path] = source_code        
        return code_files
    except Exception as e:
        logger.error(f"Issue retrieving repository files for RAG ingestion step: ", e)
        raise e

def getRepoTree(url, headers):
    try:
        result = requests.get(url, headers=headers)
        result.raise_for_status()
        
        result_json = result.json()
        tree = result_json["tree"]
        tree_blobs = [blob for blob in tree if blob.get("type") == "blob"]
        return tree_blobs
    except Exception as e:
            logger.error(f"Error getting repository tree from URL: ", e)
            raise e


def getRawCode(tree_blob, headers):
    try:
        file_url = tree_blob.get("url")
        if not file_url:
            return ""
        result = requests.get(file_url, headers=headers)
        result.raise_for_status()
        result_json = result.json()
        
        b64_encoded_content = result_json.get("content", "")
        cleaned_b64 = b64_encoded_content.replace("\n", "")
        source_code = base64.b64decode(cleaned_b64).decode("utf-8")
        return source_code
    except Exception as e:
            logger.error(f"Error retrieving source code from file: ", e)
            raise e

