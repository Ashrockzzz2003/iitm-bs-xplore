import psycopg
import json
import requests
import html2text
import sys
import os
from datetime import datetime
from google import genai
from google.genai.types import GenerateContentConfig
from config import GENAI_MODEL_ID, DB_CONNECTION_STR

from util.course import get_course_listings, save_course_to_db, save_wip_course_to_db, extract_course_code_from_url, CoursePageSchema
from util.file_search import initialize_all_pdfs

# Optional: Set LOG_FILE environment variable to enable file logging
# Example: LOG_FILE=logs/app.log python app.py
LOG_FILE = os.environ.get('LOG_FILE')
log_file_handle = None

class TeeOutput:
    """Writes to both stdout and a log file if enabled"""
    def __init__(self, *files):
        self.files = files
    
    def write(self, text):
        for f in self.files:
            f.write(text)
            f.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()

def setup_logging():
    """Optionally redirect stdout to both console and log file"""
    global log_file_handle
    if LOG_FILE:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Open log file in append mode
        log_file_handle = open(LOG_FILE, 'a', encoding='utf-8')
        
        # Create TeeOutput that writes to both stdout and log file
        sys.stdout = TeeOutput(sys.stdout, log_file_handle)
        sys.stderr = TeeOutput(sys.stderr, log_file_handle)
        
        # Write a separator with timestamp
        print(f"\n{'='*80}")
        print(f"Logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

def cleanup_logging():
    """Restore stdout and close log file"""
    global log_file_handle
    if log_file_handle:
        print(f"\n{'='*80}")
        print(f"Logging ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        log_file_handle.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

def scrape_course_page(url: str) -> dict:
    """
    Scrapes a single course page by fetching HTML, converting to text with html2text,
    and passing to Google Gemini AI for JSON extraction.
    Returns the extracted course data as a dict or None if the page returns 404 (WIP).
    """
    # Fetch HTML content
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Check for 404
        if response.status_code == 404:
            print(f"  → 404 detected for {url}")
            return None
            
        html_content = response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"  → 404 detected for {url}")
            return None
        raise
    except requests.exceptions.RequestException as e:
        print(f"  → Error fetching {url}: {e}")
        raise
    
    # Convert HTML to text using html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0  # Don't wrap lines
    course_text = h.handle(html_content)
    
    client = genai.Client()
    
    # Create a prompt that asks Gemini to extract course data in JSON format
    prompt = f"""Extract course information from the following course page content and return it as a JSON object with the following structure:

Course page content:
{course_text}

Extract the information and return it as a JSON object with the following structure:

{{
    "course_code": "The course ID, e.g., BSMA1001",
    "title": "The full name of the course",
    "description": "The main paragraph describing what the course is about",
    "credits": <integer> (Number of credits),
    "level": "The academic level (e.g., Foundational, Diploma, Degree)",
    "prerequisites": "Prerequisite courses or knowledge required",
    "video_link": "URL to the course introductory video",
    "instructors": [
        {{
            "name": "<required>",
            "bio": "optional",
            "designation": "optional",
            "profile_link": "optional"
        }}
    ],
    "learning_outcomes": ["List of bullet points under 'What you'll learn'"],
    "syllabus": [
        {{
            "week_number": <required integer>,
            "title": "optional",
            "topics": ["array of strings"]
        }}
    ],
    "assessment_structure": "Textual description of how the course is graded (assignments, exams)",
    "resources_and_books": [
        {{
            "title": "<required>",
            "author": "optional",
            "type": "e.g., 'Prescribed Book' or 'Reference'",
            "link": "optional"
        }}
    ],
    "extra": {{"Any other relevant information that does not fit into the fields above"}}
}}

Required fields: course_code, title, syllabus, instructors.
Return ONLY valid JSON, no markdown formatting or code blocks."""

    try:
        response = client.models.generate_content(
            model=GENAI_MODEL_ID,
            contents=prompt,
            config=GenerateContentConfig()
        )
        
        # Debug: Print response structure
        print(f"  [DEBUG] Response type: {type(response)}")
        print(f"  [DEBUG] Response has 'candidates' attribute: {hasattr(response, 'candidates')}")
        if hasattr(response, 'candidates'):
            print(f"  [DEBUG] Response.candidates type: {type(response.candidates)}")
            print(f"  [DEBUG] Response.candidates length: {len(response.candidates) if response.candidates else 'None'}")
            if response.candidates and len(response.candidates) > 0:
                print(f"  [DEBUG] response.candidates[0] type: {type(response.candidates[0])}")
                print(f"  [DEBUG] response.candidates[0] has 'content' attribute: {hasattr(response.candidates[0], 'content')}")
                if hasattr(response.candidates[0], 'content'):
                    print(f"  [DEBUG] response.candidates[0].content: {response.candidates[0].content}")
                    print(f"  [DEBUG] response.candidates[0].content type: {type(response.candidates[0].content)}")
                    if response.candidates[0].content:
                        print(f"  [DEBUG] response.candidates[0].content has 'parts' attribute: {hasattr(response.candidates[0].content, 'parts')}")
                        if hasattr(response.candidates[0].content, 'parts'):
                            print(f"  [DEBUG] response.candidates[0].content.parts: {response.candidates[0].content.parts}")
                            print(f"  [DEBUG] response.candidates[0].content.parts type: {type(response.candidates[0].content.parts)}")
                            if response.candidates[0].content.parts:
                                print(f"  [DEBUG] response.candidates[0].content.parts length: {len(response.candidates[0].content.parts)}")
        
        # Extract text from response
        response_text = ""
        if not hasattr(response, 'candidates') or not response.candidates:
            print(f"  [DEBUG] No candidates in response")
            return None
        
        if len(response.candidates) == 0:
            print(f"  [DEBUG] Empty candidates list")
            return None
        
        if not hasattr(response.candidates[0], 'content') or response.candidates[0].content is None:
            print(f"  [DEBUG] No content in first candidate")
            return None
        
        if not hasattr(response.candidates[0].content, 'parts') or response.candidates[0].content.parts is None:
            print(f"  [DEBUG] No parts in content")
            return None
        
        print(f"  [DEBUG] Iterating over {len(response.candidates[0].content.parts)} parts")
        for i, part in enumerate(response.candidates[0].content.parts):
            print(f"  [DEBUG] Part {i}: type={type(part)}, hasattr('text')={hasattr(part, 'text')}")
            if hasattr(part, 'text') and part.text:
                print(f"  [DEBUG] Part {i} text length: {len(part.text)}")
                response_text += part.text
        
        print(f"  [DEBUG] Extracted response_text length: {len(response_text)}")
        print(f"  [DEBUG] Response text preview (first 500 chars): {response_text[:500]}")
        
        # Check response text for 404 indicators
        if not response_text or '404' in response_text or 'page not found' in response_text.lower():
            print(f"  [DEBUG] 404 detected in response text or empty response")
            return None
        
        # Parse JSON from response
        # Remove markdown code blocks if present
        response_text_original = response_text
        response_text = response_text.strip()
        print(f"  [DEBUG] After strip: length={len(response_text)}")
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
            print(f"  [DEBUG] Removed ```json prefix")
        elif response_text.startswith("```"):
            response_text = response_text[3:]
            print(f"  [DEBUG] Removed ``` prefix")
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            print(f"  [DEBUG] Removed ``` suffix")
        response_text = response_text.strip()
        
        print(f"  [DEBUG] Final response_text length: {len(response_text)}")
        print(f"  [DEBUG] Final response_text (first 1000 chars): {response_text[:1000]}")
        
        if not response_text:
            print(f"  → Empty response for {url}")
            return None
        
        print(f"  [DEBUG] Attempting JSON parse...")
        extracted_data = json.loads(response_text)
        print(f"  [DEBUG] JSON parse successful, keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'N/A'}")
        return extracted_data
        
    except json.JSONDecodeError as e:
        print(f"  → JSON decode error for {url}: {e}")
        if 'response_text' in locals():
            print(f"  [DEBUG] Response text that failed to parse: {response_text[:1000]}...")
            print(f"  [DEBUG] Full response text length: {len(response_text)}")
        raise
    except Exception as e:
        print(f"  [DEBUG] Exception type: {type(e).__name__}")
        print(f"  [DEBUG] Exception message: {str(e)}")
        print(f"  [DEBUG] Exception args: {e.args}")
        import traceback
        print(f"  [DEBUG] Traceback:")
        traceback.print_exc()
        # Check if it's a 404 or page not found error
        error_str = str(e).lower()
        if '404' in error_str or 'not found' in error_str:
            print(f"  [DEBUG] 404 detected in error message, returning None")
            return None
        raise

def save_course_with_retry(conn, course_data, final_level, url, max_retries=3):
    """Save course to DB with retry logic for connection issues. Returns (success, new_conn)."""
    current_conn = conn
    for attempt in range(max_retries):
        try:
            with current_conn.cursor() as cursor:
                save_course_to_db(cursor, course_data, final_level, url)
            current_conn.commit()
            return (True, current_conn)
        except (psycopg.OperationalError, psycopg.InterfaceError) as e:
            if attempt < max_retries - 1:
                print(f"  → Database connection error (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"  → Reconnecting...")
                # Try to reconnect
                try:
                    current_conn.close()
                except:
                    pass
                current_conn = psycopg.connect(DB_CONNECTION_STR)
                print(f"  → Reconnected successfully")
            else:
                raise
    return (False, current_conn)

def save_wip_with_retry(conn, course_code, listing_level, url, max_retries=3):
    """Save WIP course to DB with retry logic for connection issues. Returns (success, new_conn)."""
    current_conn = conn
    for attempt in range(max_retries):
        try:
            with current_conn.cursor() as cursor:
                save_wip_course_to_db(cursor, course_code, listing_level, url)
            current_conn.commit()
            return (True, current_conn)
        except (psycopg.OperationalError, psycopg.InterfaceError) as e:
            if attempt < max_retries - 1:
                print(f"  → Database connection error (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"  → Reconnecting...")
                # Try to reconnect
                try:
                    current_conn.close()
                except:
                    pass
                current_conn = psycopg.connect(DB_CONNECTION_STR)
                print(f"  → Reconnected successfully")
            else:
                raise
    return (False, current_conn)

def main():
    # Setup optional file logging if LOG_FILE env var is set
    setup_logging()
    
    try:
        # 1. Get the list of courses and their levels
        course_list = get_course_listings()

        if not course_list:
            print("No courses found. Exiting.")
            return

        # Connect to DB
        conn = None
        try:
            conn = psycopg.connect(DB_CONNECTION_STR)
            print("Connected to Database.")
            
            print(f"--- Step 2: Crawling {len(course_list)} Course Detail Pages ---")

            for item in course_list:
                url = item.url
                listing_level = item.level

                print(f"Processing [{listing_level}]: {url}")

                try:
                    data = scrape_course_page(url)
                    
                    # Handle 404 - course page is WIP
                    if data is None:
                        # Extract course code from URL
                        course_code = extract_course_code_from_url(url)
                        print(f"  → Course page not found (404) - marking as WIP: {course_code}")
                        
                        # Save WIP course to database with retry
                        try:
                            success, conn = save_wip_with_retry(conn, course_code, listing_level, url)
                            if success:
                                print(f"  ✓ Saved WIP course: {course_code}")
                            else:
                                print(f"  ✗ Failed to save WIP course {course_code} after retries")
                        except Exception as db_error:
                            print(f"  ✗ Database error saving WIP course {course_code}: {db_error}")
                            # Try to reconnect for next iteration
                            try:
                                conn.close()
                            except:
                                pass
                            conn = psycopg.connect(DB_CONNECTION_STR)
                            print(f"  → Reconnected, continuing...")
                        continue
                    
                    # Gemini returns the extracted JSON directly
                    course_data = CoursePageSchema(**data)

                    # Logic: Prioritize the Level found on the listing page (Step 1)
                    final_level = listing_level if listing_level else course_data.level

                    # Insert into DB with retry logic
                    try:
                        success, conn = save_course_with_retry(conn, course_data, final_level, url)
                        if success:
                            print(f"  ✓ Successfully saved {course_data.course_code}")
                        else:
                            print(f"  ✗ Failed to save {course_data.course_code} after retries")
                    except Exception as db_error:
                        print(f"  ✗ Database error saving {course_data.course_code}: {db_error}")
                        # Try to reconnect for next iteration
                        try:
                            conn.close()
                        except:
                            pass
                        conn = psycopg.connect(DB_CONNECTION_STR)
                        print(f"  → Reconnected, continuing...")

                except Exception as e:
                    print(f"  ✗ Error processing {url}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't rollback here since we're committing after each course
                    # Just try to reconnect if it's a connection error
                    if isinstance(e, (psycopg.OperationalError, psycopg.InterfaceError)):
                        try:
                            conn.close()
                        except:
                            pass
                        try:
                            conn = psycopg.connect(DB_CONNECTION_STR)
                            print(f"  → Reconnected after error, continuing...")
                        except:
                            print(f"  ✗ Failed to reconnect. Exiting.")
                            return
            
            print("\n" + "="*80)
            print("Course processing completed.")
            print("="*80)
            
            # Step 3: Initialize file search stores for PDF documents
            print("\n" + "="*80)
            print("--- Step 3: Initializing File Search Stores for PDFs ---")
            print("="*80)
            try:
                initialize_all_pdfs()
                print("✓ File search store initialization completed!")
            except Exception as e:
                print(f"✗ Error initializing file search stores: {e}")
                import traceback
                traceback.print_exc()
                # Continue - don't fail the entire process
            
            print("\n" + "="*80)
            print("All done.")
            print("="*80)
        except Exception as e:
            print(f"Database connection failed: {e}")
            import traceback
            traceback.print_exc()
    finally:
        # Cleanup database connection
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except:
                pass
        # Cleanup logging
        cleanup_logging()

if __name__ == "__main__":
    main()