#!/usr/bin/env python3
"""
Hierarchical Text Aggregation Module

Stores extracted text content in a hierarchical directory structure:
- outputs/generic/content.txt (for generic content)
- outputs/ds/{level}/content.txt (for DS program content by level)
- outputs/es/{level}/content.txt (for ES program content by level)
"""

import os
from datetime import datetime
from typing import Any, Dict, List

from .text_extractor import TextExtractor
from .url_fetcher import URLFetcher


class HierarchicalTextAggregator:
    """Aggregates text content from multiple URLs into hierarchical directory structure."""

    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the hierarchical text aggregator.

        Args:
            output_dir: Base directory to save output files
        """
        self.output_dir = output_dir
        self.text_extractor = TextExtractor()
        self.url_fetcher = URLFetcher()

        # Ensure base output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Create subdirectories
        self.generic_dir = os.path.join(output_dir, "generic")
        self.ds_dir = os.path.join(output_dir, "ds")
        self.es_dir = os.path.join(output_dir, "es")

        os.makedirs(self.generic_dir, exist_ok=True)
        os.makedirs(self.ds_dir, exist_ok=True)
        os.makedirs(self.es_dir, exist_ok=True)

    def _get_level_directory(self, program: str, level: str) -> str:
        """
        Get the directory path for a specific program and level.

        Args:
            program: Program type (DS, ES, or generic)
            level: Level (main, level:foundation, level:diploma, level:bsc, level:bs)

        Returns:
            Directory path for the program/level combination
        """
        # Normalize level first
        normalized_level = self._normalize_level(level)

        # Main level content is essentially generic - goes to generic directory
        if normalized_level == "main":
            level_dir = self.generic_dir
        elif program.upper() == "DS":
            level_dir = os.path.join(self.ds_dir, normalized_level)
        elif program.upper() == "ES":
            level_dir = os.path.join(self.es_dir, normalized_level)
        else:
            # Generic content goes to generic directory
            level_dir = self.generic_dir

        os.makedirs(level_dir, exist_ok=True)
        return level_dir

    def _normalize_level(self, level: str) -> str:
        """
        Normalize level string to directory-friendly format.

        Args:
            level: Raw level string (e.g., "level:foundation")

        Returns:
            Normalized level string (e.g., "foundation")
        """
        if level.startswith("level:"):
            return level[6:]  # Remove "level:" prefix
        return level

    def aggregate_text_from_urls(self, urls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate text content from a list of URLs into hierarchical structure.

        Args:
            urls: List of URL dictionaries with metadata

        Returns:
            Dictionary with aggregation statistics
        """
        print(f"Aggregating text from {len(urls)} URLs into hierarchical structure...")

        stats = {
            "total_urls": len(urls),
            "successful": 0,
            "failed": 0,
            "total_words": 0,
            "total_characters": 0,
            "programs": set(),
            "types": set(),
            "levels": set(),
            "start_time": datetime.now(),
            "errors": [],
            "files_created": [],
        }

        # Track content by program/level for appending
        content_buffers = {}

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
                    # Determine program and level
                    program = url_info.get("program", "generic").upper()
                    level = self._normalize_level(url_info.get("level", "main"))
                    content_type = url_info.get("type", "unknown")

                    # Create content entry
                    content_entry = self._create_content_entry(url_info, result)

                    # Get directory for this program/level
                    level_dir = self._get_level_directory(program, level)

                    # Create unique key for this program/level combination
                    # For main level, combine all programs into generic
                    if level == "main":
                        key = "generic_main"
                    else:
                        key = f"{program}_{level}"

                    if key not in content_buffers:
                        if level == "main":
                            content_buffers[key] = {
                                "program": "GENERIC",
                                "level": "main",
                                "directory": level_dir,
                                "content": [],
                            }
                        else:
                            content_buffers[key] = {
                                "program": program,
                                "level": level,
                                "directory": level_dir,
                                "content": [],
                            }

                    # Add content to buffer
                    content_buffers[key]["content"].append(content_entry)

                    # Update statistics
                    stats["successful"] += 1
                    stats["total_words"] += result["word_count"]
                    stats["total_characters"] += result["char_count"]
                    stats["programs"].add(program)
                    stats["types"].add(content_type)
                    stats["levels"].add(level)

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
                stats["errors"].append(f"Error processing {url_info['url']}: {str(e)}")

        # Write content to files
        print("\nWriting content to hierarchical files...")
        for key, buffer_data in content_buffers.items():
            file_path = os.path.join(buffer_data["directory"], "content.txt")

            with open(file_path, "w", encoding="utf-8") as f:
                # Write header
                f.write("=" * 80 + "\n")
                f.write(
                    f"IITM BS Xplore - {buffer_data['program']} Program - {buffer_data['level'].title()} Level\n"
                )
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total entries: {len(buffer_data['content'])}\n")
                f.write("=" * 80 + "\n\n")

                # Write all content entries
                for entry in buffer_data["content"]:
                    f.write(entry)
                    f.write("\n\n")

                # Write footer
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF CONTENT\n")
                f.write("=" * 80 + "\n")

            stats["files_created"].append(file_path)
            print(f"  ✓ Created: {file_path}")

        # Finalize statistics
        stats["end_time"] = datetime.now()
        stats["duration"] = stats["end_time"] - stats["start_time"]
        stats["programs"] = list(stats["programs"])
        stats["types"] = list(stats["types"])
        stats["levels"] = list(stats["levels"])

        print(f"\nHierarchical aggregation complete!")
        print(f"Files created: {len(stats['files_created'])}")
        print(f"Successful: {stats['successful']}/{stats['total_urls']}")
        print(f"Total words: {stats['total_words']:,}")
        print(f"Total characters: {stats['total_characters']:,}")

        return stats

    def _create_content_entry(
        self, url_info: Dict[str, Any], result: Dict[str, Any]
    ) -> str:
        """
        Create a formatted content entry for a URL.

        Args:
            url_info: URL metadata dictionary
            result: Text extraction result

        Returns:
            Formatted content entry string
        """
        entry = []
        entry.append("=" * 40)
        entry.append(f"URL: {url_info['url']}")
        entry.append(f"PROGRAM: {url_info.get('program', 'N/A')}")
        entry.append(f"TYPE: {url_info.get('type', 'N/A')}")

        if url_info.get("course_id"):
            entry.append(f"COURSE_ID: {url_info['course_id']}")

        if url_info.get("label"):
            entry.append(f"LABEL: {url_info['label']}")

        if url_info.get("level"):
            entry.append(f"LEVEL: {url_info['level']}")

        entry.append("=" * 40)
        entry.append("")
        entry.append(result["text"])

        return "\n".join(entry)

    def aggregate_programs(self, programs: List[str]) -> Dict[str, Any]:
        """
        Aggregate text from multiple programs into hierarchical structure.

        Args:
            programs: List of program types (e.g., ['ds', 'es'])

        Returns:
            Dictionary with aggregation statistics
        """
        print(f"Fetching URLs for programs: {', '.join(programs)}")
        urls = self.url_fetcher.get_all_urls_for_programs(programs)

        return self.aggregate_text_from_urls(urls)

    def close(self):
        """Close resources."""
        self.url_fetcher.close()


