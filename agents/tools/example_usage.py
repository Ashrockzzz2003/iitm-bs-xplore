"""Example usage of the file search query tool."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.tools.file_search_query import query_pdf


def example_usage():
    """Example of how to use the file search query tool."""
    
    # Example 1: Query the student handbook using shorthand name
    print("Querying student handbook...")
    query = "What are the eligibility criteria for the qualifier exam?"
    result = query_pdf(query, pdf_path="student_handbook")
    
    print(f"\nQuery: {query}")
    print(f"\nResponse:\n{result['response']}")
    
    if result['sources']:
        print(f"\nSources:")
        for source in result['sources']:
            print(f"  - {source['title']}")
    else:
        print("\nNo grounding sources found")
    
    # Example 2: Query the grading document
    print("\n" + "="*50)
    query2 = "What are the assignment deadlines?"
    result2 = query_pdf(query2, pdf_path="grading_doc")
    
    print(f"\nQuery: {query2}")
    print(f"\nResponse:\n{result2['response']}")
    
    if result2['sources']:
        print(f"\nSources:")
        for source in result2['sources']:
            print(f"  - {source['title']}")
    
    # Example 3: Query with explicit store name
    print("\n" + "="*50)
    query3 = "What are the hardware requirements for the program?"
    # If you know the store_name, you can pass it directly
    # result3 = query_pdf(query3, store_name="your-store-name")
    # Or use the default student handbook
    result3 = query_pdf(query3, pdf_path="student_handbook")
    
    print(f"\nQuery: {query3}")
    print(f"\nResponse:\n{result3['response']}")


if __name__ == "__main__":
    example_usage()

