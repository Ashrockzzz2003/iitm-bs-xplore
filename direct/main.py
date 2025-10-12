#!/usr/bin/env python3
"""
Main Orchestration Script

Command-line interface for the direct text extraction pipeline.
Fetches URLs, extracts text, combines into single file, and uploads to Neo4j.
"""

import argparse
import sys
import os
from typing import List
from datetime import datetime

from text_aggregator import TextAggregator
from text_to_neo4j import TextToNeo4jUploader


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Direct Text Extraction Pipeline for IITM BS Xplore",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract text from DS program only
  python main.py --programs ds

  # Extract text from both DS and ES programs
  python main.py --programs ds es

  # Extract and upload to Neo4j
  python main.py --programs ds es --neo4j

  # Custom output file and Neo4j settings
  python main.py --programs ds es --output my_text.txt --neo4j --neo4j-clear

  # Use custom Neo4j connection
  python main.py --programs ds es --neo4j --neo4j-uri neo4j://localhost:7687 --neo4j-username neo4j --neo4j-password mypassword
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--programs',
        nargs='+',
        choices=['ds', 'es'],
        required=True,
        help='Programs to process (ds, es, or both)'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        default='combined_text.txt',
        help='Output text file name (default: combined_text.txt)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='outputs',
        help='Output directory (default: outputs)'
    )
    
    # Neo4j options
    parser.add_argument(
        '--neo4j',
        action='store_true',
        help='Upload to Neo4j after text extraction'
    )
    
    parser.add_argument(
        '--neo4j-uri',
        default='neo4j://127.0.0.1:7687',
        help='Neo4j URI (default: neo4j://127.0.0.1:7687)'
    )
    
    parser.add_argument(
        '--neo4j-username',
        default='neo4j',
        help='Neo4j username (default: neo4j)'
    )
    
    parser.add_argument(
        '--neo4j-password',
        default='password',
        help='Neo4j password (default: password)'
    )
    
    parser.add_argument(
        '--neo4j-database',
        default='neo4j',
        help='Neo4j database name (default: neo4j)'
    )
    
    parser.add_argument(
        '--neo4j-clear',
        action='store_true',
        help='Clear Neo4j database before uploading'
    )
    
    # Processing options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    
    return parser.parse_args()


def print_banner():
    """Print application banner."""
    print("=" * 80)
    print("IITM BS Xplore - Direct Text Extraction Pipeline")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_summary(stats: dict, args):
    """Print processing summary."""
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
    print(f"Output file: {os.path.join(args.output_dir, args.output)}")
    
    if stats['programs']:
        print(f"Programs found: {', '.join(stats['programs'])}")
    
    if stats['types']:
        print(f"Document types: {', '.join(stats['types'])}")
    
    if stats['errors']:
        print(f"\nErrors encountered: {len(stats['errors'])}")
        if args.verbose:
            for error in stats['errors']:
                print(f"  - {error}")
        else:
            print("  (Use --verbose to see detailed error messages)")
    
    print("=" * 80)


def main():
    """Main entry point."""
    args = parse_arguments()
    
    print_banner()
    
    if args.dry_run:
        print("DRY RUN MODE - No actual processing will be performed")
        print(f"Would process programs: {', '.join(args.programs).upper()}")
        print(f"Would create output file: {os.path.join(args.output_dir, args.output)}")
        if args.neo4j:
            print(f"Would upload to Neo4j: {args.neo4j_uri}")
            if args.neo4j_clear:
                print("Would clear Neo4j database before upload")
        return
    
    try:
        # Step 1: Aggregate text from programs
        print(f"Step 1: Aggregating text from programs: {', '.join(args.programs).upper()}")
        aggregator = TextAggregator(args.output_dir)
        
        try:
            stats = aggregator.aggregate_programs(args.programs, args.output)
        finally:
            aggregator.close()
        
        # Step 2: Upload to Neo4j if requested
        if args.neo4j:
            print(f"\nStep 2: Uploading to Neo4j at {args.neo4j_uri}")
            
            output_file = os.path.join(args.output_dir, args.output)
            uploader = TextToNeo4jUploader(
                uri=args.neo4j_uri,
                username=args.neo4j_username,
                password=args.neo4j_password,
                database=args.neo4j_database
            )
            
            try:
                success = uploader.upload_text_file(output_file, args.neo4j_clear)
                if success:
                    print("✓ Neo4j upload completed successfully!")
                    
                    # Show some example queries
                    print("\nExample Neo4j queries you can run:")
                    print("  # Find all documents")
                    print("  MATCH (d:Document) RETURN d.url, d.program, d.type LIMIT 10")
                    print()
                    print("  # Find documents by program")
                    print("  MATCH (d:Document) WHERE d.program = 'DS' RETURN d.url, d.label LIMIT 10")
                    print()
                    print("  # Search text content")
                    print("  MATCH (d:Document) WHERE d.textContent CONTAINS 'machine learning' RETURN d.url, d.label")
                    print()
                    print("  # Find program structure")
                    print("  MATCH (p:Program)-[:HAS_DOCUMENT]->(d:Document) RETURN p.name, count(d) as doc_count")
                else:
                    print("✗ Neo4j upload failed!")
                    sys.exit(1)
            finally:
                uploader.disconnect()
        else:
            print("\nStep 2: Skipped (--neo4j not specified)")
        
        # Print summary
        print_summary(stats, args)
        
        print(f"\n✓ Pipeline completed successfully!")
        if not args.neo4j:
            print(f"To upload to Neo4j, run: python main.py --programs {' '.join(args.programs)} --neo4j")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
