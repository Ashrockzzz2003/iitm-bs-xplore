"""
XML ChromaDB Uploader Module

This module handles uploading XML-formatted text files with chunking strategy into ChromaDB collections.
Each chunk becomes a separate document in ChromaDB for better retrieval performance.
Uses Google Gemini embeddings for vectorization.
"""

import chromadb
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from google import genai
from google.genai import types

# XML parsing utilities
import xml.etree.ElementTree as ET


def get_collection_name(program: str, level: Optional[str] = None, doc_type: Optional[str] = None) -> str:
    """
    Generate collection name based on program, level, and type.
    
    Args:
        program: Program name (e.g., 'ds', 'es')
        level: Level (e.g., 'degree', 'diploma', 'foundation')
        doc_type: Document type (e.g., 'course', 'academics')
    
    Returns:
        Collection name for ChromaDB
    """
    parts = [program]
    if level:
        parts.append(level)
    if doc_type:
        parts.append(doc_type)
    
    collection_name = "_".join(parts)
    # Replace any invalid characters with underscores
    collection_name = re.sub(r"[^a-zA-Z0-9_-]", "_", collection_name)
    
    return collection_name


def get_embeddings(text: str) -> List[float]:
    """Get embeddings for text using Google Gemini."""
    client = genai.Client()

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )

    return result.embeddings[0].values


def upload_chunks_to_collection(
    client, 
    collection_name: str, 
    chunks: List[Dict[str, Any]], 
    program: str,
    level: Optional[str] = None,
    doc_type: Optional[str] = None
) -> None:
    """
    Upload chunks to a ChromaDB collection using Gemini embeddings.
    
    Args:
        client: ChromaDB client
        collection_name: Name of the collection
        chunks: List of chunk dictionaries
        program: Program name
        level: Level (optional)
        doc_type: Document type (optional)
    """
    # Get or create collection
    try:
        collection = client.get_collection(collection_name)
        print(f"Using existing collection: {collection_name}")
    except Exception:
        # Collection doesn't exist, create it
        collection = client.create_collection(
            name=collection_name,
            metadata={
                "description": f"Chunked content from {program} program",
                "program": program,
                "level": level or "all",
                "type": doc_type or "all",
                "chunking_strategy": "xml_based"
            },
        )
        print(f"Created new collection: {collection_name}")

    if not chunks:
        print(f"No chunks to upload for collection {collection_name}")
        return

    print(f"Uploading {len(chunks)} chunks to collection '{collection_name}'...")

    # Prepare data for batch upload
    documents = []
    embeddings = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        # Get embeddings for the chunk text
        try:
            chunk_embeddings = get_embeddings(chunk['text'])
        except Exception as e:
            print(f"Warning: Failed to get embeddings for chunk {i}: {e}")
            continue

        # Prepare metadata
        metadata = chunk['metadata'].copy()
        metadata.update({
            "collection": collection_name,
            "program": program,
            "embedding_model": "gemini-embedding-001"
        })
        
        if level:
            metadata["level"] = level
        if doc_type:
            metadata["type"] = doc_type

        # Filter out None values from metadata
        metadata = {k: v for k, v in metadata.items() if v is not None}

        # Generate unique ID for this chunk
        chunk_id = f"{program}_{chunk['metadata'].get('document_id', 'unknown')}_chunk_{chunk['metadata'].get('chunk_index', i)}"

        documents.append(chunk['text'])
        embeddings.append(chunk_embeddings)
        metadatas.append(metadata)
        ids.append(chunk_id)

    # Upload to collection in batches
    batch_size = 100  # ChromaDB batch size limit
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]

        try:
            collection.add(
                documents=batch_docs,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids,
            )
            print(f"  Uploaded batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
        except Exception as e:
            print(f"Error uploading batch {i//batch_size + 1}: {e}")

    print(f"Successfully uploaded {len(documents)} chunks to collection '{collection_name}'")


def parse_hierarchical_xml(xml_file_path: str) -> List[Dict[str, Any]]:
    """
    Parse hierarchical XML file and extract chunks.
    
    Args:
        xml_file_path: Path to the XML file
        
    Returns:
        List of chunk dictionaries ready for ChromaDB
    """
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    
    chunks = []
    
    # Extract program and level from root attributes
    program = root.get('program', 'unknown')
    level = root.get('level', 'unknown')
    
    for doc_elem in root.findall('document'):
        doc_id = doc_elem.get('id', 'unknown')
        doc_url = doc_elem.get('url', '')
        doc_type = doc_elem.get('type', 'unknown')
        doc_label = doc_elem.get('label', '')
        
        # Extract chunks from this document
        content_elem = doc_elem.find('content')
        if content_elem is not None:
            for chunk_elem in content_elem.findall('chunk'):
                chunk_text = chunk_elem.text or ''
                if chunk_text.strip():
                    chunk_data = {
                        'text': chunk_text,
                        'metadata': {
                            'document_id': doc_id,
                            'url': doc_url,
                            'program': program,
                            'type': doc_type,
                            'level': level,
                            'label': doc_label,
                            'chunk_index': int(chunk_elem.get('index', 0)),
                            'chunk_start': int(chunk_elem.get('start', 0)),
                            'chunk_end': int(chunk_elem.get('end', 0)),
                            'chunk_length': int(chunk_elem.get('length', 0))
                        }
                    }
                    chunks.append(chunk_data)
    
    return chunks

def upload_xml_file(xml_file_path: str, program: str) -> None:
    """
    Upload an XML file with chunked content to ChromaDB.
    
    Args:
        xml_file_path: Path to the XML file
        program: Program name for collection naming
    """
    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )

    if not os.path.exists(xml_file_path):
        raise FileNotFoundError(f"XML file not found: {xml_file_path}")

    print(f"Processing XML file: {xml_file_path}")
    
    # Parse XML and extract chunks
    chunks = parse_hierarchical_xml(xml_file_path)

    if not chunks:
        print("No chunks found in XML file")
        return

    print(f"Found {len(chunks)} chunks in XML file")

    # Group chunks by level and type for better organization
    grouped_chunks = {}
    
    for chunk in chunks:
        level = chunk['metadata'].get('level', 'unknown')
        doc_type = chunk['metadata'].get('type', 'unknown')
        
        key = (level, doc_type)
        if key not in grouped_chunks:
            grouped_chunks[key] = []
        grouped_chunks[key].append(chunk)

    # Upload each group to its own collection
    for (level, doc_type), group_chunks in grouped_chunks.items():
        collection_name = get_collection_name(program, level, doc_type)
        upload_chunks_to_collection(
            client, 
            collection_name, 
            group_chunks, 
            program, 
            level, 
            doc_type
        )

    print("XML upload completed!")


