#!/usr/bin/env python3
"""
Main Orchestration Script

Command-line interface for the direct text extraction pipeline.
Fetches URLs, extracts text, and organizes content hierarchically.
"""

import argparse
import sys
from datetime import datetime
from typing import Any, Dict

from hierarchical_aggregator import HierarchicalTextAggregator
from text_aggregator import TextAggregator


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="IITM BS Xplore - Direct Text Extraction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract text from DS program only
  python main.py ds

  # Extract text from both DS and ES programs
  python main.py ds es

  # Use hierarchical storage (recommended)
  python main.py ds es --hierarchical

  # Dry run to preview
  python main.py ds es --hierarchical --dry-run
        """
    )
    
    # Required arguments
    parser.add_argument(
        'programs',
        nargs='+',
        choices=['ds', 'es'],
        help='Programs to process (ds, es, or both)'
    )
    
    # Optional flags
    parser.add_argument(
        '--hierarchical',
        action='store_true',
        help='Use hierarchical storage structure (recommended)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    
    return parser.parse_args()


def print_banner() -> None:
    """Print application banner."""
    print("=" * 80)
    print("IITM BS Xplore - Direct Text Extraction Pipeline")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_summary(stats: Dict[str, Any], args: argparse.Namespace) -> None:
    """Print processing summary.
    
    Args:
        stats: Processing statistics dictionary.
        args: Parsed command line arguments.
    """
    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Programs processed: {', '.join(args.programs).upper()}")
    print(f"Total URLs: {stats['total_urls']}")
    print(f"Successful extractions: {stats['successful']}")
    print(f"Failed extractions: {stats['failed']}")
    print(f"Success rate: {(stats['successful']/stats['total_urls']*100):.1f}%")
    print(f"Total words: {stats['total_words']:,}")
    print(f"Total characters: {stats['total_characters']:,}")
    print(f"Processing time: {stats['duration']}")
    
    if args.hierarchical:
        print(f"Files created: {len(stats.get('files_created', []))}")
        if stats.get('files_created'):
            print("Hierarchical files:")
            for file_path in stats['files_created']:
                print(f"  - {file_path}")
    else:
        print(f"Output file: outputs/combined_text.txt")
    
    if stats.get('errors'):
        print(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors'][:3]:  # Show first 3 errors
            print(f"  - {error}")
        if len(stats['errors']) > 3:
            print(f"  ... and {len(stats['errors']) - 3} more errors")
    
    print("=" * 80)


def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    print_banner()
    
    if args.dry_run:
        print("DRY RUN MODE - No actual processing will be performed")
        print(f"Would process programs: {', '.join(args.programs).upper()}")
        if args.hierarchical:
            print("Would use hierarchical storage structure:")
            print("  - outputs/generic/content.txt (main/academics from all programs)")
            print("  - outputs/ds/{level}/content.txt (DS program courses by level)")
            print("  - outputs/es/{level}/content.txt (ES program courses by level)")
        else:
            print("Would create output file: outputs/combined_text.txt")
        return
    
    try:
        # Step 1: Aggregate text from programs
        print(f"Step 1: Aggregating text from programs: {', '.join(args.programs).upper()}")
        
        if args.hierarchical:
            print("Using hierarchical storage structure...")
            aggregator = HierarchicalTextAggregator("outputs")
            try:
                stats = aggregator.aggregate_programs(args.programs)
            finally:
                aggregator.close()
        else:
            print("Using single file storage...")
            aggregator = TextAggregator("outputs")
            try:
                stats = aggregator.aggregate_programs(args.programs, "combined_text.txt")
            finally:
                aggregator.close()
        
        # Step 2: Processing complete
        print("\nStep 2: Text extraction and organization complete")
        
        # Print summary
        print_summary(stats, args)
        
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
