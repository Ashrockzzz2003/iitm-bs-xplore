#!/usr/bin/env python3
"""
Neo4j Knowledge Graph Uploader

This module provides functionality to upload knowledge graphs to Neo4j database.
It handles node creation, relationship mapping, and data synchronization.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from neo4j import GraphDatabase
import json
from datetime import datetime


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j connection."""
    uri: str = "neo4j://127.0.0.1:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    clear_database: bool = False


class Neo4jUploader:
    """Handles uploading knowledge graphs to Neo4j database."""
    
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            # Test connection
            with self.driver.session(database=self.config.database) as session:
                session.run("RETURN 1")
            self.logger.info(f"Successfully connected to Neo4j at {self.config.uri}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    def disconnect(self):
        """Close connection to Neo4j database."""
        if self.driver:
            self.driver.close()
            self.logger.info("Disconnected from Neo4j")
    
    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
        
        with self.driver.session(database=self.config.database) as session:
            # Delete all relationships first
            session.run("MATCH ()-[r]->() DELETE r")
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            self.logger.info("Database cleared successfully")
    
    def upload_kg(self, kg_data: Dict[str, Any], clear_first: bool = None) -> bool:
        """
        Upload knowledge graph data to Neo4j.
        
        Args:
            kg_data: Knowledge graph data with 'nodes' and 'edges' arrays
            clear_first: Whether to clear database before uploading (overrides config)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.driver:
            if not self.connect():
                return False
        
        try:
            # Clear database if requested
            if clear_first if clear_first is not None else self.config.clear_database:
                self.clear_database()
            
            nodes = kg_data.get("nodes", [])
            edges = kg_data.get("edges", [])
            
            self.logger.info(f"Uploading {len(nodes)} nodes and {len(edges)} edges to Neo4j")
            
            with self.driver.session(database=self.config.database) as session:
                # Upload nodes
                self._upload_nodes(session, nodes)
                
                # Upload edges/relationships
                self._upload_edges(session, edges)
                
                # Add metadata
                self._add_metadata(session, kg_data)
            
            self.logger.info("Knowledge graph uploaded successfully to Neo4j")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload knowledge graph: {e}")
            return False
    
    def _upload_nodes(self, session, nodes: List[Dict[str, Any]]):
        """Upload nodes to Neo4j."""
        for node in nodes:
            node_id = node.get("id", "")
            node_type = node.get("type", "Unknown")
            properties = node.get("properties", {})
            
            # Add upload timestamp
            properties["uploaded_at"] = datetime.now().isoformat()
            
            # Flatten complex properties for Neo4j compatibility
            flattened_properties = self._flatten_properties(properties)
            
            # Create node with type as label
            query = f"""
            MERGE (n:Node {{id: $id}})
            SET n:NodeType_{node_type}
            SET n += $properties
            """
            
            session.run(query, id=node_id, properties=flattened_properties)
    
    def _upload_edges(self, session, edges: List[Dict[str, Any]]):
        """Upload edges/relationships to Neo4j."""
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            edge_type = edge.get("type", "RELATES_TO")
            properties = edge.get("properties", {})
            
            # Add upload timestamp
            properties["uploaded_at"] = datetime.now().isoformat()
            
            # Flatten properties for Neo4j compatibility
            flattened_properties = self._flatten_properties(properties)
            
            # Create relationship
            query = f"""
            MATCH (source:Node {{id: $source_id}})
            MATCH (target:Node {{id: $target_id}})
            MERGE (source)-[r:{edge_type}]->(target)
            SET r += $properties
            """
            
            session.run(query, 
                       source_id=source, 
                       target_id=target, 
                       properties=flattened_properties)
    
    def _flatten_properties(self, properties: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested properties for Neo4j compatibility.
        
        Neo4j only supports primitive types and arrays of primitives.
        This method converts complex nested structures to strings.
        """
        flattened = {}
        
        for key, value in properties.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, (str, int, float, bool)) or value is None:
                # Primitive types are fine
                flattened[full_key] = value
            elif isinstance(value, list):
                # Handle lists - convert complex items to strings
                flattened_list = []
                for item in value:
                    if isinstance(item, (str, int, float, bool)) or item is None:
                        flattened_list.append(item)
                    else:
                        flattened_list.append(str(item))
                flattened[full_key] = flattened_list
            elif isinstance(value, dict):
                # Recursively flatten dictionaries
                nested = self._flatten_properties(value, f"{full_key}_")
                flattened.update(nested)
            else:
                # Convert everything else to string
                flattened[full_key] = str(value)
        
        return flattened

    def _add_metadata(self, session, kg_data: Dict[str, Any]):
        """Add metadata about the knowledge graph."""
        meta = kg_data.get("meta", {})
        
        # Create a metadata node
        metadata_query = """
        MERGE (m:Metadata {type: 'KnowledgeGraph'})
        SET m.uploaded_at = $uploaded_at,
            m.node_count = $node_count,
            m.edge_count = $edge_count,
            m.meta = $meta
        """
        
        session.run(metadata_query,
                   uploaded_at=datetime.now().isoformat(),
                   node_count=len(kg_data.get("nodes", [])),
                   edge_count=len(kg_data.get("edges", [])),
                   meta=json.dumps(meta))
    
    def query_kg(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query on the knowledge graph.
        
        Args:
            cypher_query: Cypher query string
            
        Returns:
            List of query results
        """
        if not self.driver:
            if not self.connect():
                return []
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(cypher_query)
                return [record.data() for record in result]
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return []
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific node by its ID."""
        query = "MATCH (n:Node {id: $node_id}) RETURN n"
        results = self.query_kg(query, node_id=node_id)
        return results[0] if results else None
    
    def get_relationships(self, node_id: str, direction: str = "both") -> List[Dict[str, Any]]:
        """
        Get relationships for a specific node.
        
        Args:
            node_id: ID of the node
            direction: "in", "out", or "both"
        """
        if direction == "in":
            query = "MATCH (n:Node {id: $node_id})<-[r]-(other) RETURN r, other"
        elif direction == "out":
            query = "MATCH (n:Node {id: $node_id})-[r]->(other) RETURN r, other"
        else:
            query = "MATCH (n:Node {id: $node_id})-[r]-(other) RETURN r, other"
        
        return self.query_kg(query, node_id=node_id)
    
    def get_course_prerequisites(self, course_id: str) -> List[Dict[str, Any]]:
        """Get prerequisites for a specific course."""
        query = """
        MATCH (course:Node {id: $course_id})-[:REQUIRES]->(prereq)
        RETURN prereq
        """
        return self.query_kg(query, course_id=course_id)
    
    def get_courses_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Get all courses for a specific level."""
        query = """
        MATCH (level:Node {id: $level_id})-[:HAS]->(collection:Node)-[:HAS]->(course:Node)
        WHERE collection.type = 'Collection' AND course.type = 'Course'
        RETURN course
        """
        return self.query_kg(query, level_id=level)
    
    def get_program_structure(self) -> List[Dict[str, Any]]:
        """Get the complete program structure."""
        query = """
        MATCH (program:Node {type: 'Program'})-[:HAS_LEVEL]->(level:Node)
        OPTIONAL MATCH (level)-[:HAS]->(section:Node)
        OPTIONAL MATCH (level)-[:HAS]->(collection:Node)-[:HAS]->(course:Node)
        RETURN program, level, section, collection, course
        ORDER BY level.id, section.id, course.id
        """
        return self.query_kg(query)


def create_neo4j_uploader(uri: str = "neo4j://127.0.0.1:7687", 
                         username: str = "neo4j", 
                         password: str = "password",
                         database: str = "neo4j",
                         clear_database: bool = False) -> Neo4jUploader:
    """Convenience function to create a Neo4j uploader with default settings."""
    config = Neo4jConfig(
        uri=uri,
        username=username,
        password=password,
        database=database,
        clear_database=clear_database
    )
    return Neo4jUploader(config)
