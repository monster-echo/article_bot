import os
from dotenv import load_dotenv

if os.getenv("PROD"):
    load_dotenv(".env.prod")
    print("加载生产环境配置")
else:
    load_dotenv()
    print("加载开发环境配置")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

AISTUDIOX_API_URL = os.getenv("AISTUDIOX_API_URL", "https://aistudiox.com/api")
EDGE_AISHUOHUA_URL = os.getenv("EDGE_AISHUOHUA_URL", "https://edge.aishuohua.art")
SEARXNG_API_URL = os.getenv("SEARXNG_API_URL", "https://searxng.aishuohua.art")

if not MOONSHOT_API_KEY:
    raise ValueError("请设置MOONSHOT_API_KEY环境变量")
