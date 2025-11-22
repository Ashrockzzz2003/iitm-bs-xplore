import psycopg
import requests
from config import FIRECRAWL_API_KEY, DB_CONNECTION_STR

from util.course import get_course_listings, save_course_to_db, save_wip_course_to_db, extract_course_code_from_url, CoursePageSchema

def scrape_course_page(url: str) -> dict:
    """
    Scrapes a single course page using Firecrawl REST API.
    Returns the response data or None if the page returns 404 (WIP).
    """
    api_url = "https://api.firecrawl.dev/v2/scrape"
    
    payload = {
        "url": url,
        "onlyMainContent": False,
        "maxAge": 172800000,
        "parsers": [],
        "formats": [
            {
                "type": "json",
                "schema": {
                    "type": "object",
                    "properties": {
                        "course_code": {
                            "type": "string",
                            "description": "The course ID, e.g., BSMA1001"
                        },
                        "title": {
                            "type": "string",
                            "description": "The full name of the course"
                        },
                        "description": {
                            "type": "string",
                            "description": "The main paragraph describing what the course is about"
                        },
                        "credits": {
                            "type": "integer",
                            "description": "Number of credits"
                        },
                        "level": {
                            "type": "string",
                            "description": "The academic level (e.g., Foundational, Diploma, Degree)"
                        },
                        "prerequisites": {
                            "type": "string",
                            "description": "Prerequisite courses or knowledge required"
                        },
                        "video_link": {
                            "type": "string",
                            "description": "URL to the course introductory video"
                        },
                        "instructors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    },
                                    "bio": {
                                        "type": "string"
                                    },
                                    "designation": {
                                        "type": "string"
                                    },
                                    "profile_link": {
                                        "type": "string"
                                    }
                                },
                                "required": ["name"]
                            }
                        },
                        "learning_outcomes": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of bullet points under 'What you'll learn'"
                        },
                        "syllabus": {
                            "type": "array",
                            "description": "Weekly breakdown of the course",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "week_number": {
                                        "type": "integer"
                                    },
                                    "title": {
                                        "type": "string"
                                    },
                                    "topics": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        }
                                    }
                                },
                                "required": ["week_number"]
                            }
                        },
                        "assessment_structure": {
                            "type": "string",
                            "description": "Textual description of how the course is graded (assignments, exams)"
                        },
                        "resources_and_books": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string"
                                    },
                                    "author": {
                                        "type": "string"
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "e.g., 'Prescribed Book' or 'Reference'"
                                    },
                                    "link": {
                                        "type": "string"
                                    }
                                },
                                "required": ["title"]
                            }
                        },
                        "extra": {
                            "type": "object",
                            "description": "A catch-all object for any other relevant info found on the page (e.g. support emails, exam dates, software requirements) that does not fit the other fields."
                        }
                    },
                    "required": ["course_code", "title", "syllabus", "instructors"]
                }
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response and e.response.status_code == 404:
            # Page not found - course is WIP
            return None
        else:
            # Re-raise other HTTP errors
            raise

def main():
    # 1. Get the list of courses and their levels
    course_list = get_course_listings()

    if not course_list:
        print("No courses found. Exiting.")
        return

    # Connect to DB
    try:
        with psycopg.connect(DB_CONNECTION_STR) as conn:
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
                        
                        # Save WIP course to database
                        with conn.cursor() as cursor:
                            save_wip_course_to_db(cursor, course_code, listing_level, url)
                        
                        conn.commit()
                        print(f"  ✓ Saved WIP course: {course_code}")
                        continue
                    
                    # Firecrawl API response structure: {"success": True, "data": {"json": {"data": {...}}}}
                    # Extract the JSON format result
                    extracted_json = None
                    if "data" in data:
                        if "json" in data["data"]:
                            if "data" in data["data"]["json"]:
                                extracted_json = data["data"]["json"]["data"]
                            else:
                                extracted_json = data["data"]["json"]
                        else:
                            extracted_json = data["data"]
                    elif "json" in data:
                        if "data" in data["json"]:
                            extracted_json = data["json"]["data"]
                        else:
                            extracted_json = data["json"]
                    else:
                        extracted_json = data
                    
                    if extracted_json is None:
                        print(f"  → Unexpected response structure for {url}: {data}")
                        continue
                    
                    course_data = CoursePageSchema(**extracted_json)

                    # Logic: Prioritize the Level found on the listing page (Step 1)
                    final_level = listing_level if listing_level else course_data.level

                    # Insert into DB (transaction is committed automatically when 'with' block exits)
                    with conn.cursor() as cursor:
                        save_course_to_db(cursor, course_data, final_level, url)
                    
                    # Commit after each successful course save
                    conn.commit()
                    print(f"  ✓ Successfully saved {course_data.course_code}")

                except Exception as e:
                    print(f"  ✗ Error processing {url}: {e}")
                    conn.rollback()
            
            print("All done.")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

if __name__ == "__main__":
    main()