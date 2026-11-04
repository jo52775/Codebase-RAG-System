import os
from dotenv import load_dotenv

load_dotenv()

class Repository:
    def __init__(self):
        self.name = "tinyDB"
        self.root_folder = "tinydb"
        self.branch = "master"
        self.owner = "msiemens"
        self.api_key = os.getenv("GITHUB_API_KEY")
        self.url = f"https://api.github.com/repos/{self.owner}/{self.name}/git/trees/{self.branch}?recursive=1"
        self.headers = {
                "Accept": "application/vnd.github+json",  
                "Authorization": f"Bearer {self.api_key}",   
        }