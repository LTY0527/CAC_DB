from json import load
import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_llm_client():
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise ValueError("未读取到 LLM_API_KEY，请检查 backend/.env")

    http_client = httpx.Client(
        trust_env=False,   # 关键：不读取系统代理环境变量
        timeout=httpx.Timeout(60.0, connect=20.0)
    )

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=http_client
    )

def call_llm(prompt_text):
    client = get_llm_client()
    model_name = os.getenv("LLM_MODEL", "deepseek-chat")

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "你是一名严谨的高校就业分析顾问，擅长基于结构化数据撰写管理分析专报。"
            },
            {
                "role": "user",
                "content": prompt_text
            }
        ],
        temperature=0.4,
        max_tokens=500,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("模型返回为空")
    return content