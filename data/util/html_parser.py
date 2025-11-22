"""
Custom HTML parser to extract courses, URLs, and levels from academics.html
"""
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin
from .course import CourseLink


def parse_academics_html(html_file_path: str, base_url: str = "https://study.iitm.ac.in/ds/") -> List[CourseLink]:
    """
    Parse the academics.html file to extract courses with their URLs and levels.
    
    Args:
        html_file_path: Path to the academics.html file
        base_url: Base URL to construct absolute URLs (default: https://study.iitm.ac.in/ds/)
        
    Returns:
        List of CourseLink objects with url and level
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    courses = []
    
    # Find all section headers that define levels
    # These are typically h3 or p elements with IDs like AC11, AC12, AC15, AC16, AC17
    level_sections = soup.find_all(['h3', 'p'], {'id': lambda x: x and x.startswith('AC')})
    
    # Find all tables in the document
    all_tables = soup.find_all('table')
    
    # For each table, find the nearest level section before it
    for table in all_tables:
        level = _find_level_for_table(table, level_sections)
        if level:
            _extract_courses_from_table(table, level, base_url, courses)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_courses = []
    for course in courses:
        # Use (url, level) as the key to handle same course in different levels
        key = (course.url, course.level)
        if key not in seen:
            seen.add(key)
            unique_courses.append(course)
    
    return unique_courses


def _find_level_for_table(table, level_sections):
    """Find the level section that this table belongs to by finding the nearest level section before it."""
    # Find the nearest level section that comes before this table in the document
    for prev_elem in table.find_all_previous(['h3', 'p']):
        if prev_elem in level_sections:
            level_text = prev_elem.get_text(strip=True)
            if 'Foundation Level' in level_text:
                return 'Foundation Level'
            elif 'Diploma Level' in level_text and 'PG Diploma' not in level_text:
                return 'Diploma Level'
            elif 'BSc Degree Level' in level_text or 'BSc Level' in level_text:
                return 'BSc Degree Level'
            elif 'BS Degree Level' in level_text or 'BS Level' in level_text:
                return 'BS Degree Level'
            elif 'PG Diploma Level' in level_text:
                return 'PG Diploma Level'
            elif 'MTech Level' in level_text:
                return 'MTech Level'
    return None


def _extract_courses_from_table(table, level: str, base_url: str, courses: List):
    """Helper function to extract courses from a table."""
    rows = table.find_all('tr')
    
    for row in rows:
        # Method 1: Check for data-url attribute
        data_url = row.get('data-url')
        if data_url:
            # Construct absolute URL
            if data_url.startswith('http'):
                course_url = data_url
            else:
                course_url = urljoin(base_url, data_url)
            
            courses.append(CourseLink(
                url=course_url,
                level=level
            ))
            continue
        
        # Method 2: Check for <a> tags with course_pages links
        links = row.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            # Check if it's a course link
            if 'course_pages' in href or any(code in href for code in ['BSMA', 'BSCS', 'BSHS', 'BSDA', 'BSGN']):
                # Skip "coming-soon" links
                if 'coming-soon' in href:
                    continue
                
                # Construct absolute URL
                if href.startswith('http'):
                    course_url = href
                else:
                    course_url = urljoin(base_url, href)
                
                courses.append(CourseLink(
                    url=course_url,
                    level=level
                ))
                break  # Only take the first valid link per row
