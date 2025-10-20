#!/usr/bin/env python3
"""
Hierarchical Text Aggregation Module (XML with Chunking)

Stores extracted text content in a hierarchical directory structure with XML output:
- outputs/generic/content.xml (for generic content)
- outputs/ds/{level}/content.xml (for DS program content by level)
- outputs/es/{level}/content.xml (for ES program content by level)

Each level file is an XML document containing multiple <document> elements,
and each document is chunked for improved retrieval (e.g., for ChromaDB).
"""

import os
from datetime import datetime
from typing import Any, Dict, List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from .text_extractor import TextExtractor
from .url_fetcher import URLFetcher


class HierarchicalTextAggregator:
    """Aggregates text content into hierarchical directories as XML with chunking."""

    def __init__(
        self,
        output_dir: str = "outputs",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the hierarchical text aggregator.

        Args:
            output_dir: Base directory to save output files
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.output_dir = output_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
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

    def _chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better retrieval.

        Args:
            text: Text content to chunk
            metadata: Metadata for the text

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if len(text) <= self.chunk_size:
            return [
                {
                    "text": text.strip(),
                    "metadata": {
                        **metadata,
                        "chunk_index": 0,
                        "total_chunks": 1,
                        "chunk_start": 0,
                        "chunk_end": len(text),
                        "chunk_length": len(text.strip()),
                    },
                }
            ]

        chunks: List[Dict[str, Any]] = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                sentence_end = text.rfind(".", start, end)
                if sentence_end > start + self.chunk_size * 0.7:
                    end = sentence_end + 1
                else:
                    word_end = text.rfind(" ", start, end)
                    if word_end > start + self.chunk_size * 0.8:
                        end = word_end

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_meta = {
                    **metadata,
                    "chunk_index": chunk_index,
                    "total_chunks": -1,
                    "chunk_start": start,
                    "chunk_end": end,
                    "chunk_length": len(chunk_text),
                }
                chunks.append({"text": chunk_text, "metadata": chunk_meta})
                chunk_index += 1

            start = max(start + self.chunk_size - self.chunk_overlap, end)

        total = len(chunks)
        for ch in chunks:
            ch["metadata"]["total_chunks"] = total

        return chunks

    def _create_xml_document(
        self, chunks: List[Dict[str, Any]], url_info: Dict[str, Any]
    ) -> Element:
        """Create an XML <document> element for a URL with its chunks."""
        doc = Element("document")
        doc.set(
            "id",
            url_info.get(
                "course_id", url_info["url"].split("/")[-1].replace(".html", "")
            ),
        )
        doc.set("url", url_info["url"])
        if url_info.get("program"):
            doc.set("program", url_info.get("program"))
        if url_info.get("type"):
            doc.set("type", url_info.get("type"))
        if url_info.get("level"):
            doc.set("level", url_info.get("level"))
        if url_info.get("label"):
            doc.set("label", url_info.get("label"))

        metadata_elem = SubElement(doc, "metadata")
        for key, value in url_info.items():
            if value is not None:
                me = SubElement(metadata_elem, key)
                me.text = str(value)

        content = SubElement(doc, "content")
        content.set("total_chunks", str(len(chunks)))
        for i, ch in enumerate(chunks):
            ce = SubElement(content, "chunk")
            ce.set("index", str(i))
            ce.set("start", str(ch["metadata"]["chunk_start"]))
            ce.set("end", str(ch["metadata"]["chunk_end"]))
            ce.set("length", str(ch["metadata"]["chunk_length"]))
            ce.text = ch["text"]

        return doc

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
            "total_chunks": 0,
            "programs": set(),
            "types": set(),
            "levels": set(),
            "start_time": datetime.now(),
            "errors": [],
            "files_created": [],
        }

        # Track entries by program/level; each value holds list of documents (url_info + text)
        content_buffers: Dict[str, Dict[str, Any]] = {}

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

                    # Prepare document entry (to be chunked later)
                    doc_entry = {
                        "url_info": url_info,
                        "text": result["text"],
                        "word_count": result["word_count"],
                        "char_count": result["char_count"],
                    }

                    # Get directory for this program/level
                    level_dir = self._get_level_directory(program, level)

                    # Create unique key for this program/level combination
                    # For main level, combine all programs into generic
                    if level == "main":
                        key = "generic_main"
                    else:
                        key = f"{program}_{level}"

                    if key not in content_buffers:
                        content_buffers[key] = {
                            "program": "GENERIC" if level == "main" else program,
                            "level": "main" if level == "main" else level,
                            "directory": level_dir,
                            "documents": [],
                        }

                    # Add document to buffer
                    content_buffers[key]["documents"].append(doc_entry)

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

        # Write content to XML files
        print("\nWriting XML content to hierarchical files...")
        for key, buffer_data in content_buffers.items():
            file_path = os.path.join(buffer_data["directory"], "content.xml")

            # Build XML root for this level
            root = Element("iitm_bs_xplore_level")
            root.set("generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            root.set("program", buffer_data["program"])
            root.set("level", buffer_data["level"])
            root.set("chunk_size", str(self.chunk_size))
            root.set("chunk_overlap", str(self.chunk_overlap))

            # Add each document as child
            for doc in buffer_data["documents"]:
                url_info = dict(doc["url_info"])  # copy
                # Ensure program/level in url_info reflect buffer
                url_info["program"] = buffer_data["program"]
                url_info["level"] = buffer_data["level"]

                metadata = {
                    "url": url_info["url"],
                    "program": url_info.get("program"),
                    "type": url_info.get("type"),
                    "level": url_info.get("level"),
                    "label": url_info.get("label"),
                    "word_count": doc["word_count"],
                    "char_count": doc["char_count"],
                }

                chunks = self._chunk_text(doc["text"], metadata)
                stats["total_chunks"] += len(chunks)
                root.append(self._create_xml_document(chunks, url_info))

            # Add simple statistics element
            stats_elem = SubElement(root, "statistics")
            stats_elem.set("documents", str(len(buffer_data["documents"])))

            # Pretty print and write
            rough = tostring(root, encoding="unicode")
            xml_doc = minidom.parseString(rough).toprettyxml(indent="  ")
            lines = [ln for ln in xml_doc.split("\n") if ln.strip()]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            stats["files_created"].append(file_path)
            print(f"  ✓ Created: {file_path}")

        # Finalize statistics
        stats["end_time"] = datetime.now()
        stats["duration"] = stats["end_time"] - stats["start_time"]
        stats["programs"] = list(stats["programs"])
        stats["types"] = list(stats["types"])
        stats["levels"] = list(stats["levels"])

        print(f"\nHierarchical XML aggregation complete!")
        print(f"Files created: {len(stats['files_created'])}")
        print(f"Successful: {stats['successful']}/{stats['total_urls']}")
        print(f"Total words: {stats['total_words']:,}")
        print(f"Total characters: {stats['total_characters']:,}")
        print(f"Total chunks: {stats['total_chunks']:,}")

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
    programs: List[str],
    output_dir: str = "outputs",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Dict[str, Any]:
    """
    Convenience function to aggregate text from multiple programs hierarchically.

    Args:
        programs: List of program types (e.g., ['ds', 'es'])
        output_dir: Output directory

    Returns:
        Dictionary with aggregation statistics
    """
    aggregator = HierarchicalTextAggregator(output_dir, chunk_size, chunk_overlap)
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
