"""
Content Categorization Utility

Categorizes website content as either course-specific or generic based on URL patterns.
This helps separate course-related content from general website information.
"""

import logging
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_titles_from_html(html: str) -> List[Dict[str, str]]:
    """Extract all titles and headings from HTML content.
    
    Args:
        html: HTML content to extract titles from
        
    Returns:
        List of dictionaries containing title text and context
    """
    soup = BeautifulSoup(html, 'lxml')
    titles = []
    
    # Extract from various heading elements
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        title_text = tag.get_text(strip=True)
        if title_text and len(title_text) > 3:  # Filter out very short titles
            titles.append({
                'text': title_text,
                'tag': tag.name,
                'context': 'heading'
            })
    
    # Extract from title tags and meta descriptions
    if soup.title and soup.title.string:
        title_text = soup.title.string.strip()
        if title_text:
            titles.append({
                'text': title_text,
                'tag': 'title',
                'context': 'page_title'
            })
    
    # Extract from elements with common title classes
    for selector in ['.title', '.page-title', '.content-title', '.section-title', '.course-title']:
        for element in soup.select(selector):
            title_text = element.get_text(strip=True)
            if title_text and len(title_text) > 3:
                titles.append({
                    'text': title_text,
                    'tag': element.name,
                    'context': 'class_based'
                })
    
    # Extract from table headers that might contain course information
    for table in soup.find_all('table'):
        for th in table.find_all('th'):
            title_text = th.get_text(strip=True)
            if title_text and len(title_text) > 3:
                titles.append({
                    'text': title_text,
                    'tag': 'th',
                    'context': 'table_header'
                })
    
    # Remove duplicates while preserving order
    seen = set()
    unique_titles = []
    for title in titles:
        if title['text'] not in seen:
            seen.add(title['text'])
            unique_titles.append(title)
    
    return unique_titles






def categorize_url_content(url: str, html: str) -> Tuple[Dict[str, List[Dict[str, str]]], str]:
    """Categorize content from a URL as course-specific or generic.
    
    Args:
        url: Source URL
        html: HTML content from the URL
        
    Returns:
        Tuple of (categorization_result, category_type)
        category_type is either 'course', 'generic', or 'mixed'
    """
    logger.info(f"Categorizing content from URL: {url}")
    
    # Extract titles from HTML
    titles = extract_titles_from_html(html)
    logger.info(f"Extracted {len(titles)} titles from HTML")
    
    if not titles:
        logger.warning("No titles found in HTML content")
        return {'course': [], 'generic': []}, 'generic'
    
    # For academics pages, categorize titles as both course and generic content
    if '/academics' in url.lower():
        logger.info("Detected academics page - categorizing content")
        course_titles = []
        generic_titles = []
        
        for title in titles:
            title_text = title['text'].lower()
            
            # Course-specific keywords
            course_keywords = {
                'course', 'curriculum', 'syllabus', 'academic', 'program', 'degree', 'diploma',
                'foundation', 'prerequisite', 'credit', 'semester', 'module', 'lesson',
                'learning', 'outcome', 'objective', 'assessment', 'evaluation', 'exam',
                'assignment', 'project', 'lab', 'practical', 'theory', 'tutorial',
                'instructor', 'professor', 'faculty', 'department', 'school', 'college',
                'university', 'institute', 'education', 'study', 'student', 'enrollment',
                'admission', 'registration', 'schedule', 'timetable', 'calendar'
            }
            
            # Check for course codes
            import re
            course_code_pattern = re.compile(r'\b[A-Z]{2,4}\s?-?\d{3,4}\b')
            has_course_code = course_code_pattern.search(title['text'])
            
            # Check for course keywords
            has_course_keywords = any(keyword in title_text for keyword in course_keywords)
            
            if has_course_code or has_course_keywords:
                course_titles.append({'text': title['text'], 'reason': 'Contains course-related content'})
            else:
                generic_titles.append({'text': title['text'], 'reason': 'General page content'})
        
        return {'course': course_titles, 'generic': generic_titles}, 'mixed'
    
    # For course pages, always treat as course content
    if '/course' in url.lower():
        logger.info("Detected course page - treating as course content")
        course_titles = [{'text': title['text'], 'reason': 'Course page - course content'} for title in titles]
        return {'course': course_titles, 'generic': []}, 'course'
    
    # For other pages, treat as generic content
    logger.info("Treating as generic content")
    generic_titles = [{'text': title['text'], 'reason': 'Generic page content'} for title in titles]
    return {'course': [], 'generic': generic_titles}, 'generic'


def get_course_specific_titles(categorization: Dict[str, List[Dict[str, str]]]) -> List[str]:
    """Extract just the text of course-specific titles.
    
    Args:
        categorization: Result from categorize_content_with_llm
        
    Returns:
        List of course-specific title texts
    """
    return [item['text'] for item in categorization.get('course', [])]


def get_generic_titles(categorization: Dict[str, List[Dict[str, str]]]) -> List[str]:
    """Extract just the text of generic titles.
    
    Args:
        categorization: Result from categorize_content_with_llm
        
    Returns:
        List of generic title texts
    """
    return [item['text'] for item in categorization.get('generic', [])]
