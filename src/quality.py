#!/usr/bin/env python3
"""Quality scoring functions for ToolMint"""

import re
from typing import Dict, Any, List, Tuple

def calculate_parameter_score(params: List[Dict]) -> float:
    """Parameter quality score: 0-40 points"""
    if not params:
        return 0.0
    
    score = 0.0
    
    # Number of parameters (max 15 points)
    param_count = len(params)
    if param_count >= 5:
        score += 15
    elif param_count >= 3:
        score += 10
    elif param_count >= 1:
        score += 5
    
    # Parameter diversity (max 15 points)
    param_types = set()
    for p in params:
        name = p['name'].lower()
        if 'table' in name:
            param_types.add('table')
        elif 'col' in name or 'column' in name:
            param_types.add('column')
        elif 'value' in name or 'threshold' in name:
            param_types.add('value')
        elif 'limit' in name or 'offset' in name:
            param_types.add('pagination')
        elif 'order' in name or 'sort' in name:
            param_types.add('sorting')
        elif 'where' in name or 'filter' in name or 'join' in name or 'group' in name:
            param_types.add('filter')
    
    # Each distinct type adds 3 points (up to 5 types × 3 = 15)
    score += min(len(param_types) * 3, 15)
    
    # Parameter type diversity (max 10 points)
    type_set = {p['type'] for p in params}
    score += min(len(type_set) * 5, 10)
    
    return min(score, 40)

def calculate_complexity_score(sql: str) -> float:
    """SQL complexity score: 0-30 points"""
    sql_upper = sql.upper()
    score = 0.0
    
    # Base SELECT: 5 points
    if 'SELECT' in sql_upper:
        score += 5
    
    # JOIN: +8 points
    if 'JOIN' in sql_upper:
        score += 8
        # Additional JOINs: +2 points each (max 2 extra)
        join_count = sql_upper.count('JOIN')
        score += min(join_count - 1, 2) * 2
    
    # GROUP BY: +7 points
    if 'GROUP BY' in sql_upper:
        score += 7
    
    # Aggregate functions: +5 points
    aggregates = ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']
    if any(agg in sql_upper for agg in aggregates):
        score += 5
    
    # WHERE + HAVING: +3 points
    if 'WHERE' in sql_upper:
        score += 2
    if 'HAVING' in sql_upper:
        score += 3
    
    # Subquery: +5 points
    if sql.count('SELECT') > 1:  # Nested SELECT
        score += 5
    
    # DISTINCT: +2 points
    if 'DISTINCT' in sql_upper:
        score += 2
    
    return min(score, 30)

def calculate_description_score(question: str, sql: str) -> float:
    """Description quality score: 0-20 points"""
    if not question:
        return 0.0
    
    score = 0.0
    
    # Length (max 10 points)
    if len(question) >= 100:
        score += 10
    elif len(question) >= 50:
        score += 7
    elif len(question) >= 20:
        score += 4
    else:
        score += 2
    
    # Contains useful keywords? (max 10 points)
    keywords = ['how many', 'what', 'which', 'list', 'show', 'return', 'find', 
                'calculate', 'count', 'average', 'maximum', 'minimum', 'total']
    keyword_count = sum(1 for kw in keywords if kw in question.lower())
    score += min(keyword_count * 2, 10)
    
    return min(score, 20)

def calculate_reusability_score(sql: str, params: List[Dict]) -> float:
    """Reusability score: 0-10 points"""
    score = 10.0
    
    # Penalize hardcoded values
    # String literals (single or double quotes)
    if re.search(r"'[^']{2,}'", sql) or re.search(r'"[^"]{2,}"', sql):
        score -= 3
    
    # Hardcoded numbers (excluding LIMIT/OFFSET)
    sql_without_params = re.sub(r'\{\{\.[\w]+\}\}', '', sql)
    if re.search(r'\b\d{2,}\b', sql_without_params):  # Numbers like 10+
        score -= 2
    
    # Fixed table/column names that were not parameterized
    if re.search(r'\bFROM\s+[a-zA-Z_]\w+(?!\s*\()', sql) and '{{.table' not in sql:
        score -= 2
    
    return max(score, 0)

