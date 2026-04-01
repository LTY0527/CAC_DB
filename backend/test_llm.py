import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("API KEY exists:", bool(os.getenv("LLM_API_KEY")))
print("BASE URL:", os.getenv("LLM_BASE_URL"))
print("MODEL:", os.getenv("LLM_MODEL"))

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    http_client=httpx.Client(trust_env=False, timeout=60.0)
)

resp = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "deepseek-chat"),
    messages=[
        {"role": "user", "content": "请回复：测试成功"}
    ]
)

print(resp.choices[0].message.content)