from dotenv import load_dotenv
from core.utils.openai_client import get_openai_client

load_dotenv()

client = get_openai_client()

text = "삼성전자 반도체 업황 회복으로 실적 기대감 확대"

resp = client.embeddings.create(
    model="text-embedding-3-small",
    input=text
)

vec = resp.data[0].embedding
print("embedding length:", len(vec))
