import hashlib
import math

from openai import OpenAI

from backend.app.core.config import Settings


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.client is not None:
            vectors: list[list[float]] = []
            batch_size = max(1, min(self.settings.embedding_batch_size, 10))
            for start in range(0, len(texts), batch_size):
                batch = texts[start : start + batch_size]
                response = self.client.embeddings.create(model=self.settings.embedding_model, input=batch)
                vectors.extend(item.embedding for item in response.data)
            return vectors
        return [self._fallback_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def _fallback_embedding(self, text: str, dimensions: int = 256) -> list[float]:
        vector = [0.0] * dimensions
        tokens = [token for token in text.lower().split() if token]
        if not tokens:
            tokens = [text[:64]]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(0, len(digest), 2):
                index = int.from_bytes(digest[i : i + 2], "little") % dimensions
                vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
