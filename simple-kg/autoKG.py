import os
from Neo4jKG import Neo4jKG
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

BASE_URL = "https://study.iitm.ac.in/ds/"

def extract_foundation_courses(kg):
    print("🔍 Fetching Foundation Level courses from IITM site...")
    url = urljoin(BASE_URL, "academics.html#AC11")
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the header that says "Foundation Level"
    foundation_header = soup.find("p", id="AC11")
    if not foundation_header:
        raise ValueError("Could not find Foundation Level section in HTML")

    # Find the next table after the Foundation header
    table = foundation_header.find_next("table")
    if not table:
        raise ValueError("Could not find course table under Foundation Level section")

    courses = []
    for row in table.find("tbody").find_all("tr"):
        # skip empty placeholder rows
        if not row.get("data-url"):
            continue

        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        course_name = cols[0].get_text(strip=True)
        credits_text = cols[1].get_text(strip=True)
        code = cols[2].get_text(strip=True)
        prereq = cols[3].get_text(strip=True)
        coreq = cols[4].get_text(strip=True)
        link = urljoin(BASE_URL, row["data-url"])

        credits = None
        try:
            credits = int(credits_text)
        except ValueError:
            credits = None

        courses.append({
            "code": code,
            "name": course_name,
            "credits": credits,
            "link": link,
            "prereq": prereq,
            "coreq": coreq,
        })

    print(f"✅ Found {len(courses)} Foundation courses.")
    for c in courses:
        print(f"- {c['code']}: {c['name']} ({c['credits']} credits)")

    # Populate Neo4j
    for c in courses:
        kg.create_course(c["code"], c["name"], c["credits"], c["link"])
        kg.link_level_course("Foundation", c["code"], mandatory=True)

        # Handle prerequisites if they exist
        if c["prereq"].lower() not in ["none", "nil", "-"]:
            for p in c["prereq"].split(","):
                prereq_code = p.strip().split()[-1]  # crude fallback, refine later
                kg.add_prerequisite(c["code"], prereq_code)

        # Handle corequisites if they exist
        if c["coreq"].lower() not in ["none", "nil", "-"]:
            for co in c["coreq"].split(","):
                coreq_code = co.strip().split()[-1]
                kg.add_corequisite(c["code"], coreq_code)

    print("✅ Foundation Level courses loaded into Neo4j.")

def extract_diploma_programming_courses(kg):
    print("🔍 Fetching Diploma in Programming courses from IITM site...")
    url = urljoin(BASE_URL, "academics.html#AC13")
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Locate "Courses for Diploma in Programming" header
    diploma_header = soup.find("p", string=lambda s: s and "Courses for Diploma in Programming" in s)
    if not diploma_header:
        raise ValueError("❌ Could not find 'Courses for Diploma in Programming' section on the page.")

    table = diploma_header.find_next("table")
    if not table:
        raise ValueError("❌ Could not find course table under Diploma in Programming section.")

    courses = []

    for row in table.find("tbody").find_all("tr"):
        # Skip empty rows
        if not row.get("data-url"):
            continue

        cols = row.find_all("td")
        if len(cols) < 5:
            continue  # not enough columns, skip

        # --- 🧩 Extract metadata (badges like PROJECT / LAB) ---
        badge = cols[0].find("span", class_="badge")
        meta_data = {}
        if badge:
            badge_text = badge.get_text(strip=True)
            meta_data["type"] = badge_text
            course_name = cols[0].get_text(strip=True).replace(badge_text, "").strip(" -")
        else:
            course_name = cols[0].get_text(strip=True)

        credits_text = cols[1].get_text(strip=True)
        code = cols[2].get_text(strip=True)
        prereq = cols[3].get_text(strip=True)
        coreq = cols[4].get_text(strip=True)
        link = urljoin(BASE_URL, row["data-url"])

        # Clean "None" or empty strings
        prereq = None if prereq.lower() in ["none", "-", ""] else prereq
        coreq = None if coreq.lower() in ["none", "-", ""] else coreq

        try:
            credits = int(credits_text)
        except ValueError:
            credits = None

        courses.append({
            "code": code,
            "name": course_name,
            "credits": credits,
            "link": link,
            "prereq": prereq,
            "coreq": coreq,
            "meta_data": meta_data
        })

    print(f"✅ Found {len(courses)} Diploma in Programming courses.")
    for c in courses:
        type_str = f" ({c['meta_data'].get('type')})" if c["meta_data"] else ""
        prereq_str = f" → Prereq: {c['prereq']}" if c["prereq"] else ""
        coreq_str = f" | Coreq: {c['coreq']}" if c["coreq"] else ""
        print(f"- {c['code']}: {c['name']}{type_str} ({c['credits']} credits){prereq_str}{coreq_str}")

    # --- Load into Neo4j ---
    for c in courses:
        kg.create_course(c["code"], c["name"], c["credits"], c["link"], c["meta_data"])
        kg.link_level_course("Diploma in Programming", c["code"], mandatory=True)

        # Link prerequisites
        if c["prereq"]:
            prereqs = [p.strip() for p in c["prereq"].replace(",", " and ").split(" and ") if p.strip()]
            for prereq_code in prereqs:
                kg.add_prerequisite(c["code"], prereq_code)

        # Link corequisites
        if c["coreq"]:
            coreqs = [co.strip() for co in c["coreq"].replace(",", " and ").split(" and ") if co.strip()]
            for coreq_code in coreqs:
                kg.add_corequisite(c["code"], coreq_code)

    print("✅ Diploma in Programming courses loaded into Neo4j.")

