import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

owner = "msiemens"
repo = os.getenv("REPO_NAME")
branch = "master"
root_folder = "tinydb"
API_KEY = os.getenv("GITHUB_API_KEY")

headers = {
    "Accept": "application/vnd.github+json",  
    "Authorization": f"Bearer {API_KEY}",   
}
url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

def getCodeFiles():
    tree_blobs = getRepoTree()
    code_files = {}
    
    for tree_blob in tree_blobs:
        codefile_path = tree_blob.get("path", "")
        if codefile_path.startswith(root_folder):
            source_code = getRawCode(tree_blob)
            code_files[codefile_path] = source_code        
    return code_files

def getRepoTree():
    result = requests.get(url, headers=headers)
    result.raise_for_status()
    
    result_json = result.json()
    tree = result_json["tree"]
    tree_blobs = [blob for blob in tree if blob.get("type") == "blob"]
    return tree_blobs

def getRawCode(tree_blob):
    file_url = tree_blob.get("url")
    result = requests.get(file_url, headers=headers)
    result.raise_for_status()
    result_json = result.json()
    
    b64_encoded_content = result_json.get("content", "")
    cleaned_b64 = b64_encoded_content.replace("\n", "")
    source_code = base64.b64decode(cleaned_b64).decode("utf-8")
    return source_code
