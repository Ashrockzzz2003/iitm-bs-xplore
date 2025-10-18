"""
AI Agent Tools for ChromaDB Vector Database

This module provides easy-to-use functions that AI agents can import and use
to interact with the ChromaDB vector database.
"""

from typing import List, Dict, Any, Optional
from chroma_uploader import ChromaUploader


class VectorDBTools:
    """AI Agent-friendly tools for ChromaDB operations."""
    
    def __init__(self, persist_directory: str = "chroma_data"):
        """
        Initialize the VectorDB tools.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.uploader = ChromaUploader(persist_directory)
    
    def search_content(self, query: str, collection: Optional[str] = None, 
                      n_results: int = 5) -> Dict[str, Any]:
        """
        Search for content across collections.
        
        Args:
            query: Search query text
            collection: Specific collection to search (None for all collections)
            n_results: Number of results to return per collection
            
        Returns:
            Dictionary with search results
        """
        if collection:
            # Search specific collection
            results = self.uploader.query_collection(collection, query, n_results)
            return {
                "collection": collection,
                "query": query,
                "results": self._format_results(results),
                "total_results": len(results.get('documents', [[]])[0]) if results else 0
            }
        else:
            # Search all collections
            all_results = {}
            collections = self.uploader.list_collections()
            
            for coll in collections:
                results = self.uploader.query_collection(coll, query, n_results)
                if results and results.get('documents', [[]])[0]:
                    all_results[coll] = {
                        "results": self._format_results(results),
                        "total_results": len(results.get('documents', [[]])[0])
                    }
            
            return {
                "query": query,
                "collections_searched": len(collections),
                "collections_with_results": len(all_results),
                "results_by_collection": all_results
            }
    
    def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """
        Get information about a specific collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Collection information
        """
        info = self.uploader.get_collection_info(collection)
        return {
            "collection": collection,
            "exists": bool(info),
            "document_count": info.get('count', 0) if info else 0,
            "metadata": info.get('metadata', {}) if info else {}
        }
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all available collections with their info.
        
        Returns:
            List of collection information
        """
        collections = self.uploader.list_collections()
        collection_info = []
        
        for coll in collections:
            info = self.uploader.get_collection_info(coll)
            collection_info.append({
                "name": coll,
                "document_count": info.get('count', 0) if info else 0,
                "description": info.get('metadata', {}).get('description', '') if info else ''
            })
        
        return collection_info
    
    def search_by_program(self, query: str, program: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search for content within a specific program (ds, es, generic).
        
        Args:
            query: Search query text
            program: Program type (ds, es, generic)
            n_results: Number of results to return per collection
            
        Returns:
            Search results for the program
        """
        collections = self.uploader.list_collections()
        program_collections = [coll for coll in collections if coll.startswith(program)]
        
        if not program_collections:
            return {
                "program": program,
                "query": query,
                "error": f"No collections found for program '{program}'",
                "available_programs": list(set(coll.split('_')[0] for coll in collections))
            }
        
        results = {}
        for coll in program_collections:
            search_results = self.uploader.query_collection(coll, query, n_results)
            if search_results and search_results.get('documents', [[]])[0]:
                results[coll] = {
                    "results": self._format_results(search_results),
                    "total_results": len(search_results.get('documents', [[]])[0])
                }
        
        return {
            "program": program,
            "query": query,
            "collections_searched": program_collections,
            "collections_with_results": len(results),
            "results_by_collection": results
        }
    
    def search_by_level(self, query: str, level: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search for content within a specific academic level (degree, diploma, foundation).
        
        Args:
            query: Search query text
            level: Academic level (degree, diploma, foundation)
            n_results: Number of results to return per collection
            
        Returns:
            Search results for the level
        """
        collections = self.uploader.list_collections()
        level_collections = [coll for coll in collections if coll.endswith(level)]
        
        if not level_collections:
            return {
                "level": level,
                "query": query,
                "error": f"No collections found for level '{level}'",
                "available_levels": list(set(coll.split('_')[1] for coll in collections if '_' in coll))
            }
        
        results = {}
        for coll in level_collections:
            search_results = self.uploader.query_collection(coll, query, n_results)
            if search_results and search_results.get('documents', [[]])[0]:
                results[coll] = {
                    "results": self._format_results(search_results),
                    "total_results": len(search_results.get('documents', [[]])[0])
                }
        
        return {
            "level": level,
            "query": query,
            "collections_searched": level_collections,
            "collections_with_results": len(results),
            "results_by_collection": results
        }
    
    def get_similar_content(self, content: str, collection: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Find content similar to a given text snippet.
        
        Args:
            content: Text content to find similar content for
            collection: Collection to search in
            n_results: Number of similar results to return
            
        Returns:
            Similar content results
        """
        results = self.uploader.query_collection(collection, content, n_results)
        return {
            "input_content": content[:100] + "..." if len(content) > 100 else content,
            "collection": collection,
            "similar_results": self._format_results(results),
            "total_found": len(results.get('documents', [[]])[0]) if results else 0
        }
    
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format ChromaDB results for easier consumption by AI agents.
        
        Args:
            results: Raw ChromaDB query results
            
        Returns:
            Formatted results list
        """
        if not results or not results.get('documents', [[]])[0]:
            return []
        
        formatted = []
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
            formatted.append({
                "rank": i + 1,
                "content": doc,
                "similarity_score": 1 - distance,  # Convert distance to similarity
                "metadata": {
                    "program": metadata.get('program'),
                    "level": metadata.get('level'),
                    "chunk_index": metadata.get('chunk_index'),
                    "total_chunks": metadata.get('total_chunks'),
                    "file_path": metadata.get('file_path')
                }
            })
        
        return formatted


# Convenience functions for direct import
def create_vector_tools(persist_directory: str = "chroma_data") -> VectorDBTools:
    """Create a VectorDBTools instance."""
    return VectorDBTools(persist_directory)


def quick_search(query: str, collection: Optional[str] = None, n_results: int = 5) -> Dict[str, Any]:
    """
    Quick search function for simple use cases.
    
    Args:
        query: Search query
        collection: Optional specific collection
        n_results: Number of results
        
    Returns:
        Search results
    """
    tools = VectorDBTools()
    return tools.search_content(query, collection, n_results)


def quick_search_by_program(query: str, program: str, n_results: int = 5) -> Dict[str, Any]:
    """
    Quick search by program function.
    
    Args:
        query: Search query
        program: Program type (ds, es, generic)
        n_results: Number of results
        
    Returns:
        Search results
    """
    tools = VectorDBTools()
    return tools.search_by_program(query, program, n_results)


# Example usage for AI agents
if __name__ == "__main__":
    # Example usage
    tools = VectorDBTools()
    
    # Search across all collections
    print("=== Search across all collections ===")
    results = tools.search_content("software engineering")
    print(f"Found results in {results['collections_with_results']} collections")
    
    # Search specific collection
    print("\n=== Search specific collection ===")
    results = tools.search_content("artificial intelligence", "ds_degree")
    print(f"Found {results['total_results']} results in ds_degree")
    
    # Search by program
    print("\n=== Search by program ===")
    results = tools.search_by_program("circuits", "es")
    print(f"Found results in {results['collections_with_results']} ES collections")
    
    # List collections
    print("\n=== Available collections ===")
    collections = tools.list_collections()
    for coll in collections:
        print(f"- {coll['name']}: {coll['document_count']} documents")
