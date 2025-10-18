import chromadb
import os
from google import genai
from google.genai import types

chroma_client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8000")),
)


def get_embeddings(text: str) -> list:
    """Get embeddings for text using Google Gemini (same as uploader)."""
    client = genai.Client()

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )

    return result.embeddings[0].values


def query_chroma(collection_name: str, query: str):
    try:
        collection = chroma_client.get_collection(name=collection_name)

        # Get embeddings for the query using the same model as uploader
        query_embeddings = get_embeddings(query)

        results = collection.query(
            query_embeddings=[query_embeddings],
            n_results=int(os.getenv("CHROMA_N_RESULTS", "5")),
        )

        # print(f"results['included']: {results['included']}")
        # print(f"results['distances']: {results['distances']}")
        # print(f"results['metadatas']: {results['metadatas']}")
        # print(f"results['documents']: {results['documents']}")
        # print(f"results['embeddings']: {results['embeddings']}")
        # print(f"results['data']: {results['data']}")

        return results["documents"][0]

    except Exception as e:
        raise Exception(f"Error querying chroma: {e}")