def aggregate_text_hierarchically(
    programs: List[str], output_dir: str = "outputs"
) -> Dict[str, Any]:
    """
    Convenience function to aggregate text from multiple programs hierarchically.

    Args:
        programs: List of program types (e.g., ['ds', 'es'])
        output_dir: Output directory

    Returns:
        Dictionary with aggregation statistics
    """
    aggregator = HierarchicalTextAggregator(output_dir)
    try:
        return aggregator.aggregate_programs(programs)
    finally:
        aggregator.close()


if __name__ == "__main__":
    # Test the hierarchical text aggregator
    import sys

    if len(sys.argv) < 2:
        print("Usage: python hierarchical_aggregator.py <program1> [program2] ...")
        print("Example: python hierarchical_aggregator.py ds es")
        sys.exit(1)

    programs = sys.argv[1:]
    print(f"Aggregating text hierarchically for programs: {', '.join(programs)}")

    stats = aggregate_text_hierarchically(programs)

    print(f"\nFinal Statistics:")
    print(f"  Successful: {stats['successful']}/{stats['total_urls']}")
    print(f"  Total words: {stats['total_words']:,}")
    print(f"  Total characters: {stats['total_characters']:,}")
    print(f"  Files created: {len(stats['files_created'])}")
    print(f"  Processing time: {stats['duration']}")

    print(f"\nFiles created:")
    for file_path in stats["files_created"]:
        print(f"  - {file_path}")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats["errors"][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(stats["errors"]) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")