def extract_diploma_data_science_courses(kg):
    """
    Scrapes IITM Data Science website for 'Diploma in Data Science Pathway' courses,
    including badges like PROJECT, OPTION 2, etc., and loads them into Neo4j.
    """
    print("🔍 Fetching Diploma in Data Science courses from IITM site...")
    url = urljoin(BASE_URL, "academics.html#AC12")
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the <p> header for 'Diploma in Data Science Pathway'
    data_sci_header = soup.find("p", string=lambda s: s and "Diploma in Data Science Pathway" in s)
    if not data_sci_header:
        raise ValueError("Could not find 'Diploma in Data Science Pathway' section in HTML")

    # Get the next table after the header
    table = data_sci_header.find_next("table")
    if not table:
        raise ValueError("Could not find course table under Diploma in Data Science section")

    courses = []
    for row in table.find("tbody").find_all("tr"):
        if not row.get("data-url"):
            continue  # skip placeholders

        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        # --- 🧠 Extract badges (can be before or after course name)
        badges = [b.get_text(strip=True) for b in cols[0].find_all("span", class_="badge")]
        meta_data = {}
        if badges:
            meta_data["tags"] = badges

        # Remove badge text from course name
        raw_text = cols[0].get_text(" ", strip=True)
        for badge in badges:
            raw_text = raw_text.replace(badge, "")
        course_name = raw_text.strip(" -")

        credits_text = cols[1].get_text(strip=True)
        code = cols[2].get_text(strip=True)
        prereq = cols[3].get_text(strip=True)
        coreq = cols[4].get_text(strip=True)
        link = urljoin(BASE_URL, row["data-url"])

        try:
            credits = int(credits_text)
        except ValueError:
            credits = None

        courses.append({
            "code": code,
            "name": course_name,
            "credits": credits,
            "link": link,
            "prereq": prereq,
            "coreq": coreq,
            "meta_data": meta_data
        })

    print(f"✅ Found {len(courses)} Diploma in Data Science courses.")
    for c in courses:
        badge_str = f" ({', '.join(c['meta_data']['tags'])})" if c["meta_data"] else ""
        print(f"- {c['code']}: {c['name']}{badge_str} ({c['credits']} credits)")

    # --- Load into Neo4j ---
    for c in courses:
        kg.create_course(c["code"], c["name"], c["credits"], c["link"], c["meta_data"])
        kg.link_level_course("Diploma in Data Science", c["code"], mandatory=True)

        # Prerequisites
        if c["prereq"].lower() not in ["none", "nil", "-"]:
            for p in c["prereq"].split(","):
                prereq_code = p.strip().split()[-1]
                kg.add_prerequisite(c["code"], prereq_code)

        # Corequisites
        if c["coreq"].lower() not in ["none", "nil", "-"]:
            for co in c["coreq"].split(","):
                coreq_code = co.strip().split()[-1]
                kg.add_corequisite(c["code"], coreq_code)

    print("✅ Diploma in Data Science courses loaded into Neo4j.")

