#!/usr/bin/env python3
"""Utility functions for ToolMint"""

import re
import hashlib
from typing import List

# ====== Settings ======
SAFE = re.compile(r"[^a-z0-9_]+")

def sha(s: str, n=8): 
    """Generate SHA1 hash of string, truncated to n characters"""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]

def slug(s: str, prefix="tool"):
    """Convert string to URL-safe slug"""
    s = (s or "").lower()
    s = SAFE.sub("_", s).strip("_")
    s = re.sub(r"_+", "_", s)
    if not s or not s[0].isalpha(): 
        s = f"{prefix}_{s}" if s else prefix
    return s[:60]

def generate_smart_tool_name(sql: str, question: str = "") -> str:
    """
    Derive a descriptive tool name from the SQL structure.
    Example: select_grouped_sorted_limited, select_joined_filtered, insert_into_table
    """
    sql_upper = sql.upper()
    
    # 1. Determine the primary SQL operation
    if sql_upper.strip().startswith('SELECT'):
        prefix = "select"
    elif sql_upper.strip().startswith('INSERT'):
        prefix = "insert"
    elif sql_upper.strip().startswith('UPDATE'):
        prefix = "update"
    elif sql_upper.strip().startswith('DELETE'):
        prefix = "delete"
    elif sql_upper.strip().startswith('CREATE'):
        prefix = "create"
    elif sql_upper.strip().startswith('ALTER'):
        prefix = "alter"
    elif sql_upper.strip().startswith('DROP'):
        prefix = "drop"
    else:
        prefix = "query"
    
    # 2. Detect structural features in priority order
    features = []
    
    # Aggregate functions (highest priority)
    if re.search(r'\bCOUNT\s*\(', sql, re.I):
        features.append("count")
    elif re.search(r'\bSUM\s*\(', sql, re.I):
        features.append("sum")
    elif re.search(r'\b(AVG|MAX|MIN)\s*\(', sql, re.I):
        features.append("aggregate")
    
    # GROUP BY
    if re.search(r'\bGROUP\s+BY\b', sql, re.I):
        features.append("grouped")
    
    # JOIN
    if re.search(r'\b(INNER\s+)?JOIN\b', sql, re.I):
        features.append("joined")
    elif re.search(r'\bLEFT\s+JOIN\b', sql, re.I):
        features.append("left_joined")
    elif re.search(r'\bRIGHT\s+JOIN\b', sql, re.I):
        features.append("right_joined")
    
    # WHERE (filtering)
    if re.search(r'\bWHERE\b', sql, re.I):
        features.append("filtered")
    
    # ORDER BY
    if re.search(r'\bORDER\s+BY\b', sql, re.I):
        features.append("sorted")
    
    # LIMIT
    if re.search(r'\bLIMIT\b', sql, re.I):
        features.append("limited")
    
    # OFFSET
    if re.search(r'\bOFFSET\b', sql, re.I):
        features.append("offset")
    
    # HAVING
    if re.search(r'\bHAVING\b', sql, re.I):
        features.append("having")
    
    # DISTINCT
    if re.search(r'\bDISTINCT\b', sql, re.I):
        features.append("distinct")
    
    # 3. Construct the name — up to three features in priority order
    parts = [prefix]
    
    # Priority: aggregate > grouped > joined > filtered > sorted > limited
    priority_order = ["count", "sum", "aggregate", "grouped", "joined", "left_joined", 
                      "filtered", "sorted", "limited", "distinct", "having", "offset"]
    
    sorted_features = []
    for feature in priority_order:
        if feature in features:
            sorted_features.append(feature)
    
    # Limit to at most three features
    parts.extend(sorted_features[:3])
    
    name = "_".join(parts)
    
    # Clean up the identifier
    name = re.sub(r'[^a-z0-9_]+', '_', name.lower())
    name = re.sub(r'_+', '_', name).strip('_')
    
    # Shorten if necessary
    if len(name) > 50:
        name = name[:50].rstrip('_')
    
    return name if name else "query"
