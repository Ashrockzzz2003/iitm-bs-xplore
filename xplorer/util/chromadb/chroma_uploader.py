"""
ChromaDB Uploader Module

This module handles uploading text files from direct/outputs/ into ChromaDB collections.
Each txt file becomes a separate collection named after its folder path.
Uses Google Gemini embeddings for vectorization.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings

from google import genai
from google.genai import types

from dotenv import load_dotenv

load_dotenv()


def get_collection_name(file_path: str) -> str:
    """Convert file path to collection name."""
    path_parts = Path(file_path).parts

    # Find the index of 'outputs' in the path
    try:
        outputs_index = path_parts.index("outputs")
        relevant_parts = path_parts[outputs_index + 1 :]
    except ValueError:
        # Fallback if 'outputs' not found
        relevant_parts = path_parts[-2:]  # Take last two parts

    # Remove 'content.txt' and join with underscore
    if relevant_parts[-1] == "content.txt":
        relevant_parts = relevant_parts[:-1]

    # Join parts with underscore and clean up
    collection_name = "_".join(relevant_parts)
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


def read_txt_files(outputs_dir: str) -> Dict[str, str]:
    """Read all txt files from the outputs directory."""
    txt_files = {}
    outputs_path = Path(outputs_dir)

    if not outputs_path.exists():
        raise FileNotFoundError(f"Outputs directory not found: {outputs_dir}")

    # Find all content.txt files recursively
    for txt_file in outputs_path.rglob("content.txt"):
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:  # Only include non-empty files
                    txt_files[str(txt_file)] = content
        except Exception as e:
            print(f"Warning: Could not read {txt_file}: {e}")

    return txt_files


def upload_to_collection(
    client, collection_name: str, text: str, metadata: Optional[Dict] = None
) -> None:
    """Upload text to a ChromaDB collection using Gemini embeddings."""
    # Get or create collection
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        # Collection doesn't exist, create it
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": f"Content from {collection_name}"},
        )

    # Get embeddings for the text
    print(f"Getting embeddings for collection '{collection_name}'...")
    embeddings = get_embeddings(text)

    # Prepare data for upload
    base_metadata = metadata or {}
    base_metadata.update(
        {"content_length": len(text), "embedding_model": "gemini-embedding-001"}
    )

    # Filter out None values from metadata
    base_metadata = {k: v for k, v in base_metadata.items() if v is not None}

    # Upload to collection
    collection.add(
        documents=[text],
        embeddings=embeddings,
        metadatas=[base_metadata],
        ids=[f"{collection_name}_document"],
    )

    print(
        f"Uploaded document to collection '{collection_name}' with {len(embeddings)}-dimensional embedding"
    )


def upload_all_files(outputs_dir: str, persist_directory: str = "chroma_data") -> None:
    """Upload all txt files from outputs directory to ChromaDB."""
    client = chromadb.PersistentClient(
        path=persist_directory, settings=Settings(anonymized_telemetry=False)
    )

    print(f"Reading txt files from {outputs_dir}...")
    txt_files = read_txt_files(outputs_dir)

    if not txt_files:
        print("No txt files found to upload.")
        return

    print(f"Found {len(txt_files)} txt files to upload.")

    for file_path, content in txt_files.items():
        collection_name = get_collection_name(file_path)

        # Extract metadata from file path
        path_parts = Path(file_path).parts
        program = None
        level = None

        if "ds" in path_parts:
            program = "ds"
        elif "es" in path_parts:
            program = "es"
        elif "generic" in path_parts:
            program = "generic"

        if "degree" in path_parts:
            level = "degree"
        elif "diploma" in path_parts:
            level = "diploma"
        elif "foundation" in path_parts:
            level = "foundation"

        metadata = {"file_path": file_path, "program": program, "level": level}

        print(f"Uploading {file_path} to collection '{collection_name}'...")
        upload_to_collection(client, collection_name, content, metadata)

    print("Upload completed!")
