#!/usr/bin/env python3
"""
Neo4j Configuration Management

Handles loading and managing Neo4j configuration from files and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Neo4jSettings:
    """Neo4j connection and upload settings."""
    uri: str = "neo4j://127.0.0.1:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    clear_database: bool = False
    auto_upload: bool = True
    batch_size: int = 1000
    retry_attempts: int = 3
    timeout_seconds: int = 30
    log_level: str = "INFO"
    log_queries: bool = False
    log_upload_progress: bool = True


def load_config(config_path: Optional[str] = None) -> Neo4jSettings:
    """
    Load Neo4j configuration from file or environment variables.
    
    Args:
        config_path: Path to configuration file. If None, looks for neo4j_config.json
        
    Returns:
        Neo4jSettings object with configuration
    """
    settings = Neo4jSettings()
    
    # Try to load from config file
    if config_path is None:
        config_path = "neo4j_config.json"
    
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load Neo4j settings
            neo4j_config = config_data.get("neo4j", {})
            settings.uri = neo4j_config.get("uri", settings.uri)
            settings.username = neo4j_config.get("username", settings.username)
            settings.password = neo4j_config.get("password", settings.password)
            settings.database = neo4j_config.get("database", settings.database)
            settings.clear_database = neo4j_config.get("clear_database", settings.clear_database)
            
            # Load upload settings
            upload_config = config_data.get("upload_settings", {})
            settings.auto_upload = upload_config.get("auto_upload", settings.auto_upload)
            settings.batch_size = upload_config.get("batch_size", settings.batch_size)
            settings.retry_attempts = upload_config.get("retry_attempts", settings.retry_attempts)
            settings.timeout_seconds = upload_config.get("timeout_seconds", settings.timeout_seconds)
            
            # Load logging settings
            logging_config = config_data.get("logging", {})
            settings.log_level = logging_config.get("level", settings.log_level)
            settings.log_queries = logging_config.get("log_queries", settings.log_queries)
            settings.log_upload_progress = logging_config.get("log_upload_progress", settings.log_upload_progress)
            
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
    
    # Override with environment variables if present
    settings.uri = os.getenv("NEO4J_URI", settings.uri)
    settings.username = os.getenv("NEO4J_USERNAME", settings.username)
    settings.password = os.getenv("NEO4J_PASSWORD", settings.password)
    settings.database = os.getenv("NEO4J_DATABASE", settings.database)
    settings.clear_database = os.getenv("NEO4J_CLEAR", "false").lower() == "true"
    settings.auto_upload = os.getenv("NEO4J_AUTO_UPLOAD", "true").lower() == "true"
    
    return settings


def save_config(settings: Neo4jSettings, config_path: str = "neo4j_config.json") -> None:
    """
    Save Neo4j configuration to file.
    
    Args:
        settings: Neo4jSettings object to save
        config_path: Path to save configuration file
    """
    config_data = {
        "neo4j": {
            "uri": settings.uri,
            "username": settings.username,
            "password": settings.password,
            "database": settings.database,
            "clear_database": settings.clear_database
        },
        "upload_settings": {
            "auto_upload": settings.auto_upload,
            "batch_size": settings.batch_size,
            "retry_attempts": settings.retry_attempts,
            "timeout_seconds": settings.timeout_seconds
        },
        "logging": {
            "level": settings.log_level,
            "log_queries": settings.log_queries,
            "log_upload_progress": settings.log_upload_progress
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)


def get_neo4j_uri() -> str:
    """Get Neo4j URI from environment or default."""
    return os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")


def get_neo4j_credentials() -> tuple[str, str]:
    """Get Neo4j credentials from environment or defaults."""
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return username, password
