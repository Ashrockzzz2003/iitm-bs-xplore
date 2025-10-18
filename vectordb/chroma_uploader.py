"""
ChromaDB Uploader Module

This module handles uploading text files from direct/outputs/ into ChromaDB collections.
Each txt file becomes a separate collection named after its folder path.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import chromadb
from chromadb.config import Settings


class ChromaUploader:
    """Handles uploading text files to ChromaDB collections."""
    
    def __init__(self, persist_directory: str = "chroma_data"):
        """
        Initialize the ChromaDB uploader.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
    def get_collection_name(self, file_path: str) -> str:
        """
        Convert file path to collection name.
        
        Args:
            file_path: Path to the txt file
            
        Returns:
            Collection name based on folder structure
        """
        # Extract path relative to direct/outputs/
        path_parts = Path(file_path).parts
        
        # Find the index of 'outputs' in the path
        try:
            outputs_index = path_parts.index('outputs')
            relevant_parts = path_parts[outputs_index + 1:]
        except ValueError:
            # Fallback if 'outputs' not found
            relevant_parts = path_parts[-2:]  # Take last two parts
        
        # Remove 'content.txt' and join with underscore
        if relevant_parts[-1] == 'content.txt':
            relevant_parts = relevant_parts[:-1]
        
        # Join parts with underscore and clean up
        collection_name = '_'.join(relevant_parts)
        # Replace any invalid characters with underscores
        collection_name = re.sub(r'[^a-zA-Z0-9_-]', '_', collection_name)
        
        return collection_name
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                search_start = max(start + chunk_size - 100, start)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > start + chunk_size // 2:  # Only if we find a good break point
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
                
        return chunks
    
    def read_txt_files(self, outputs_dir: str) -> Dict[str, str]:
        """
        Read all txt files from the outputs directory.
        
        Args:
            outputs_dir: Path to the outputs directory
            
        Returns:
            Dictionary mapping file paths to their content
        """
        txt_files = {}
        outputs_path = Path(outputs_dir)
        
        if not outputs_path.exists():
            raise FileNotFoundError(f"Outputs directory not found: {outputs_dir}")
        
        # Find all content.txt files recursively
        for txt_file in outputs_path.rglob("content.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # Only include non-empty files
                        txt_files[str(txt_file)] = content
            except Exception as e:
                print(f"Warning: Could not read {txt_file}: {e}")
                
        return txt_files
    
    def upload_to_collection(self, collection_name: str, text: str, 
                           metadata: Optional[Dict] = None) -> None:
        """
        Upload text to a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            text: Text content to upload
            metadata: Optional metadata for the text
        """
        # Get or create collection
        try:
            collection = self.client.get_collection(collection_name)
        except Exception:
            # Collection doesn't exist, create it
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": f"Content from {collection_name}"}
            )
        
        # Chunk the text
        chunks = self.chunk_text(text)
        
        # Prepare data for upload
        documents = []
        metadatas = []
        ids = []
        
        base_metadata = metadata or {}
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk)
            })
            # Filter out None values from metadata
            chunk_metadata = {k: v for k, v in chunk_metadata.items() if v is not None}
            metadatas.append(chunk_metadata)
            ids.append(f"{collection_name}_chunk_{i}")
        
        # Upload to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Uploaded {len(chunks)} chunks to collection '{collection_name}'")
    
    def upload_all_files(self, outputs_dir: str) -> None:
        """
        Upload all txt files from outputs directory to ChromaDB.
        
        Args:
            outputs_dir: Path to the outputs directory
        """
        print(f"Reading txt files from {outputs_dir}...")
        txt_files = self.read_txt_files(outputs_dir)
        
        if not txt_files:
            print("No txt files found to upload.")
            return
        
        print(f"Found {len(txt_files)} txt files to upload.")
        
        for file_path, content in txt_files.items():
            collection_name = self.get_collection_name(file_path)
            
            # Extract metadata from file path
            path_parts = Path(file_path).parts
            program = None
            level = None
            
            if 'ds' in path_parts:
                program = 'ds'
            elif 'es' in path_parts:
                program = 'es'
            elif 'generic' in path_parts:
                program = 'generic'
            
            if 'degree' in path_parts:
                level = 'degree'
            elif 'diploma' in path_parts:
                level = 'diploma'
            elif 'foundation' in path_parts:
                level = 'foundation'
            
            metadata = {
                "file_path": file_path,
                "program": program,
                "level": level,
                "content_length": len(content)
            }
            
            print(f"Uploading {file_path} to collection '{collection_name}'...")
            self.upload_to_collection(collection_name, content, metadata)
        
        print("Upload completed!")
    
    def list_collections(self) -> List[str]:
        """
        List all available collections.
        
        Returns:
            List of collection names
        """
        collections = self.client.list_collections()
        return [col.name for col in collections]
    
    def query_collection(self, collection_name: str, query_text: str, 
                        n_results: int = 5) -> Dict:
        """
        Query a collection for similar text.
        
        Args:
            collection_name: Name of the collection to query
            query_text: Text to search for
            n_results: Number of results to return
            
        Returns:
            Query results
        """
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results
        except ValueError:
            print(f"Collection '{collection_name}' not found.")
            return {}
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection information
        """
        try:
            collection = self.client.get_collection(collection_name)
            count = collection.count()
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata
            }
        except ValueError:
            print(f"Collection '{collection_name}' not found.")
            return {}


def main():
    """Main function for testing the uploader."""
    uploader = ChromaUploader()
    
    # Upload all files
    outputs_dir = "/Users/ashrock_m13/Ashrockzzz/2025/ai/iitm-bs-xplore/direct/outputs"
    uploader.upload_all_files(outputs_dir)
    
    # List collections
    collections = uploader.list_collections()
    print(f"\nAvailable collections: {collections}")
    
    # Show info for each collection
    for collection_name in collections:
        info = uploader.get_collection_info(collection_name)
        print(f"\nCollection: {info}")


if __name__ == "__main__":
    main()
