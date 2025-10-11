# Neo4j Integration Guide

This guide explains how to use the Neo4j integration features to upload and query knowledge graphs in a Neo4j database.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Neo4j Database

Make sure your Neo4j instance is running at `neo4j://127.0.0.1:7687` with:
- Username: `neo4j`
- Password: `password`

### 3. Upload Knowledge Graph

```bash
# Upload with automatic Neo4j integration
python app.py --url "https://study.iitm.ac.in/ds/academics.html" --neo4j

# Or upload existing JSON file
python -m src.neo4j_integration.cli upload outputs/data.json --clear
```

## 📋 Features

### Automatic Upload
- Upload knowledge graphs directly when generating them
- Configurable connection settings
- Optional database clearing before upload

### Command Line Interface
- Upload knowledge graphs from JSON files
- Execute custom Cypher queries
- View database status and statistics
- Clear database when needed

### Advanced Querying
- Pre-built queries for academic data
- Course prerequisite analysis
- Program structure exploration
- Relationship pattern discovery

## 🛠️ Usage

### Command Line Interface

#### Upload Knowledge Graph
```bash
python -m src.neo4j_integration.cli upload <kg_file.json> [options]
```

Options:
- `--clear`: Clear database before uploading
- `--uri`: Neo4j URI (default: neo4j://127.0.0.1:7687)
- `--username`: Username (default: neo4j)
- `--password`: Password (default: password)
- `--database`: Database name (default: neo4j)

#### Query Database
```bash
python -m src.neo4j_integration.cli query "MATCH (n) RETURN n LIMIT 5" [options]
```

Options:
- `--output`: Save results to file
- `--uri`, `--username`, `--password`, `--database`: Connection settings

#### View Status
```bash
python -m src.neo4j_integration.cli status
```

#### Clear Database
```bash
python -m src.neo4j_integration.cli clear --confirm
```

### Programmatic Usage

```python
from src.neo4j_integration import create_neo4j_uploader

# Create uploader
uploader = create_neo4j_uploader(
    uri="neo4j://127.0.0.1:7687",
    username="neo4j",
    password="password",
    database="neo4j",
    clear_database=False
)

# Upload knowledge graph
kg_data = {"nodes": [...], "edges": [...]}
success = uploader.upload_kg(kg_data)

# Query data
results = uploader.query_kg("MATCH (n) RETURN n LIMIT 5")

# Get specific data
courses = uploader.get_courses_by_level("level:foundation")
prereqs = uploader.get_course_prerequisites("BSDA1001")

uploader.disconnect()
```

## 🔧 Configuration

### Configuration File

Create `neo4j_config.json` in the project root:

```json
{
  "neo4j": {
    "uri": "neo4j://127.0.0.1:7687",
    "username": "neo4j",
    "password": "password",
    "database": "neo4j",
    "clear_database": false
  },
  "upload_settings": {
    "auto_upload": true,
    "batch_size": 1000,
    "retry_attempts": 3,
    "timeout_seconds": 30
  },
  "logging": {
    "level": "INFO",
    "log_queries": false,
    "log_upload_progress": true
  }
}
```

### Environment Variables

Override configuration with environment variables:

```bash
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_password"
export NEO4J_DATABASE="neo4j"
export NEO4J_CLEAR="false"
export NEO4J_AUTO_UPLOAD="true"
```

## 📊 Data Model

### Node Types
- `NodeType_Program`: Academic programs
- `NodeType_Level`: Academic levels (Foundation, Diploma, etc.)
- `NodeType_Section`: Content sections
- `NodeType_Course`: Individual courses
- `NodeType_Collection`: Course collections
- `NodeType_Metadata`: Upload metadata

### Relationship Types
- `HAS_LEVEL`: Program has academic levels
- `HAS_SECTION`: Level has content sections
- `HAS`: General containment relationships
- `REQUIRES`: Course prerequisites
- `CONTAINS`: Level contains courses

### Node Properties
All nodes include:
- `id`: Unique identifier
- `type`: Node type
- `properties`: Type-specific properties
- `uploaded_at`: Upload timestamp

## 🔍 Example Queries

### Find All Programs
```cypher
MATCH (p:NodeType_Program) 
RETURN p.id, p.properties.name
```

### Get Course Prerequisites
```cypher
MATCH (course:Node {id: "BSDA1001"})-[:REQUIRES]->(prereq:Node)
RETURN prereq.id, prereq.properties
```

### Find Program Structure
```cypher
MATCH (program:Node {type: "Program"})-[:HAS_LEVEL]->(level:Node)
OPTIONAL MATCH (level)-[:HAS]->(section:Node)
RETURN program.id, level.id, section.id
ORDER BY level.id, section.id
```

### Find Most Connected Nodes
```cypher
MATCH (n:Node)
WITH n, size([(n)-[]->() | 1]) + size([(n)<-[]-() | 1]) as connections
WHERE connections > 0
RETURN n.id, n.type, connections
ORDER BY connections DESC
LIMIT 10
```

### Search by Content
```cypher
MATCH (n:Node)
WHERE n.properties.title CONTAINS "Foundation" 
   OR n.properties.title CONTAINS "Diploma"
RETURN n.id, n.type, n.properties.title
```

## 🚨 Troubleshooting

### Connection Issues
- Verify Neo4j is running: `neo4j status`
- Check connection string format
- Ensure credentials are correct
- Check firewall/network settings

### Upload Issues
- Verify JSON format is valid
- Check database permissions
- Monitor Neo4j logs for errors
- Try clearing database first

### Query Issues
- Validate Cypher syntax
- Check node/relationship labels
- Use `EXPLAIN` or `PROFILE` for performance
- Start with simple queries

## 📚 Examples

See `examples/neo4j_example.py` for comprehensive usage examples including:
- Basic upload and query operations
- Advanced academic data queries
- Relationship pattern analysis
- Error handling and best practices

## 🔗 Integration with Main App

The Neo4j integration is seamlessly integrated with the main application:

```bash
# Generate KG and upload to Neo4j automatically
python app.py --url "https://study.iitm.ac.in/ds/academics.html" --neo4j

# With custom Neo4j settings
python app.py --url "https://study.iitm.ac.in/ds/academics.html" \
  --neo4j \
  --neo4j-uri "neo4j://localhost:7687" \
  --neo4j-username "neo4j" \
  --neo4j-password "your_password" \
  --neo4j-clear
```

## 🎯 Best Practices

1. **Always backup** your Neo4j database before clearing
2. **Use transactions** for large uploads
3. **Monitor performance** with query profiling
4. **Index frequently queried properties**
5. **Use parameterized queries** for security
6. **Test queries** before running on production data

## 📈 Performance Tips

- Use `MERGE` instead of `CREATE` to avoid duplicates
- Batch operations for large datasets
- Create indexes on frequently queried properties
- Use `LIMIT` in queries to avoid large result sets
- Profile queries to identify bottlenecks

## 🔒 Security

- Use strong passwords for Neo4j
- Enable authentication and authorization
- Use encrypted connections (neo4j+s://)
- Regularly update Neo4j version
- Monitor access logs
