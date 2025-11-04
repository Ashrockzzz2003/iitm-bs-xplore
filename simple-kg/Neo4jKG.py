from neo4j import GraphDatabase
import json

# --- Neo4j Connection Setup ---
class Neo4jKG:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    # Utility function to run Cypher queries safely
    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [r.data() for r in result]

# --- Create Nodes ---
    def create_level(self, name, credits_required):
        query = """
        MERGE (l:Level {name: $name})
        SET l.credits_required = $credits_required
        RETURN l
        """
        return self.run_query(query, {"name": name, "credits_required": credits_required})

    def create_course(self, code, name, credits, details_link, meta_data=None):
        """
        Creates or updates a Course node with optional metadata (stored as JSON string).
        """
        query = """
        MERGE (c:Course {code: $code})
        SET c.name = $name,
            c.credits = $credits,
            c.details_link = $details_link,
            c.meta_data = $meta_data
        RETURN c
        """
        meta_json = json.dumps(meta_data or {}, ensure_ascii=False)
        return self.run_query(
            query,
            {
                "code": code,
                "name": name,
                "credits": credits,
                "details_link": details_link,
                "meta_data": meta_json,
            },
        )

    # --- Create Relationships ---
    def link_level_course(self, level_name, course_code, mandatory, path=None):
        query = """
        MATCH (l:Level {name: $level_name})
        MATCH (c:Course {code: $course_code})
        MERGE (l)-[r:HAS_COURSE]->(c)
        SET r.mandatory = $mandatory,
            r.path = $path
        RETURN l, r, c
        """
        return self.run_query(query, {
            "level_name": level_name,
            "course_code": course_code,
            "mandatory": mandatory,
            "path": path
        })

    def add_prerequisite(self, course_code, prereq_code):
        query = """
        MATCH (c1:Course {code: $course_code})
        MATCH (c2:Course {code: $prereq_code})
        MERGE (c1)-[:HAS_PREREQUISITE]->(c2)
        RETURN c1, c2
        """
        return self.run_query(query, {"course_code": course_code, "prereq_code": prereq_code})

    def add_corequisite(self, course_code, coreq_code):
        query = """
        MATCH (c1:Course {code: $course_code})
        MATCH (c2:Course {code: $coreq_code})
        MERGE (c1)-[:HAS_COREQUISITE]->(c2)
        RETURN c1, c2
        """
        return self.run_query(query, {"course_code": course_code, "coreq_code": coreq_code})

    def add_progression(self, from_level, to_level):
        query = """
        MATCH (l1:Level {name: $from_level})
        MATCH (l2:Level {name: $to_level})
        MERGE (l1)-[:PROGRESS_TO]->(l2)
        RETURN l1, l2
        """
        return self.run_query(query, {"from_level": from_level, "to_level": to_level})

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    import json

    def print_courses_by_level(self, level_name: str):
        """
        Prints all courses in a given level with their prerequisites, corequisites, and metadata.
        """
        query = """
        MATCH (l:Level {name: $level_name})-[:HAS_COURSE]->(c:Course)
        OPTIONAL MATCH (c)-[:HAS_PREREQUISITE]->(p:Course)
        OPTIONAL MATCH (c)-[:HAS_COREQUISITE]->(co:Course)
        RETURN c.code AS code,
               c.name AS name,
               c.credits AS credits,
               c.details_link AS link,
               c.meta_data AS meta_data,
               collect(DISTINCT p.code) AS prerequisites,
               collect(DISTINCT co.code) AS corequisites
        ORDER BY c.code
        """

        results = self.run_query(query, {"level_name": level_name})

        if not results:
            print(f"⚠️ No courses found for level '{level_name}'")
            return

        print(f"\n📘 Courses in '{level_name}' level:")
        print("=" * (len(level_name) + 22))

        for record in results:
            code = record.get("code")
            name = record.get("name")
            credits = record.get("credits")
            prereqs = [p for p in record.get("prerequisites", []) if p]
            coreqs = [c for c in record.get("corequisites", []) if c]

            # --- 🧠 Parse metadata (stored as JSON string)
            meta_data_raw = record.get("meta_data")
            meta_info = None
            if meta_data_raw:
                try:
                    meta_info = json.loads(meta_data_raw)
                except Exception:
                    meta_info = meta_data_raw  # fallback if not valid JSON

            # --- 🎨 Print
            print(f"\n🎓 {code}: {name} ({credits} credits)")
            print(f"🔗 Link: {record.get('link')}")
            if meta_info:
                if isinstance(meta_info, dict):
                    formatted_meta = ", ".join(f"{k}: {v}" for k, v in meta_info.items())
                    print(f"🏷️  Meta: {formatted_meta}")
                else:
                    print(f"🏷️  Meta: {meta_info}")
            else:
                print(f"🏷️  Meta: None")

            print(f"   Prerequisites: {', '.join(prereqs) if prereqs else 'None'}")
            print(f"   Corequisites:  {', '.join(coreqs) if coreqs else 'None'}")

        print("\n✅ Done.")