def extract_degree_level_courses(kg):
    """
    Scrapes IITM Data Science website for 'BS/BSc Degree Level' elective courses
    and loads them into Neo4j for both 'BSc Degree Level' and 'BS Degree Level'.
    """
    print("🔍 Fetching Degree Level courses from IITM site...")
    url = urljoin(BASE_URL, "academics.html#AC16")
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find header for 'Elective Courses' under BS Degree Level
    degree_header = soup.find("p", string=lambda s: s and "Elective Courses" in s)
    if not degree_header:
        raise ValueError("Could not find 'Elective Courses' section under BS Degree Level")

    # Find the next <table>
    table = degree_header.find_next("table")
    if not table:
        raise ValueError("Could not find course table under BS Degree Level Elective Courses")

    courses = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        # --- 🧩 Extract course name, badges, and link ---
        link_tag = cols[0].find("a", href=True)
        course_link = urljoin(BASE_URL, link_tag["href"]) if link_tag else None

        # Extract text and remove badge text
        badges = [b.get_text(strip=True) for b in cols[0].find_all("span", class_="badge")]
        meta_data = {}
        if badges:
            meta_data["type"] = badges

        raw_text = cols[0].get_text(" ", strip=True)
        for badge in badges:
            raw_text = raw_text.replace(badge, "")
        course_name = raw_text.replace("\xa0", " ").strip(" -").strip()

        code = cols[1].get_text(strip=True)
        credits_text = cols[2].get_text(strip=True)

        try:
            credits = int(credits_text)
        except ValueError:
            credits = None

        courses.append({
            "code": code,
            "name": course_name,
            "credits": credits,
            "link": course_link,
            "meta_data": meta_data,
        })

    print(f"✅ Found {len(courses)} Degree Level elective courses.")
    for c in courses:
        tags = f" ({', '.join(c['meta_data'].get('tags', []))})" if c["meta_data"] else ""
        print(f"- {c['code']}: {c['name']}{tags} ({c['credits']} credits)")

    # --- Load into Neo4j ---
    for c in courses:
        kg.create_course(c["code"], c["name"], c["credits"], c["link"], c["meta_data"])

        # This level applies to BOTH BSc and BS Degree Levels
        kg.link_level_course("BSc Degree Level", c["code"], mandatory=False)
        kg.link_level_course("BS Degree Level", c["code"], mandatory=False)

    print("✅ Degree Level courses loaded into Neo4j for both BSc and BS Degree Levels.")

