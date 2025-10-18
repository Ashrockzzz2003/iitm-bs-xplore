"""
Command Line Interface for ChromaDB Vector Database

This module provides CLI commands for uploading and querying ChromaDB collections.
"""

import argparse
import sys
from pathlib import Path
from chroma_uploader import ChromaUploader


def upload_command(args):
    """Upload txt files to ChromaDB collections."""
    uploader = ChromaUploader(persist_directory=args.persist_dir)
    
    outputs_dir = args.outputs_dir
    if not Path(outputs_dir).exists():
        print(f"Error: Outputs directory not found: {outputs_dir}")
        sys.exit(1)
    
    print(f"Uploading files from {outputs_dir}...")
    uploader.upload_all_files(outputs_dir)


def list_command(args):
    """List all available collections."""
    uploader = ChromaUploader(persist_directory=args.persist_dir)
    
    collections = uploader.list_collections()
    
    if not collections:
        print("No collections found.")
        return
    
    print(f"Found {len(collections)} collections:")
    for i, collection_name in enumerate(collections, 1):
        print(f"  {i}. {collection_name}")
        
        # Get collection info
        info = uploader.get_collection_info(collection_name)
        if info:
            print(f"     - Documents: {info.get('count', 'Unknown')}")
            metadata = info.get('metadata', {})
            if metadata:
                print(f"     - Description: {metadata.get('description', 'N/A')}")


def query_command(args):
    """Query a collection for similar text."""
    uploader = ChromaUploader(persist_directory=args.persist_dir)
    
    if not args.collection:
        print("Error: Collection name is required for query command.")
        sys.exit(1)
    
    if not args.query:
        print("Error: Query text is required for query command.")
        sys.exit(1)
    
    print(f"Querying collection '{args.collection}' with: '{args.query}'")
    
    results = uploader.query_collection(
        collection_name=args.collection,
        query_text=args.query,
        n_results=args.n_results
    )
    
    if not results:
        print("No results found or collection doesn't exist.")
        return
    
    print(f"\nFound {len(results.get('documents', [[]])[0])} results:")
    print("-" * 80)
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results.get('documents', [[]])[0],
        results.get('metadatas', [[]])[0],
        results.get('distances', [[]])[0]
    )):
        print(f"\nResult {i + 1} (Distance: {distance:.4f}):")
        print(f"Chunk: {metadata.get('chunk_index', 'N/A')}/{metadata.get('total_chunks', 'N/A')}")
        print(f"Program: {metadata.get('program', 'N/A')}")
        print(f"Level: {metadata.get('level', 'N/A')}")
        print(f"Content: {doc[:200]}{'...' if len(doc) > 200 else ''}")
        print("-" * 40)


def info_command(args):
    """Get detailed information about a collection."""
    uploader = ChromaUploader(persist_directory=args.persist_dir)
    
    if not args.collection:
        print("Error: Collection name is required for info command.")
        sys.exit(1)
    
    info = uploader.get_collection_info(args.collection)
    
    if not info:
        print(f"Collection '{args.collection}' not found.")
        return
    
    print(f"Collection: {info['name']}")
    print(f"Document count: {info['count']}")
    print(f"Metadata: {info.get('metadata', {})}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="ChromaDB Vector Database CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload all txt files
  python cli.py upload

  # List all collections
  python cli.py list

  # Query a collection
  python cli.py query -c ds_degree -q "software engineering"

  # Get collection info
  python cli.py info -c ds_degree
        """
    )
    
    parser.add_argument(
        "--persist-dir",
        default="chroma_data",
        help="ChromaDB persistence directory (default: chroma_data)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload txt files to ChromaDB")
    upload_parser.add_argument(
        "--outputs-dir",
        default="/Users/ashrock_m13/Ashrockzzz/2025/ai/iitm-bs-xplore/direct/outputs",
        help="Path to outputs directory (default: direct/outputs)"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all collections")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query a collection")
    query_parser.add_argument(
        "-c", "--collection",
        required=True,
        help="Collection name to query"
    )
    query_parser.add_argument(
        "-q", "--query",
        required=True,
        help="Query text"
    )
    query_parser.add_argument(
        "-n", "--n-results",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get collection information")
    info_parser.add_argument(
        "-c", "--collection",
        required=True,
        help="Collection name to get info for"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the appropriate command
    if args.command == "upload":
        upload_command(args)
    elif args.command == "list":
        list_command(args)
    elif args.command == "query":
        query_command(args)
    elif args.command == "info":
        info_command(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
