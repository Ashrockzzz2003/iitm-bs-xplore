"""
Knowledge Graph Cleaner

Utilities for cleaning and filtering knowledge graphs to remove unwanted content.
Specifically designed to remove generic content from course-specific knowledge graphs.
"""

import logging
from typing import Dict, List, Any, Set
import re

logger = logging.getLogger(__name__)

# Keywords that indicate generic/non-course content
GENERIC_KEYWORDS = {
    'navigation', 'menu', 'footer', 'header', 'sidebar', 'breadcrumb',
    'login', 'logout', 'signin', 'signup', 'register', 'account',
    'contact', 'about', 'help', 'support', 'faq', 'privacy', 'terms',
    'policy', 'disclaimer', 'copyright', 'legal', 'accessibility',
    'home', 'main', 'index', 'welcome', 'overview', 'introduction',
    'announcement', 'news', 'update', 'notification', 'alert',
    'search', 'filter', 'sort', 'browse', 'explore', 'discover',
    'social', 'share', 'follow', 'subscribe', 'newsletter',
    'advertisement', 'ad', 'promo', 'banner', 'sponsor',
    'cookie', 'tracking', 'analytics', 'metrics', 'statistics'
}

# Node types that are typically generic
GENERIC_NODE_TYPES = {
    'Navigation', 'Menu', 'Footer', 'Header', 'Sidebar', 'Breadcrumb',
    'Link', 'Button', 'Form', 'Input', 'Select', 'Checkbox', 'Radio',
    'Image', 'Icon', 'Logo', 'Banner', 'Advertisement', 'Ad',
    'Social', 'Share', 'Follow', 'Subscribe', 'Newsletter',
    'Search', 'Filter', 'Sort', 'Browse', 'Explore', 'Discover',
    'Announcement', 'News', 'Update', 'Notification', 'Alert',
    'Contact', 'About', 'Help', 'Support', 'FAQ', 'Privacy', 'Terms',
    'Policy', 'Disclaimer', 'Copyright', 'Legal', 'Accessibility'
}

# Section titles that indicate generic content
GENERIC_SECTION_TITLES = {
    'navigation', 'menu', 'footer', 'header', 'sidebar', 'breadcrumb',
    'login', 'logout', 'signin', 'signup', 'register', 'account',
    'contact', 'about', 'help', 'support', 'faq', 'privacy', 'terms',
    'policy', 'disclaimer', 'copyright', 'legal', 'accessibility',
    'home', 'main', 'index', 'welcome', 'overview', 'introduction',
    'announcement', 'news', 'update', 'notification', 'alert',
    'search', 'filter', 'sort', 'browse', 'explore', 'discover',
    'social', 'share', 'follow', 'subscribe', 'newsletter',
    'advertisement', 'ad', 'promo', 'banner', 'sponsor',
    'cookie', 'tracking', 'analytics', 'metrics', 'statistics',
    'site map', 'site navigation', 'quick links', 'related links',
    'external links', 'useful links', 'resources', 'tools',
    'utilities', 'services', 'features', 'benefits', 'advantages'
}


def is_generic_content(node: Dict[str, Any]) -> bool:
    """Check if a node represents generic (non-course) content.
    
    Args:
        node: Node dictionary to check
        
    Returns:
        True if the node is generic content, False otherwise
    """
    node_type = node.get('type', '').lower()
    properties = node.get('properties', {})
    title = properties.get('title', '').lower()
    
    # Check node type
    if node_type in [t.lower() for t in GENERIC_NODE_TYPES]:
        return True
    
    # Check title against generic keywords
    if any(keyword in title for keyword in GENERIC_KEYWORDS):
        return True
    
    # Check if title matches generic section patterns
    if any(pattern in title for pattern in GENERIC_SECTION_TITLES):
        return True
    
    # Check for generic ID patterns
    node_id = node.get('id', '').lower()
    if any(pattern in node_id for pattern in ['nav', 'menu', 'footer', 'header', 'sidebar']):
        return True
    
    # Check for generic content in attributes
    attributes = properties.get('attributes', {})
    if isinstance(attributes, dict):
        for attr_name, attr_value in attributes.items():
            attr_name_lower = attr_name.lower()
            if any(keyword in attr_name_lower for keyword in GENERIC_KEYWORDS):
                return True
            
            # Check attribute values for generic content
            if isinstance(attr_value, dict):
                for sub_attr_name, sub_attr_value in attr_value.items():
                    if isinstance(sub_attr_value, str):
                        sub_attr_value_lower = sub_attr_value.lower()
                        if any(keyword in sub_attr_value_lower for keyword in GENERIC_KEYWORDS):
                            return True
    
    return False


