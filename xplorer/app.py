#!/usr/bin/env python3
"""
Main Orchestration Script

Automated text extraction pipeline for IITM BS Xplore.
Always processes DS and ES programs, extracts text, organizes content hierarchically,
and uploads to ChromaDB.
"""

import os
import shutil
import sys
from datetime import datetime
from typing import Any, Dict

from util.hierarchical_aggregator import HierarchicalTextAggregator
from util.chromadb.chroma_uploader import upload_all_files


def cleanup_directories() -> None:
    """Clean up outputs and chroma_data directories before running."""
    print("Cleaning up previous run data...")

    # Clean up outputs directory
    if os.path.exists("outputs"):
        shutil.rmtree("outputs")
        print("  ✓ Cleared outputs/ directory")
    else:
        print("  ✓ outputs/ directory already clean")

    # Clean up chroma_data directory
    if os.path.exists("chroma_data"):
        shutil.rmtree("chroma_data")
        print("  ✓ Cleared chroma_data/ directory")
    else:
        print("  ✓ chroma_data/ directory already clean")

    print()


def print_banner() -> None:
    """Print application banner."""
    print("=" * 80)
    print("IITM BS Xplore - Automated Text Extraction & ChromaDB Pipeline")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_summary(stats: Dict[str, Any]) -> None:
    """Print processing summary.

    Args:
        stats: Processing statistics dictionary.
    """
    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Programs processed: DS, ES")
    print(f"Total URLs: {stats['total_urls']}")
    print(f"Successful extractions: {stats['successful']}")
    print(f"Failed extractions: {stats['failed']}")
    print(f"Success rate: {(stats['successful']/stats['total_urls']*100):.1f}%")
    print(f"Total words: {stats['total_words']:,}")
    print(f"Total characters: {stats['total_characters']:,}")
    print(f"Processing time: {stats['duration']}")

    print(f"Files created: {len(stats.get('files_created', []))}")
    if stats.get("files_created"):
        print("Hierarchical files:")
        for file_path in stats["files_created"]:
            print(f"  - {file_path}")

    if stats.get("errors"):
        print(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats["errors"][:3]:  # Show first 3 errors
            print(f"  - {error}")
        if len(stats["errors"]) > 3:
            print(f"  ... and {len(stats['errors']) - 3} more errors")

    print("=" * 80)


def main() -> None:
    """Main entry point."""
    print_banner()

    # Clean up previous run data
    cleanup_directories()

    try:
        # Step 1: Aggregate text from DS and ES programs
        print("Step 1: Aggregating text from DS and ES programs...")
        print("Using hierarchical storage structure...")

        aggregator = HierarchicalTextAggregator("outputs")
        try:
            stats = aggregator.aggregate_programs(["ds", "es"])
        finally:
            aggregator.close()

        # Step 2: Text extraction complete
        print("\nStep 2: Text extraction and organization complete")

        # Print summary
        print_summary(stats)

        # Step 3: Upload to ChromaDB
        print("\nStep 3: Uploading to ChromaDB...")
        try:
            upload_all_files("outputs", "chroma_data")
            print("✓ ChromaDB upload completed successfully!")
        except Exception as e:
            print(f"⚠ ChromaDB upload failed: {e}")
            print("Continuing without ChromaDB upload...")

        print(f"\n✓ Pipeline completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