def calculate_tool_quality_score(sql: str, params: List[Dict], question: str) -> Tuple[float, Dict[str, Any]]:
    """
    Score the tool from 0 to 100.
    Return: (score, breakdown_dict)
    """
    score = 0.0
    breakdown = {}
    
    # 1. PARAMETER SCORE (40 points)
    param_score = calculate_parameter_score(params)
    score += param_score
    breakdown["parameters"] = param_score
    
    # 2. SQL COMPLEXITY SCORE (30 points)
    complexity_score = calculate_complexity_score(sql)
    score += complexity_score
    breakdown["complexity"] = complexity_score
    
    # 3. DESCRIPTION QUALITY (20 points)
    description_score = calculate_description_score(question, sql)
    score += description_score
    breakdown["description"] = description_score
    
    # 4. REUSABILITY (10 points)
    reusability_score = calculate_reusability_score(sql, params)
    score += reusability_score
    breakdown["reusability"] = reusability_score
    
    return score, breakdown

def describe_sql_structure(sql: str) -> str:
    """Explain how the SQL behaves in natural language"""
    sql_upper = sql.upper()
    desc_parts = []
    
    # Determine whether it is SELECT, INSERT, UPDATE, etc.
    if 'SELECT' in sql_upper:
        desc_parts.append("Retrieves data")
        
        # Aggregate functions
        if 'COUNT(' in sql_upper:
            desc_parts.append("counts records")
        elif 'SUM(' in sql_upper:
            desc_parts.append("calculates sum")
        elif 'AVG(' in sql_upper:
            desc_parts.append("calculates average")
        elif 'MAX(' in sql_upper or 'MIN(' in sql_upper:
            desc_parts.append("finds extremes")
        
        # JOIN
        if 'JOIN' in sql_upper:
            desc_parts.append("by joining multiple tables")
        
        # GROUP BY
        if 'GROUP BY' in sql_upper:
            desc_parts.append("grouped by criteria")
        
        # WHERE
        if 'WHERE' in sql_upper:
            desc_parts.append("with filtering conditions")
        
        # ORDER BY
        if 'ORDER BY' in sql_upper:
            desc_parts.append("sorted by specified column")
        
        # LIMIT
        if 'LIMIT' in sql_upper:
            desc_parts.append("limited to top results")
    
    return " ".join(desc_parts) if desc_parts else ""

def describe_parameters(params: List[Dict]) -> str:
    """Describe parameters in a user-friendly way"""
    if not params:
        return ""
    
    # Categorize parameters for readability
    tables = [p for p in params if 'table' in p['name'].lower()]
    columns = [p for p in params if 'col' in p['name'].lower()]
    filters = [p for p in params if p['name'] in ['value', 'threshold', 'limit_n', 'offset_n']]
    strings = [p for p in params if p['type'] == 'string' and p not in tables + columns]
    
    desc_parts = []
    
    if tables:
        desc_parts.append(f"customizable tables ({len(tables)})")
    if columns:
        desc_parts.append(f"flexible column selection ({len(columns)})")
    if filters:
        desc_parts.append(f"adjustable filters and limits ({len(filters)})")
    if strings:
        desc_parts.append(f"string pattern matching ({len(strings)})")
    
    return "Parameters: " + ", ".join(desc_parts) if desc_parts else ""

def generate_semantic_description(sql: str, question: str, params: List[Dict]) -> str:
    """
    Build a rich description optimized for embedding-based retrieval.
    Goal: surface the tool when users ask in natural language.
    Avoid reusing the original question; rely on SQL structure and parameters.
    """
    parts = []
    
    # 1. Explain what the SQL does
    sql_desc = describe_sql_structure(sql)
    if sql_desc:
        parts.append(sql_desc)
    
    # 2. Describe what can be customized through parameters
    if params:
        param_desc = describe_parameters(params)
        if param_desc:
            parts.append(param_desc)
    
    # 3. Combine both parts in an embedding-friendly sentence
    description = ". ".join(parts)
    
    # Trim to embedding-friendly length (≈500 chars)
    return description[:500]
