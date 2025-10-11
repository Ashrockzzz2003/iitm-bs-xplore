#!/usr/bin/env python3
"""
Neo4j CLI Utility

Command-line interface for Neo4j operations including uploading knowledge graphs,
querying data, and managing the database.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
import logging

from .neo4j_uploader import Neo4jUploader, Neo4jConfig, create_neo4j_uploader


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_kg_data(file_path: str) -> dict:
    """Load knowledge graph data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading KG data from {file_path}: {e}")
        sys.exit(1)


def upload_command(args):
    """Handle upload command."""
    kg_data = load_kg_data(args.file)
    
    uploader = create_neo4j_uploader(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database,
        clear_database=args.clear
    )
    
    if uploader.upload_kg(kg_data):
        print("✅ Knowledge graph uploaded successfully!")
    else:
        print("❌ Failed to upload knowledge graph")
        sys.exit(1)


def query_command(args):
    """Handle query command."""
    uploader = create_neo4j_uploader(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )
    
    if not uploader.connect():
        print("❌ Failed to connect to Neo4j")
        sys.exit(1)
    
    try:
        results = uploader.query_kg(args.query)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"✅ Query results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        sys.exit(1)
    finally:
        uploader.disconnect()


def clear_command(args):
    """Handle clear command."""
    uploader = create_neo4j_uploader(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )
    
    if not uploader.connect():
        print("❌ Failed to connect to Neo4j")
        sys.exit(1)
    
    if args.confirm:
        uploader.clear_database()
        print("✅ Database cleared successfully!")
    else:
        print("⚠️  Use --confirm flag to clear the database")
        sys.exit(1)
    
    uploader.disconnect()


def status_command(args):
    """Handle status command."""
    uploader = create_neo4j_uploader(
        uri=args.uri,
        username=args.username,
        password=args.password,
        database=args.database
    )
    
    if not uploader.connect():
        print("❌ Failed to connect to Neo4j")
        sys.exit(1)
    
    try:
        # Get basic stats
        stats_query = """
        MATCH (n)
        RETURN 
            count(n) as total_nodes,
            count(DISTINCT labels(n)) as unique_labels,
            count([r IN relationships(n) | r]) as total_relationships
        """
        
        stats = uploader.query_kg(stats_query)
        if stats:
            print("📊 Database Statistics:")
            print(f"  Total nodes: {stats[0]['total_nodes']}")
            print(f"  Unique labels: {stats[0]['unique_labels']}")
            print(f"  Total relationships: {stats[0]['total_relationships']}")
        
        # Get node type breakdown
        node_types_query = """
        MATCH (n)
        RETURN labels(n) as labels, count(n) as count
        ORDER BY count DESC
        """
        
        node_types = uploader.query_kg(node_types_query)
        if node_types:
            print("\n📋 Node Types:")
            for result in node_types:
                labels = result['labels']
                count = result['count']
                label_str = ':'.join(labels) if labels else 'No Label'
                print(f"  {label_str}: {count}")
        
        # Get relationship types
        rel_types_query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationship_type, count(r) as count
        ORDER BY count DESC
        """
        
        rel_types = uploader.query_kg(rel_types_query)
        if rel_types:
            print("\n🔗 Relationship Types:")
            for result in rel_types:
                rel_type = result['relationship_type']
                count = result['count']
                print(f"  {rel_type}: {count}")
                
    except Exception as e:
        print(f"❌ Failed to get status: {e}")
        sys.exit(1)
    finally:
        uploader.disconnect()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Neo4j Knowledge Graph Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a knowledge graph
  python -m src.neo4j_integration.cli upload data.json --clear
  
  # Query the database
  python -m src.neo4j_integration.cli query "MATCH (n) RETURN n LIMIT 5"
  
  # Get database status
  python -m src.neo4j_integration.cli status
  
  # Clear the database
  python -m src.neo4j_integration.cli clear --confirm
        """
    )
    
    # Global arguments
    parser.add_argument('--uri', default='neo4j://127.0.0.1:7687',
                       help='Neo4j URI (default: neo4j://127.0.0.1:7687)')
    parser.add_argument('--username', default='neo4j',
                       help='Neo4j username (default: neo4j)')
    parser.add_argument('--password', default='password',
                       help='Neo4j password (default: password)')
    parser.add_argument('--database', default='neo4j',
                       help='Neo4j database name (default: neo4j)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload knowledge graph to Neo4j')
    upload_parser.add_argument('file', help='Path to JSON knowledge graph file')
    upload_parser.add_argument('--clear', action='store_true',
                              help='Clear database before uploading')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Execute Cypher query')
    query_parser.add_argument('query', help='Cypher query string')
    query_parser.add_argument('--output', '-o', help='Output file for results')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear the database')
    clear_parser.add_argument('--confirm', action='store_true',
                             help='Confirm database clearing')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show database status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.verbose)
    
    # Route to appropriate command handler
    if args.command == 'upload':
        upload_command(args)
    elif args.command == 'query':
        query_command(args)
    elif args.command == 'clear':
        clear_command(args)
    elif args.command == 'status':
        status_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
