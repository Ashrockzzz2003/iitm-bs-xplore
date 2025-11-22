import json
import os
import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from psycopg.types.json import Json
from config import COURSE_PREFIX, FIRECRAWL_API_KEY, COURSE_LISTING_URL

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

# --- Schema for Individual Course Pages (imported by app.py) ---
class Instructor(BaseModel):
    name: str
    bio: Optional[str] = None
    designation: Optional[str] = None
    profile_link: Optional[str] = None

class WeekSyllabus(BaseModel):
    week_number: int
    title: Optional[str] = None
    topics: List[str] = []

class Book(BaseModel):
    title: str
    author: Optional[str] = None
    type: Optional[str] = Field(None, description="e.g., Prescribed, Reference")
    link: Optional[str] = None

class CoursePageSchema(BaseModel):
    course_code: str = Field(..., description="The course ID, e.g., BSMA1001")
    title: str
    description: str
    credits: Optional[int]
    level: Optional[str] = Field(None, description="Foundational, Diploma, etc.")
    prerequisites: Optional[str]
    video_link: Optional[str] = Field(None, description="Link to course videos/intro")
    instructors: List[Instructor]
    learning_outcomes: List[str]
    syllabus: List[WeekSyllabus]
    assessment_structure: Optional[str]
    resources_and_books: List[Book]
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any other relevant information that does not fit into the fields above."
    )

def get_course_listings() -> List[CourseLink]:
    """
    Parse courses from the course listing page using custom HTML parser.
    
    Args:
        None
        
    Returns:
        List of CourseLink objects with url and level
    """
    # Import here to avoid circular import
    from .html_parser import parse_academics_html
    
    # Get the path to the HTML file
    # Assuming the HTML file is in dump/academics.html relative to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.dirname(current_dir)
    html_file_path = os.path.join(data_dir, "dump", "academics.html")
    
    if not os.path.exists(html_file_path):
        print(f"Error: HTML file not found at {html_file_path}")
        return []
    
    print(f"--- Step 1: Extracting Course List & Levels from {html_file_path} ---")
    courses = parse_academics_html(html_file_path, base_url=COURSE_PREFIX)
    print(f"Found {len(courses)} courses.")
    return courses

def extract_course_code_from_url(url: str) -> str:
    """
    Extracts course code from URL.
    Example: https://study.iitm.ac.in/course_pages/BSMA1001.html -> BSMA1001
    """
    import re
    # Extract course code from URL (e.g., BSMA1001 from .../BSMA1001.html)
    match = re.search(r'/([A-Z0-9]+)\.html', url)
    if match:
        return match.group(1)
    # Fallback: try to extract from any part of the URL
    parts = url.split('/')
    for part in reversed(parts):
        if part and '.' in part:
            return part.split('.')[0].upper()
    return url.split('/')[-1].replace('.html', '').upper()

def save_wip_course_to_db(cursor, course_code: str, level: str, source_url: str):
    """
    Saves a WIP (Work In Progress) course to the database.
    This is used when a course page returns 404.
    """
    insert_query = """
        INSERT INTO courses (
            course_code, level, source_url, status
        ) VALUES (
            %s, %s, %s, 'wip'
        )
        ON CONFLICT (course_code) 
        DO UPDATE SET
            level = EXCLUDED.level,
            source_url = EXCLUDED.source_url,
            status = 'wip',
            last_updated = CURRENT_TIMESTAMP;
    """
    
    cursor.execute(insert_query, (course_code, level, source_url))

def save_course_to_db(cursor, course_data: CoursePageSchema, final_level: str, source_url: str):
    """
    Inserts or Updates the course data into PostgreSQL.
    """
    insert_query = """
        INSERT INTO courses (
            course_code, title, description, credits, level, prerequisites, 
            video_link, instructors, learning_outcomes, syllabus, 
            resources_and_books, assessment_structure, extra, source_url, status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, 
            %s, %s, %s, %s, 'active'
        )
        ON CONFLICT (course_code) 
        DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            level = EXCLUDED.level, 
            credits = EXCLUDED.credits,
            syllabus = EXCLUDED.syllabus,
            instructors = EXCLUDED.instructors,
            learning_outcomes = EXCLUDED.learning_outcomes,
            resources_and_books = EXCLUDED.resources_and_books,
            assessment_structure = EXCLUDED.assessment_structure,
            extra = EXCLUDED.extra,
            status = 'active',
            last_updated = CURRENT_TIMESTAMP;
    """

    cursor.execute(insert_query, (
        course_data.course_code,
        course_data.title,
        course_data.description,
        course_data.credits,
        final_level,
        course_data.prerequisites,
        course_data.video_link,
        Json([i.dict() for i in course_data.instructors]),
        Json(course_data.learning_outcomes),
        Json([w.dict() for w in course_data.syllabus]),
        Json([b.dict() for b in course_data.resources_and_books]),
        course_data.assessment_structure,
        Json(course_data.extra),
        source_url,
    ))