def extract_pg_diploma_courses_fixed(kg):
    """
    Robust extractor for PG Diploma courses.
    Restricts extraction to the container that starts at <p id="AC17"> (PG Diploma Level)
    and finds Core Courses and Elective Courses tables inside that container.
    """
    print("🔍 Fetching PG Diploma courses (robust) from IITM site...")
    url = urljoin(BASE_URL, "academics.html#AC17")
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the PG Diploma anchor
    pg_anchor = soup.find("p", id="AC17")
    if not pg_anchor:
        raise ValueError("Could not find PG Diploma anchor (id='AC17') on the page")

    # Find the containing block for this section.
    # The page usually uses a <div class="container-fluid ..."> around the section.
    container = pg_anchor.find_parent(lambda t: t.name == "div" and "container-fluid" in (t.get("class") or []))
    if container is None:
        # fallback: limit to next N siblings after anchor (safer than searching whole page)
        container = pg_anchor.find_next_sibling()
        if container is None:
            container = soup  # last resort - whole document

    def find_table_within_container(header_text):
        """
        Find a paragraph containing header_text within container and return the next table inside container.
        """
        header = container.find("p", string=lambda s: s and header_text in s)
        if not header:
            return None
        # Next table *after* header
        table = header.find_next("table")
        # ensure table is inside the same container; if not, return None
        if table and container in table.parents:
            return table
        return None

    core_table = find_table_within_container("Core Courses")
    elective_table = find_table_within_container("Elective Courses")

    all_courses = []

    def parse_table_rows(table, default_meta_type=None):
        rows = []
        if not table:
            return rows
        tbody = table.find("tbody")
        if not tbody:
            return rows
        for row in tbody.find_all("tr"):
            # Some rows are placeholders without data-url or without cells
            cols = row.find_all("td")
            if not cols or len(cols) < 3:
                continue

            # course link (if any)
            link_tag = cols[0].find("a", href=True)
            link = urljoin(BASE_URL, link_tag["href"]) if link_tag else None

            # Extract badges anywhere in the first cell
            badges = [b.get_text(strip=True) for b in cols[0].find_all("span", class_="badge")]
            meta_data = {}
            if badges:
                meta_data["tags"] = badges
            if default_meta_type:
                # Add/override type (e.g., CORE COURSE) while preserving tags
                meta_data.setdefault("type", default_meta_type)

            # Clean course name by removing badge texts
            raw_text = cols[0].get_text(" ", strip=True)
            for b in badges:
                raw_text = raw_text.replace(b, "")
            course_name = raw_text.replace("\xa0", " ").strip(" -").strip()

            # Different table ordering: some tables use Code then Credits; some use Credits then Code.
            # Use heuristics: if second column contains code-like string (letters+digits), treat as code.
            col1 = cols[1].get_text(strip=True)
            col2 = cols[2].get_text(strip=True) if len(cols) > 2 else ""

            # Decide which column is code vs credits
            # code pattern like BSCS2001, BSMA1001 etc.
            def looks_like_code(s):
                return bool(s) and any(ch.isalpha() for ch in s) and any(ch.isdigit() for ch in s)

            if looks_like_code(col1):
                code = col1
                credits_text = col2
            elif looks_like_code(col2):
                code = col2
                credits_text = col1
            else:
                # fallback: first non-empty after name
                code = col1 or col2
                credits_text = col2 or col1

            try:
                credits = int(credits_text)
            except Exception:
                # try to extract digits only
                import re
                m = re.search(r"\d+", credits_text or "")
                credits = int(m.group()) if m else None

            rows.append({
                "code": code.strip(),
                "name": course_name,
                "credits": credits,
                "link": link,
                "meta_data": meta_data
            })
        return rows

    # Parse core and elective tables (core courses marked mandatory)
    core_courses = parse_table_rows(core_table, default_meta_type="CORE COURSE")
    elective_courses = parse_table_rows(elective_table, default_meta_type="ELECTIVE COURSE")

    # Combine and de-dupe by course code (in case same course appears twice)
    combined = {}
    for c in core_courses + elective_courses:
        if not c["code"]:
            continue
        if c["code"] in combined:
            # merge meta_data (concat tags, prefer CORE type)
            existing = combined[c["code"]]
            # merge tags
            existing_tags = set(existing.get("meta_data", {}).get("tags", []))
            new_tags = set(c.get("meta_data", {}).get("tags", []))
            tags = list(existing_tags.union(new_tags))
            existing.setdefault("meta_data", {})["tags"] = tags
            # prefer CORE COURSE if any
            existing_type = existing["meta_data"].get("type")
            new_type = c["meta_data"].get("type")
            if new_type == "CORE COURSE" or existing_type is None:
                existing["meta_data"]["type"] = new_type
            # fill missing fields
            existing["name"] = existing["name"] or c["name"]
            existing["link"] = existing["link"] or c["link"]
            existing["credits"] = existing["credits"] or c["credits"]
        else:
            combined[c["code"]] = c

    all_courses = list(combined.values())

    print(f"✅ Found {len(all_courses)} PG Diploma courses (core + elective) in the PG container.")
    for c in all_courses:
        tags = ", ".join(c.get("meta_data", {}).get("tags", []))
        ttype = c.get("meta_data", {}).get("type")
        tag_part = f" [{tags}]" if tags else ""
        type_part = f" ({ttype})" if ttype else ""
        print(f"- {c['code']}: {c['name']}{tag_part}{type_part} — {c['credits']} credits")

    # Insert into Neo4j: core courses mandatory, electives not
    for c in all_courses:
        kg.create_course(c["code"], c["name"], c["credits"], c["link"], c.get("meta_data"))
        is_core = (c.get("meta_data", {}).get("type") == "CORE COURSE")
        kg.link_level_course("PG Diploma", c["code"], mandatory=is_core)

    print("✅ PG Diploma courses loaded into Neo4j (fixed extractor).")

