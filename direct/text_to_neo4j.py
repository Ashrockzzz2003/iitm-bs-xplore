#!/usr/bin/env python3
"""
Text to Neo4j Upload Module

Uploads text content to Neo4j as Document nodes for automatic
knowledge graph generation using Neo4j's NLP/AI features.
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase


class TextToNeo4jUploader:
    """Uploads text content to Neo4j as Document nodes."""
    
    def __init__(self, uri: str = "neo4j://127.0.0.1:7687", 
                 username: str = "neo4j", 
                 password: str = "password",
                 database: str = "neo4j"):
        """
        Initialize the Neo4j uploader.
        
        Args:
            uri: Neo4j URI
            username: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
    
    def connect(self) -> bool:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test connection
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            print(f"✓ Connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            return False
    
    def disconnect(self):
        """Close connection to Neo4j database."""
        if self.driver:
            self.driver.close()
            print("Disconnected from Neo4j")
    
    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
        
        with self.driver.session(database=self.database) as session:
            # Delete all relationships first
            session.run("MATCH ()-[r]->() DELETE r")
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            print("✓ Database cleared successfully")
    
    def parse_text_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse the combined text file and extract document sections.
        
        Args:
            file_path: Path to the combined text file
            
        Returns:
            List of document dictionaries
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")
        
        print(f"Parsing text file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content by URL separators
        sections = re.split(r'={40}\n', content)
        
        documents = []
        current_doc = None
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if this is a URL header section
            if section.startswith('URL: '):
                # Save previous document if exists
                if current_doc and current_doc.get('text'):
                    documents.append(current_doc)
                
                # Parse header information
                lines = section.split('\n')
                current_doc = {
                    'text': '',
                    'metadata': {}
                }
                
                for line in lines:
                    if line.startswith('URL: '):
                        current_doc['url'] = line[5:].strip()
                    elif line.startswith('PROGRAM: '):
                        current_doc['metadata']['program'] = line[9:].strip()
                    elif line.startswith('TYPE: '):
                        current_doc['metadata']['type'] = line[6:].strip()
                    elif line.startswith('COURSE_ID: '):
                        current_doc['metadata']['course_id'] = line[11:].strip()
                    elif line.startswith('LABEL: '):
                        current_doc['metadata']['label'] = line[7:].strip()
                    elif line.startswith('LEVEL: '):
                        current_doc['metadata']['level'] = line[7:].strip()
                    elif line.startswith('ERROR: '):
                        current_doc['error'] = line[7:].strip()
            
            elif current_doc and not section.startswith('='):
                # This is text content
                current_doc['text'] += section + '\n'
        
        # Add the last document
        if current_doc and current_doc.get('text'):
            documents.append(current_doc)
        
        print(f"Parsed {len(documents)} document sections")
        return documents
    
    def upload_text_documents(self, documents: List[Dict[str, Any]], clear_first: bool = False) -> bool:
        """
        Upload text documents to Neo4j.
        
        Args:
            documents: List of document dictionaries
            clear_first: Whether to clear database before uploading
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            if not self.connect():
                return False
        
        try:
            # Clear database if requested
            if clear_first:
                self.clear_database()
            
            print(f"Uploading {len(documents)} documents to Neo4j...")
            
            with self.driver.session(database=self.database) as session:
                # Upload documents
                self._upload_documents(session, documents)
                
                # Create relationships between documents
                self._create_relationships(session, documents)
                
                # Add metadata
                self._add_metadata(session, documents)
            
            print("✓ Documents uploaded successfully to Neo4j")
            return True
            
        except Exception as e:
            print(f"✗ Failed to upload documents: {e}")
            return False
    
    def _upload_documents(self, session, documents: List[Dict[str, Any]]):
        """Upload document nodes to Neo4j."""
        for i, doc in enumerate(documents, 1):
            print(f"  Uploading document {i}/{len(documents)}: {doc.get('url', 'Unknown')}")
            
            # Create document node
            doc_id = f"doc:{i:04d}"
            url = doc.get('url', f'unknown_{i}')
            text_content = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            # Add upload timestamp
            metadata['uploaded_at'] = datetime.now().isoformat()
            metadata['document_id'] = doc_id
            metadata['word_count'] = len(text_content.split())
            metadata['char_count'] = len(text_content)
            
            # Create node with type as label
            query = """
            MERGE (d:Document {id: $doc_id})
            SET d.url = $url,
                d.textContent = $text_content,
                d.program = $program,
                d.type = $doc_type,
                d.course_id = $course_id,
                d.label = $label,
                d.level = $level,
                d.uploaded_at = $uploaded_at,
                d.word_count = $word_count,
                d.char_count = $char_count
            """
            
            session.run(query, 
                       doc_id=doc_id,
                       url=url,
                       text_content=text_content,
                       program=metadata.get('program', 'Unknown'),
                       doc_type=metadata.get('type', 'unknown'),
                       course_id=metadata.get('course_id', ''),
                       label=metadata.get('label', ''),
                       level=metadata.get('level', ''),
                       uploaded_at=metadata['uploaded_at'],
                       word_count=metadata['word_count'],
                       char_count=metadata['char_count'])
    
    def _create_relationships(self, session, documents: List[Dict[str, Any]]):
        """Create relationships between documents."""
        print("  Creating relationships between documents...")
        
        # Group documents by program
        programs = {}
        for doc in documents:
            program = doc.get('metadata', {}).get('program', 'Unknown')
            if program not in programs:
                programs[program] = []
            programs[program].append(doc)
        
        # Create program nodes and relationships
        for program, program_docs in programs.items():
            # Create program node
            program_query = """
            MERGE (p:Program {name: $program_name})
            SET p.type = 'Program',
                p.uploaded_at = $uploaded_at
            """
            session.run(program_query, 
                       program_name=program, 
                       uploaded_at=datetime.now().isoformat())
            
            # Connect documents to program
            for doc in program_docs:
                doc_id = f"doc:{documents.index(doc) + 1:04d}"
                rel_query = """
                MATCH (p:Program {name: $program_name})
                MATCH (d:Document {id: $doc_id})
                MERGE (p)-[:HAS_DOCUMENT]->(d)
                """
                session.run(rel_query, program_name=program, doc_id=doc_id)
        
        # Create relationships between academics and course documents
        academics_docs = [doc for doc in documents if doc.get('metadata', {}).get('type') == 'academics']
        course_docs = [doc for doc in documents if doc.get('metadata', {}).get('type') == 'course']
        
        for academics_doc in academics_docs:
            academics_doc_id = f"doc:{documents.index(academics_doc) + 1:04d}"
            academics_program = academics_doc.get('metadata', {}).get('program')
            
            # Connect to courses in the same program
            for course_doc in course_docs:
                course_program = course_doc.get('metadata', {}).get('program')
                if course_program == academics_program:
                    course_doc_id = f"doc:{documents.index(course_doc) + 1:04d}"
                    
                    rel_query = """
                    MATCH (a:Document {id: $academics_id})
                    MATCH (c:Document {id: $course_id})
                    MERGE (a)-[:HAS_COURSE]->(c)
                    """
                    session.run(rel_query, academics_id=academics_doc_id, course_id=course_doc_id)
    
    def _add_metadata(self, session, documents: List[Dict[str, Any]]):
        """Add metadata about the upload."""
        # Create a metadata node
        metadata_query = """
        MERGE (m:Metadata {type: 'TextUpload'})
        SET m.uploaded_at = $uploaded_at,
            m.document_count = $doc_count,
            m.total_words = $total_words,
            m.total_characters = $total_characters,
            m.programs = $programs
        """
        
        total_words = sum(len(doc.get('text', '').split()) for doc in documents)
        total_chars = sum(len(doc.get('text', '')) for doc in documents)
        programs = list(set(doc.get('metadata', {}).get('program', 'Unknown') for doc in documents))
        
        session.run(metadata_query,
                   uploaded_at=datetime.now().isoformat(),
                   doc_count=len(documents),
                   total_words=total_words,
                   total_characters=total_chars,
                   programs=programs)
    
    def upload_text_file(self, file_path: str, clear_first: bool = False) -> bool:
        """
        Upload a text file to Neo4j.
        
        Args:
            file_path: Path to the text file
            clear_first: Whether to clear database before uploading
            
        Returns:
            True if successful, False otherwise
        """
        try:
            documents = self.parse_text_file(file_path)
            return self.upload_text_documents(documents, clear_first)
        except Exception as e:
            print(f"✗ Error uploading text file: {e}")
            return False
    
    def query_documents(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query on the uploaded documents.
        
        Args:
            cypher_query: Cypher query string
            
        Returns:
            List of query results
        """
        if not self.driver:
            if not self.connect():
                return []
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher_query)
                return [record.data() for record in result]
        except Exception as e:
            print(f"✗ Query failed: {e}")
            return []


def upload_text_to_neo4j(file_path: str, 
                        uri: str = "neo4j://127.0.0.1:7687",
                        username: str = "neo4j", 
                        password: str = "password",
                        database: str = "neo4j",
                        clear_first: bool = False) -> bool:
    """
    Convenience function to upload text file to Neo4j.
    
    Args:
        file_path: Path to the text file
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        database: Neo4j database name
        clear_first: Whether to clear database before uploading
        
    Returns:
        True if successful, False otherwise
    """
    uploader = TextToNeo4jUploader(uri, username, password, database)
    try:
        return uploader.upload_text_file(file_path, clear_first)
    finally:
        uploader.disconnect()


if __name__ == "__main__":
    # Test the uploader
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python text_to_neo4j.py <text_file> [--clear]")
        print("Example: python text_to_neo4j.py outputs/combined_text.txt --clear")
        sys.exit(1)
    
    file_path = sys.argv[1]
    clear_first = '--clear' in sys.argv
    
    print(f"Uploading text file: {file_path}")
    if clear_first:
        print("Will clear database before uploading")
    
    success = upload_text_to_neo4j(file_path, clear_first=clear_first)
    
    if success:
        print("✓ Upload completed successfully!")
    else:
        print("✗ Upload failed!")
        sys.exit(1)
