import os
from elasticsearch import Elasticsearch
from openai import OpenAI

class RAGService:
    def __init__(self):
        # 1. Elasticsearch Connection
        es_host = os.getenv("ES_HOST", "es-container")
        es_port = int(os.getenv("ES_PORT", 9200))
        self.es = Elasticsearch(f"http://{es_host}:{es_port}")
        
        # 2. OpenAI Configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key, base_url=os.getenv("OPENAI_BASE_URL"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.chat_model = os.getenv("SUMMARY_MODEL", "gpt-4o-mini") 

        # 3. Index Setup
        self.index_name = "news_vector_idx"
        self._check_and_create_index_es7()

    def _check_and_create_index_es7(self):
        """
        [ES 7.x 호환] 인덱스 매핑 설정
        ES 7에서는 dense_vector에 'index', 'similarity' 옵션을 빼야 안전합니다.
        """
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "summary": {"type": "text"},
                        "content": {"type": "text"},
                        "vector": {
                            "type": "dense_vector",
                            "dims": 1536  # OpenAI ada-002/3-small 차원
                            # ES 7.x에서는 index: true, similarity 옵션을 제거해야 호환성 문제 없음
                        }
                    }
                }
            }
            try:
                self.es.indices.create(index=self.index_name, body=mapping)
                print(f"[RAGService] Created index '{self.index_name}' for ES 7.x")
            except Exception as e:
                print(f"[RAGService] Failed to create index: {e}")

    def _get_embedding(self, text):
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[RAGService] Embedding Error: {e}")
            return []

    def retrieve_context(self, query):
        """
        [ES 7.x 호환] 하이브리드 검색 (Vector -> Text Fallback)
        1. 벡터 검색 시도
        2. 실패하거나 결과가 없으면 텍스트(키워드) 검색 시도
        """
        print(f"[RAGService] Retrieving context for: {query}")
        
        contexts = []
        
        # ---------------------------------------------------------
        # 1. 시도: 벡터 검색 (Vector Search)
        # ---------------------------------------------------------
        try:
            query_vector = self._get_embedding(query)
            if query_vector:
                script_query = {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                            "params": {"query_vector": query_vector}
                        }
                    }
                }
                response = self.es.search(
                    index=self.index_name,
                    body={"query": script_query, "size": 3}
                )
                
                for hit in response['hits']['hits']:
                    source = hit['_source']
                    text = source.get('summary') or source.get('content') or source.get('title')
                    if text: contexts.append(text)
                
                if contexts:
                    print(f"[RAGService] Vector search success: {len(contexts)} hits")
                    return contexts

            
        except Exception as e:
            print(f"[RAGService] ES Search Error: {e}")
            return []

    def generate_answer(self, query, context_list):
        if not context_list:
            return "죄송합니다. 관련 정보를 찾을 수 없어 답변드리기 어렵습니다."
            
        context_str = "\n\n".join(context_list)
        
        system_prompt = (
            "너는 금융 뉴스 데이터를 기반으로 답변하는 AI 어시스턴트야. "
            "아래 제공된 [Context] 내용을 바탕으로 사용자 질문에 대해 친절하고 정확한 한국어로 답변해줘. "
            "Context에 없는 내용은 지어내지 말고 '정보가 없습니다'라고 말해."
        )
        
        user_prompt = f"[Context]:\n{context_str}\n\n[Question]: {query}"

        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[RAGService] Generation Error: {e}")
            return "답변 생성 중 오류가 발생했습니다."

rag_service = RAGService()