# kg_tools.py
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ----------------------------
# Neo4j setup
# ----------------------------
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# ----------------------------
# Tool: run_cypher_query
# ----------------------------
def run_cypher_query(cypher: str):
    """
    Executes a Cypher query on Neo4j and returns results as a list of dicts.
    """
    with driver.session() as session:
        try:
            result = session.run(cypher)
            return [record.data() for record in result]
        except Exception as e:
            return {"error": str(e), "query": cypher}

# ----------------------------
# Tool: fuzzy_search_courses
# ----------------------------
def fuzzy_search_courses(course_name: str, limit: int = 5):
    """
    Performs fuzzy search for courses using Neo4j fulltext index 'courseIndex'.
    Requires the index to exist:
    CREATE FULLTEXT INDEX courseIndex FOR (c:Course) ON EACH [c.name, c.code];
    """
    with driver.session() as session:
        try:
            cypher = """
            CALL db.index.fulltext.queryNodes('courseIndex', $query + '~')
            YIELD node, score
            RETURN node.code AS code, node.name AS name, score
            ORDER BY score DESC
            LIMIT $limit
            """
            results = session.run(cypher, {"query": course_name, "limit": limit})
            return [r.data() for r in results]
        except Exception as e:
            return {"error": str(e)}

def fuzzy_search_levels(level_name: str, limit: int = 5):
    """
    Performs fuzzy search for levels using Neo4j fulltext index 'levelIndex'.
    Requires the index to exist:
    CREATE FULLTEXT INDEX levelIndex FOR (l:Level) ON EACH [l.name];
    """
    with driver.session() as session:
        try:
            cypher = """
            CALL db.index.fulltext.queryNodes('levelIndex', $query + '~')
            YIELD node, score
            RETURN node.name AS level_name, node.credits_required AS credits, score
            ORDER BY score DESC
            LIMIT $limit
            """
            results = session.run(cypher, {"query": level_name, "limit": limit})
            return [r.data() for r in results]
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    print(fuzzy_search_levels("Degree level"))