def clean_course_kg(kg: Dict[str, Any]) -> Dict[str, Any]:
    """Remove generic content from a course-specific knowledge graph.
    
    Args:
        kg: Knowledge graph to clean
        
    Returns:
        Cleaned knowledge graph with generic content removed
    """
    logger.info("Cleaning course knowledge graph to remove generic content")
    
    nodes = kg.get('nodes', [])
    edges = kg.get('edges', [])
    meta = kg.get('meta', {})
    
    # Identify nodes to remove
    nodes_to_remove = set()
    for node in nodes:
        if is_generic_content(node):
            nodes_to_remove.add(node['id'])
            logger.debug(f"Marking generic node for removal: {node['id']} - {node.get('properties', {}).get('title', 'No title')}")
    
    # Filter out generic nodes
    cleaned_nodes = [node for node in nodes if node['id'] not in nodes_to_remove]
    
    # Filter out edges that reference removed nodes
    cleaned_edges = []
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        
        # Keep edge if both source and target are not removed
        if source not in nodes_to_remove and target not in nodes_to_remove:
            cleaned_edges.append(edge)
        else:
            logger.debug(f"Removing edge referencing generic node: {source} -> {target}")
    
    # Update metadata
    cleaned_meta = meta.copy()
    cleaned_meta['cleaned'] = True
    cleaned_meta['original_node_count'] = len(nodes)
    cleaned_meta['original_edge_count'] = len(edges)
    cleaned_meta['removed_node_count'] = len(nodes_to_remove)
    cleaned_meta['removed_edge_count'] = len(edges) - len(cleaned_edges)
    
    logger.info(f"Course KG cleaning complete: removed {len(nodes_to_remove)} generic nodes and {len(edges) - len(cleaned_edges)} edges")
    
    return {
        'nodes': cleaned_nodes,
        'edges': cleaned_edges,
        'meta': cleaned_meta
    }


def clean_generic_kg(kg: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a generic knowledge graph by removing course-specific content.
    
    Args:
        kg: Knowledge graph to clean
        
    Returns:
        Cleaned knowledge graph with course-specific content removed
    """
    logger.info("Cleaning generic knowledge graph to remove course-specific content")
    
    nodes = kg.get('nodes', [])
    edges = kg.get('edges', [])
    meta = kg.get('meta', {})
    
    # Identify course-specific nodes to remove
    nodes_to_remove = set()
    for node in nodes:
        node_type = node.get('type', '').lower()
        properties = node.get('properties', {})
        title = properties.get('title', '').lower()
        
        # Remove course nodes
        if node_type == 'course':
            nodes_to_remove.add(node['id'])
            logger.debug(f"Marking course node for removal: {node['id']}")
            continue
        
        # Remove nodes with course codes in title or ID
        if re.search(r'\b[A-Z]{2,4}\s?-?\d{3,4}\b', title) or re.search(r'\b[A-Z]{2,4}\s?-?\d{3,4}\b', node.get('id', '')):
            nodes_to_remove.add(node['id'])
            logger.debug(f"Marking course-code node for removal: {node['id']}")
            continue
        
        # Remove academic level nodes
        if node_type == 'level' and any(level in title for level in ['foundation', 'diploma', 'degree', 'academic']):
            nodes_to_remove.add(node['id'])
            logger.debug(f"Marking academic level node for removal: {node['id']}")
            continue
        
        # Remove program nodes
        if node_type == 'program' and any(program in title for program in ['bs', 'bachelor', 'science', 'data science', 'electronics']):
            nodes_to_remove.add(node['id'])
            logger.debug(f"Marking program node for removal: {node['id']}")
            continue
    
    # Filter out course-specific nodes
    cleaned_nodes = [node for node in nodes if node['id'] not in nodes_to_remove]
    
    # Filter out edges that reference removed nodes
    cleaned_edges = []
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        
        # Keep edge if both source and target are not removed
        if source not in nodes_to_remove and target not in nodes_to_remove:
            cleaned_edges.append(edge)
        else:
            logger.debug(f"Removing edge referencing course node: {source} -> {target}")
    
    # Update metadata
    cleaned_meta = meta.copy()
    cleaned_meta['cleaned'] = True
    cleaned_meta['original_node_count'] = len(nodes)
    cleaned_meta['original_edge_count'] = len(edges)
    cleaned_meta['removed_node_count'] = len(nodes_to_remove)
    cleaned_meta['removed_edge_count'] = len(edges) - len(cleaned_edges)
    
    logger.info(f"Generic KG cleaning complete: removed {len(nodes_to_remove)} course-specific nodes and {len(edges) - len(cleaned_edges)} edges")
    
    return {
        'nodes': cleaned_nodes,
        'edges': cleaned_edges,
        'meta': cleaned_meta
    }


def clean_dual_kgs(course_kg: Dict[str, Any], generic_kg: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Clean both course and generic knowledge graphs.
    
    Args:
        course_kg: Course-specific knowledge graph
        generic_kg: Generic knowledge graph
        
    Returns:
        Tuple of (cleaned_course_kg, cleaned_generic_kg)
    """
    logger.info("Cleaning both knowledge graphs")
    
    cleaned_course_kg = clean_course_kg(course_kg)
    cleaned_generic_kg = clean_generic_kg(generic_kg)
    
    return cleaned_course_kg, cleaned_generic_kg