def upload_all_xml_files(outputs_dir: str) -> None:
    """
    Upload all XML files from outputs directory to ChromaDB.
    
    Args:
        outputs_dir: Directory containing XML files
    """
    outputs_path = Path(outputs_dir)
    
    if not outputs_path.exists():
        raise FileNotFoundError(f"Outputs directory not found: {outputs_dir}")

    # Find all XML files
    xml_files = list(outputs_path.rglob("*.xml"))
    
    if not xml_files:
        print("No XML files found to upload.")
        return

    print(f"Found {len(xml_files)} XML files to upload.")

    for xml_file in xml_files:
        # Extract program from file path
        path_parts = xml_file.parts
        program = "unknown"
        
        if "ds" in path_parts:
            program = "ds"
        elif "es" in path_parts:
            program = "es"
        elif "generic" in path_parts:
            program = "generic"

        print(f"\nProcessing: {xml_file}")
        try:
            upload_xml_file(str(xml_file), program)
        except Exception as e:
            print(f"Error processing {xml_file}: {e}")

    print("\nAll XML files processed!")


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload XML files to ChromaDB")
    parser.add_argument("--xml-file", help="Path to specific XML file to upload")
    parser.add_argument("--outputs-dir", default="outputs", help="Directory containing XML files")
    parser.add_argument("--program", help="Program name (ds, es, generic)")
    
    args = parser.parse_args()
    
    if args.xml_file:
        if not args.program:
            print("Error: --program is required when uploading a specific XML file")
            return
        
        upload_xml_file(args.xml_file, args.program)
    else:
        upload_all_xml_files(args.outputs_dir)


if __name__ == "__main__":
    main()
