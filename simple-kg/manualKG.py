import os
from Neo4jKG import Neo4jKG
from dotenv import load_dotenv

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def main():
    kg = Neo4jKG(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    kg.clear_database()

    kg.create_level("Foundation", 32)
    kg.create_level("Diploma in Programming", 27)
    kg.create_level("Diploma in Data Science", 27)
    kg.create_level("BSc Degree", 28)
    kg.create_level("BS Degree", 28)
    kg.create_level("PG Diploma", 20)
    kg.create_level("M.Tech", 20)

    kg.add_progression("Foundation", "Diploma in Programming")
    kg.add_progression("Foundation", "Diploma in Data Science")
    kg.add_progression("Diploma in Programming", "BSc Degree")
    kg.add_progression("Diploma in Data Science", "BSc Degree")
    kg.add_progression("BSc Degree", "BS Degree")
    kg.add_progression("BS Degree", "PG Diploma")
    kg.add_progression("PG Diploma", "M.Tech")

    kg.create_course("BSMA1001", "Mathematics for Data Science I", 4, "https://study.iitm.ac.in/ds/course_pages/BSMA1001.html")
    kg.link_level_course("Foundation", "BSMA1001", mandatory=True)

    kg.create_course("BSMA1002", "Statistics for Data Science I", 4,"https://study.iitm.ac.in/ds/course_pages/BSMA1002.html")
    kg.link_level_course("Foundation", "BSMA1002", mandatory=True)

    kg.create_course("BSCS1001", "Computational Thinking", 4,"https://study.iitm.ac.in/ds/course_pages/BSCS1001.html")
    kg.link_level_course("Foundation", "BSCS1001", mandatory=True)

    kg.create_course("BSHS1001", "English I", 4,"https://study.iitm.ac.in/ds/course_pages/BSHS1001.html")
    kg.link_level_course("Foundation", "BSHS1001", mandatory=True)

    kg.create_course("BSMA1003", "Mathematics for Data Science II", 4, "https://study.iitm.ac.in/ds/course_pages/BSMA1003.html")
    kg.link_level_course("Foundation", "BSMA1003", mandatory=True)
    kg.add_prerequisite("BSMA1003", "BSMA1001")

    kg.create_course("BSMA1004", "Statistics for Data Science II", 4,"https://study.iitm.ac.in/ds/course_pages/BSMA1004.html")
    kg.link_level_course("Foundation", "BSMA1004", mandatory=True)
    kg.add_prerequisite("BSMA1004", "BSMA1001")
    kg.add_prerequisite("BSMA1004", "BSMA1002")
    kg.add_corequisite("BSMA1004", "BSMA1003")

    kg.create_course("BSCS1002", "Programming in Python", 4, "https://study.iitm.ac.in/ds/course_pages/BSCS1002.html")
    kg.link_level_course("Foundation", "BSCS1002", mandatory=True)
    kg.add_prerequisite("BSCS1002", "BSCS1001")

    kg.create_course("BSHS1002", "English II", 4, "https://study.iitm.ac.in/ds/course_pages/BSHS1002.html")
    kg.link_level_course("Foundation", "BSHS1002", mandatory=True)
    kg.add_prerequisite("BSHS1002", "BSHS1001")

    kg.close()

def print_courses_by_level(level_name: str):
    kg = Neo4jKG(uri=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    kg.print_courses_by_level(level_name)
    kg.close()

if __name__ == "__main__":
    print("Creating KG manually")
    main()
    print("KG created")

    print_courses_by_level("Foundation")