def extract_mtech_courses(kg):
    """
    Scrapes IITM Data Science website for 'M.Tech Level' courses
    and loads them into Neo4j as core courses.
    """
    print("🔍 Fetching M.Tech Level courses from IITM site...")
    url = urljoin(BASE_URL, "academics.html#AC17")  # Page has no AC18, AC17 covers PG + MTech
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the <p> header for "MTech Level Courses"
    mtech_header = soup.find("p", string=lambda s: s and "MTech Level Courses" in s)
    if not mtech_header:
        raise ValueError("❌ Could not find 'MTech Level Courses' section in the HTML")

    # Find the next <table> after this header
    table = mtech_header.find_next("table")
    if not table:
        raise ValueError("❌ Could not find course table under MTech Level section")

    # --- Extract all course rows ---
    courses = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        # Extract link if present
        link_tag = cols[0].find("a", href=True)
        link = urljoin(BASE_URL, link_tag["href"]) if link_tag else None

        # Extract course details
        course_name = cols[0].get_text(" ", strip=True).replace("\xa0", " ").strip(" -")
        code = cols[1].get_text(strip=True)
        credits_text = cols[2].get_text(strip=True)

        try:
            credits = int(credits_text)
        except ValueError:
            credits = None

        meta_data = {"type": "CORE COURSE"}

        courses.append({
            "code": code,
            "name": course_name,
            "credits": credits,
            "link": link,
            "meta_data": meta_data
        })

    print(f"✅ Found {len(courses)} M.Tech core courses.")
    for c in courses:
        print(f"- {c['code']}: {c['name']} ({c['credits']} credits)")

    # --- Load into Neo4j ---
    for c in courses:
        kg.create_course(c["code"], c["name"], c["credits"], c["link"], c["meta_data"])
        kg.link_level_course("M.Tech", c["code"], mandatory=True)

    print("✅ M.Tech Level courses loaded into Neo4j.")


def main():
    kg = Neo4jKG(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    kg.clear_database()

    add_level_information(kg)
    extract_foundation_courses(kg)
    extract_diploma_programming_courses(kg)
    extract_diploma_data_science_courses(kg)
    extract_degree_level_courses(kg)
    extract_pg_diploma_courses_fixed(kg)
    extract_mtech_courses(kg)

    kg.close()
    print("🎉 KG created successfully from IITM site.")


def add_level_information(kg: Neo4jKG):
    kg.create_level("Foundation", 32)
    kg.create_level("Diploma in Programming", 27)
    kg.create_level("Diploma in Data Science", 27)
    kg.create_level("BSc Degree Level", 28)
    kg.create_level("BS Degree Level", 28)
    kg.create_level("PG Diploma", 20)
    kg.create_level("M.Tech", 20)

    kg.add_progression("Foundation", "Diploma in Programming")
    kg.add_progression("Foundation", "Diploma in Data Science")

    kg.add_progression("Diploma in Programming", "BSc Degree Level")
    kg.add_progression("Diploma in Data Science", "BSc Degree Level")

    kg.add_progression("BSc Degree Level", "BS Degree Level")

    kg.add_progression("BS Degree Level", "PG Diploma")

    kg.add_progression("PG Diploma", "M.Tech")

def print_courses_by_level(level_name: str):
    kg = Neo4jKG(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    kg.print_courses_by_level(level_name)
    kg.close()


if __name__ == "__main__":
    print("Creating KG manually")
    main()
    print("KG created")

    print_courses_by_level("Foundation")
    print_courses_by_level("Diploma in Programming")
    print_courses_by_level("Diploma in Data Science")
    print_courses_by_level("BSc Degree Level")
    print_courses_by_level("PG Diploma")
    print_courses_by_level("M.Tech")