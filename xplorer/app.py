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
from typing import Any, Dict, List

from util.hierarchical_aggregator import HierarchicalTextAggregator
from util.chromadb.xml_chroma_uploader import upload_all_xml_files

from dotenv import load_dotenv

load_dotenv()


ADDITIONAL_DOCUMENT_SOURCES: List[Dict[str, Any]] = [
    {
        "url": "https://docs.google.com/document/u/1/d/e/2PACX-1vSBP6TJyZDklGPMyRtTwQc1cWZKOrozsOy5qmBwB8awTFvBbPN33-IxUV2WYupNdlXQOCgKwV9fDQKq/pub?urp=gmail_link",
        "program": "GENERIC",
        "type": "document",
        "level": "grading_policy",
        "label": "IITM BS Grading Policy",
        "source": "google_docs",
        "tags": ["grading", "policies", "assessments"],
    },
    {
        "url": "https://docs.google.com/document/u/0/d/e/2PACX-1vRxGnnDCVAO3KX2CGtMIcJQuDrAasVk2JHbDxkjsGrTP5ShhZK8N6ZSPX89lexKx86QPAUswSzGLsOA/pub?pli=1",
        "program": "GENERIC",
        "type": "document",
        "level": "student_handbook",
        "label": "IITM BS Student Handbook",
        "source": "google_docs",
        "tags": ["handbook", "policies", "guidelines"],
    },
]


def cleanup_directories() -> None:
    """Clean up outputs and chroma_data directories before running."""
    print("Cleaning up previous run data...")

    # Clean up outputs directory except the chroma_data directory if it exists inside the outputs directory
    if os.path.exists("outputs"):
        for item in os.listdir("outputs"):
            if item != "chroma_data":
                item_path = os.path.join("outputs", item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"  ✓ Cleared {item}/ directory")
                elif os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"  ✓ Removed {item} file")

    print()


def print_banner() -> None:
    """Print application banner."""
    print("=" * 80)
    print("IITM BS Xplore - Automated Text Extraction & ChromaDB Pipeline")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_summary(stats: Dict[str, Any], segment_label: str) -> None:
    """Print processing summary.

    Args:
        stats: Processing statistics dictionary.
        segment_label: Human friendly label for the processed data slice.
    """
    print("\n" + "=" * 80)
    print(f"PROCESSING SUMMARY: {segment_label}")
    print("=" * 80)
    programs = stats.get("programs") or []
    program_display = ", ".join(programs) if programs else segment_label
    print(f"Programs processed: {program_display}")
    print(f"Total URLs: {stats['total_urls']}")
    print(f"Successful extractions: {stats['successful']}")
    print(f"Failed extractions: {stats['failed']}")
    print(f"Success rate: {(stats['successful']/stats['total_urls']*100):.1f}%")
    print(f"Total words: {stats['total_words']:,}")
    print(f"Total characters: {stats['total_characters']:,}")
    print(f"Total chunks: {stats.get('total_chunks', 0):,}")
    print(f"Processing time: {stats['duration']}")

    print(f"Files created: {len(stats.get('files_created', []))}")
    if stats.get("files_created"):
        print("Hierarchical XML files:")
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
        print("Using hierarchical XML chunking strategy...")

        aggregator = HierarchicalTextAggregator("outputs", chunk_size=1000, chunk_overlap=200)
        doc_stats = None
        try:
            stats = aggregator.aggregate_programs(["ds", "es"])

            # Optional Step 2: Additional document sources
            if ADDITIONAL_DOCUMENT_SOURCES:
                print("\nStep 2: Aggregating policy documents (handbook + grading)...")
                doc_stats = aggregator.aggregate_text_from_urls(ADDITIONAL_DOCUMENT_SOURCES)
        finally:
            aggregator.close()

        # Text extraction complete for DS/ES
        print("\n✓ Text extraction and organization complete for DS/ES")
        print_summary(stats, "DS & ES Programs")

        if doc_stats:
            print("\n✓ Policy documents processed successfully")
            print_summary(doc_stats, "Policy & Handbook Documents")

        # Step 3 (or 4 if docs processed): Upload to ChromaDB
        next_step = 4 if doc_stats else 3
        print(f"\nStep {next_step}: Uploading to ChromaDB...")
        try:
            upload_all_xml_files("outputs")
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
