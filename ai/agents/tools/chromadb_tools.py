import chromadb
import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

# Initialize ChromaDB client with error handling
try:
    chroma_client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )
    CHROMA_AVAILABLE = True
except Exception as e:
    print(f"Warning: ChromaDB not available: {e}")
    chroma_client = None
    CHROMA_AVAILABLE = False


def get_embeddings(text: str) -> list:
    """Get embeddings for text using Google Gemini (same as uploader)."""
    client = genai.Client()

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )

    return result.embeddings[0].values


def get_available_collections() -> List[str]:
    """Get list of available collections in ChromaDB."""
    if not CHROMA_AVAILABLE:
        print("ChromaDB not available")
        return []
    
    try:
        collections = chroma_client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        print(f"Warning: Could not list collections: {e}")
        return []


def get_collection_info(collection_name: str) -> Dict[str, Any]:
    """Get information about a specific collection."""
    if not CHROMA_AVAILABLE:
        raise Exception("ChromaDB not available")
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
        count = collection.count()
        return {
            "name": collection_name,
            "count": count,
            "metadata": collection.metadata
        }
    except Exception as e:
        raise Exception(f"Error getting collection info: {e}")


def query_chroma(collection_name: str, query: str, n_results: int = 5, 
                where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Query ChromaDB collection with enhanced filtering and metadata.
    
    Args:
        collection_name: Name of the collection to query
        query: Query text
        n_results: Number of results to return
        where: Optional metadata filter (e.g., {"program": "ds", "level": "degree"})
    
    Returns:
        Dictionary with documents, metadatas, distances, and other results
    """
    if not CHROMA_AVAILABLE:
        raise Exception("ChromaDB not available")
    
    try:
        collection = chroma_client.get_collection(name=collection_name)

        # Get embeddings for the query using the same model as uploader
        query_embeddings = get_embeddings(query)

        # Build query parameters
        query_params = {
            "query_embeddings": [query_embeddings],
            "n_results": n_results,
        }
        
        # Add metadata filter if provided
        if where:
            query_params["where"] = where

        results = collection.query(**query_params)

        # Return structured results
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else [],
            "collection": collection_name,
            "query": query,
            "total_results": len(results["documents"][0]) if results["documents"] else 0
        }

    except Exception as e:
        raise Exception(f"Error querying chroma: {e}")


def query_by_program_and_level(program: str, level: str, query: str, 
                              n_results: int = 5) -> Dict[str, Any]:
    """
    Query specific program and level collections.
    
    Args:
        program: Program name (ds, es, generic)
        level: Level (foundation, diploma, degree, main)
        query: Query text
        n_results: Number of results to return
    
    Returns:
        Query results from the specific collection
    """
    # Map level names
    level_mapping = {
        "main": "main",
        "foundation": "foundation", 
        "diploma": "diploma",
        "degree": "degree"
    }
    
    normalized_level = level_mapping.get(level.lower(), level)
    collection_name = f"{program}_{normalized_level}_course"
    
    try:
        return query_chroma(collection_name, query, n_results)
    except Exception as e:
        # Try alternative collection naming
        alt_collection = f"{program}_{normalized_level}"
        try:
            return query_chroma(alt_collection, query, n_results)
        except:
            raise Exception(f"Could not find collection for {program}/{level}: {e}")


def smart_query(query: str, program: Optional[str] = None, level: Optional[str] = None,
               n_results: int = 5) -> Dict[str, Any]:
    """
    Smart query that searches across relevant collections.
    
    Args:
        query: Query text
        program: Optional program filter (ds, es, generic)
        level: Optional level filter (foundation, diploma, degree, main)
        n_results: Number of results to return
    
    Returns:
        Combined results from relevant collections
    """
    available_collections = get_available_collections()
    
    if not available_collections:
        raise Exception("No collections available in ChromaDB")
    
    # If specific program and level provided, query that collection
    if program and level:
        return query_by_program_and_level(program, level, query, n_results)
    
    # Otherwise, search across all relevant collections
    all_results = {
        "documents": [],
        "metadatas": [],
        "distances": [],
        "ids": [],
        "collections_searched": [],
        "query": query,
        "total_results": 0
    }
    
    # Filter collections based on criteria
    target_collections = available_collections
    
    if program:
        target_collections = [c for c in target_collections if program.lower() in c.lower()]
    
    if level:
        target_collections = [c for c in target_collections if level.lower() in c.lower()]
    
    # Query each relevant collection
    for collection_name in target_collections:
        try:
            results = query_chroma(collection_name, query, n_results)
            all_results["collections_searched"].append(collection_name)
            
            # Combine results
            all_results["documents"].extend(results["documents"])
            all_results["metadatas"].extend(results["metadatas"])
            all_results["distances"].extend(results["distances"])
            all_results["ids"].extend(results["ids"])
            
        except Exception as e:
            print(f"Warning: Could not query collection {collection_name}: {e}")
    
    all_results["total_results"] = len(all_results["documents"])
    
    # Sort by distance (lower is better)
    if all_results["distances"]:
        sorted_indices = sorted(range(len(all_results["distances"])), 
                              key=lambda i: all_results["distances"][i])
        
        all_results["documents"] = [all_results["documents"][i] for i in sorted_indices]
        all_results["metadatas"] = [all_results["metadatas"][i] for i in sorted_indices]
        all_results["distances"] = [all_results["distances"][i] for i in sorted_indices]
        all_results["ids"] = [all_results["ids"][i] for i in sorted_indices]
    
    # Limit to requested number of results
    if n_results and len(all_results["documents"]) > n_results:
        all_results["documents"] = all_results["documents"][:n_results]
        all_results["metadatas"] = all_results["metadatas"][:n_results]
        all_results["distances"] = all_results["distances"][:n_results]
        all_results["ids"] = all_results["ids"][:n_results]
        all_results["total_results"] = n_results
    
    return all_results


def format_query_results(results: Dict[str, Any], include_metadata: bool = True) -> str:
    """
    Format query results into a readable string.
    
    Args:
        results: Results from query_chroma or smart_query
        include_metadata: Whether to include metadata in output
    
    Returns:
        Formatted string with results
    """
    if not isinstance(results, dict):
        return "No results found."

    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []
    distances = results.get("distances") or []
    total_results = results.get("total_results", len(documents))

    if not documents:
        return "No results found."

    output = []
    output.append(f"Found {total_results} results")
    
    if "collections_searched" in results:
        output.append(f"Searched collections: {', '.join(results['collections_searched'])}")
    
    output.append("")
    
    for i, doc in enumerate(documents):
        metadata = metadatas[i] if i < len(metadatas) else {}
        distance = distances[i] if i < len(distances) else 0.0
        output.append(f"--- Result {i+1} (Distance: {distance:.3f}) ---")
        output.append(f"Text: {doc[:200]}{'...' if len(doc) > 200 else ''}")
        
        if include_metadata and metadata:
            output.append("Metadata:")
            for key, value in metadata.items():
                output.append(f"  {key}: {value}")
        
        output.append("")
    
    return "\n".join(output)
