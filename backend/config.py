import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", "default-dev-key")
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
