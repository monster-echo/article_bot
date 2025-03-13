import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")

if not MOONSHOT_API_KEY:
    raise ValueError("请设置MOONSHOT_API_KEY环境变量")
