#!/usr/bin/env python3
"""
Text Aggregation Module

Combines extracted text from multiple URLs into a single text file
with clear separators and metadata.
"""

import os
from datetime import datetime
from typing import Any, Dict, List

from text_extractor import TextExtractor
from url_fetcher import URLFetcher


class TextAggregator:
    """Aggregates text content from multiple URLs into a single file."""

    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the text aggregator.

        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = output_dir
        self.text_extractor = TextExtractor()
        self.url_fetcher = URLFetcher()

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def aggregate_text_from_urls(
        self, urls: List[Dict[str, Any]], output_file: str = "combined_text.txt"
    ) -> Dict[str, Any]:
        """
        Aggregate text content from a list of URLs.

        Args:
            urls: List of URL dictionaries with metadata
            output_file: Name of output file

        Returns:
            Dictionary with aggregation statistics
        """
        output_path = os.path.join(self.output_dir, output_file)

        print(f"Aggregating text from {len(urls)} URLs...")
        print(f"Output file: {output_path}")

        stats = {
            "total_urls": len(urls),
            "successful": 0,
            "failed": 0,
            "total_words": 0,
            "total_characters": 0,
            "programs": set(),
            "types": set(),
            "start_time": datetime.now(),
            "errors": [],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("IITM BS Xplore - Combined Text Content\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total URLs: {len(urls)}\n")
            f.write("=" * 80 + "\n\n")

            # Process each URL
            for i, url_info in enumerate(urls, 1):
                print(f"Processing {i}/{len(urls)}: {url_info['url']}")

                try:
                    # Fetch HTML content
                    html = self.url_fetcher.fetch_html(url_info["url"])

                    # Extract text
                    result = self.text_extractor.extract_text_from_html(
                        html, url_info["url"]
                    )

                    if result["word_count"] > 0:
                        # Write URL separator
                        f.write("=" * 40 + "\n")
                        f.write(f"URL: {url_info['url']}\n")
                        f.write(f"PROGRAM: {url_info['program']}\n")
                        f.write(f"TYPE: {url_info['type']}\n")

                        if url_info.get("course_id"):
                            f.write(f"COURSE_ID: {url_info['course_id']}\n")

                        if url_info.get("label"):
                            f.write(f"LABEL: {url_info['label']}\n")

                        if url_info.get("level"):
                            f.write(f"LEVEL: {url_info['level']}\n")

                        f.write("=" * 40 + "\n\n")

                        # Write extracted text
                        f.write(result["text"])
                        f.write("\n\n")

                        # Update statistics
                        stats["successful"] += 1
                        stats["total_words"] += result["word_count"]
                        stats["total_characters"] += result["char_count"]
                        stats["programs"].add(url_info["program"])
                        stats["types"].add(url_info["type"])

                        print(
                            f"  ✓ Extracted {result['word_count']} words, {result['char_count']} characters"
                        )
                    else:
                        print(f"  ⚠ No text content extracted")
                        stats["failed"] += 1
                        stats["errors"].append(f"No text content: {url_info['url']}")

                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    stats["failed"] += 1
                    stats["errors"].append(
                        f"Error processing {url_info['url']}: {str(e)}"
                    )

                    # Write error entry to file
                    f.write("=" * 40 + "\n")
                    f.write(f"URL: {url_info['url']}\n")
                    f.write(f"PROGRAM: {url_info['program']}\n")
                    f.write(f"TYPE: {url_info['type']}\n")
                    f.write(f"ERROR: {str(e)}\n")
                    f.write("=" * 40 + "\n\n")
                    f.write(f"ERROR: Failed to extract text content from this URL.\n\n")

        # Finalize statistics
        stats["end_time"] = datetime.now()
        stats["duration"] = stats["end_time"] - stats["start_time"]
        stats["programs"] = list(stats["programs"])
        stats["types"] = list(stats["types"])

        # Write footer with statistics
        with open(output_path, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("AGGREGATION STATISTICS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total URLs processed: {stats['total_urls']}\n")
            f.write(f"Successful extractions: {stats['successful']}\n")
            f.write(f"Failed extractions: {stats['failed']}\n")
            f.write(f"Total words: {stats['total_words']:,}\n")
            f.write(f"Total characters: {stats['total_characters']:,}\n")
            f.write(f"Programs: {', '.join(stats['programs'])}\n")
            f.write(f"Types: {', '.join(stats['types'])}\n")
            f.write(f"Processing time: {stats['duration']}\n")

            if stats["errors"]:
                f.write(f"\nErrors encountered:\n")
                for error in stats["errors"]:
                    f.write(f"  - {error}\n")

        print(f"\nAggregation complete!")
        print(f"Output file: {output_path}")
        print(f"Successful: {stats['successful']}/{stats['total_urls']}")
        print(f"Total words: {stats['total_words']:,}")
        print(f"Total characters: {stats['total_characters']:,}")

        return stats

    def aggregate_programs(
        self, programs: List[str], output_file: str = "combined_text.txt"
    ) -> Dict[str, Any]:
        """
        Aggregate text from multiple programs.

        Args:
            programs: List of program types (e.g., ['ds', 'es'])
            output_file: Name of output file

        Returns:
            Dictionary with aggregation statistics
        """
        print(f"Fetching URLs for programs: {', '.join(programs)}")
        urls = self.url_fetcher.get_all_urls_for_programs(programs)

        return self.aggregate_text_from_urls(urls, output_file)

    def close(self):
        """Close resources."""
        self.url_fetcher.close()


def aggregate_text_from_programs(
    programs: List[str],
    output_file: str = "combined_text.txt",
    output_dir: str = "outputs",
) -> Dict[str, Any]:
    """
    Convenience function to aggregate text from multiple programs.

    Args:
        programs: List of program types (e.g., ['ds', 'es'])
        output_file: Name of output file
        output_dir: Output directory

    Returns:
        Dictionary with aggregation statistics
    """
    aggregator = TextAggregator(output_dir)
    try:
        return aggregator.aggregate_programs(programs, output_file)
    finally:
        aggregator.close()


if __name__ == "__main__":
    # Test the text aggregator
    import sys

    if len(sys.argv) < 2:
        print("Usage: python text_aggregator.py <program1> [program2] ...")
        print("Example: python text_aggregator.py ds es")
        sys.exit(1)

    programs = sys.argv[1:]
    print(f"Aggregating text for programs: {', '.join(programs)}")

    stats = aggregate_text_from_programs(programs)

    print(f"\nFinal Statistics:")
    print(f"  Successful: {stats['successful']}/{stats['total_urls']}")
    print(f"  Total words: {stats['total_words']:,}")
    print(f"  Total characters: {stats['total_characters']:,}")
    print(f"  Processing time: {stats['duration']}")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats["errors"][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(stats["errors"]) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")
