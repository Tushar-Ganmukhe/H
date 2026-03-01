import os
from pathlib import Path
from dotenv import load_dotenv
from langfuse import Langfuse
from dotenv import load_dotenv
import os

load_dotenv()

# Always load .env (works for API + tests + scripts)
ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)
