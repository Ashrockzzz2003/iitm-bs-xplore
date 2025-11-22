import os
from typing import List
from pydantic import BaseModel, Field
from config import COURSE_LISTING_URL


# --- Schema for the Listing Page ---
class CourseLink(BaseModel):
    url: str = Field(
        ...,
        description="The absolute URL to the course detail page (e.g., .../BSMA1001.html)",
    )
    level: str = Field(
        ...,
        description="The academic level under which this course is listed, e.g., 'Foundation Level', 'Diploma Level', 'BSc Degree Level'",
    )


class CourseListingPage(BaseModel):
    courses: List[CourseLink]


def get_course_links_with_levels():
    """
    Parse courses from the academics.html file using custom HTML parser.

    Returns:
        List of dictionaries with 'url' and 'level' keys
    """
    # Import here to avoid circular import
    from .html_parser import parse_academics_html

    # Get the path to the HTML file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.dirname(current_dir)
    html_file_path = os.path.join(data_dir, "dump", "academics.html")

    if not os.path.exists(html_file_path):
        print(f"Error: HTML file not found at {html_file_path}")
        return []

    print(f"Scanning listing page: {html_file_path}...")

    try:
        courses = parse_academics_html(
            html_file_path,
            base_url=COURSE_LISTING_URL.replace("/academics.html#AC1", ""),
        )
        return [course.dict() for course in courses]
    except Exception as e:
        print(f"Error parsing course listings: {e}")
        import traceback

        traceback.print_exc()
        return []


# if __name__ == "__main__":
#     courses = get_course_links_with_levels()

#     print(f"Found {len(courses)} courses via AI extraction:")
#     for c in courses:
#         print(f"[{c['level']}] {c['url']}")

#     # Save for the next step
#     with open("course_links_dynamic.json", "w") as f:
#         # Convert Pydantic models to dict
#         json.dump([c.dict() for c in courses], f, indent=2)
