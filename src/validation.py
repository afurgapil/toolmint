#!/usr/bin/env python3
"""Validation functions for ToolMint"""

import re
from typing import Dict, Any, List, Tuple
from .quality import calculate_tool_quality_score, generate_semantic_description
from .labels import generate_labels
from .utils import sha, generate_smart_tool_name

def validate_tool(sql: str, params: List[Dict], question: str) -> Tuple[bool, str]:
    """Legacy validation - kept for backward compatibility"""
    is_valid, msg, _ = validate_tool_advanced(sql, params, question, min_score=0.0)
    return is_valid, msg

def validate_tool_advanced(sql: str, params: List[Dict], question: str, 
                        min_score: float = 50.0) -> Tuple[bool, str, float]:
    """
    Advanced quality validation with scoring.
    Returns: (is_valid, error_message, quality_score)
    """
    # Immediate rejection for basic issues
    if not sql or not sql.strip():
        return False, "Empty SQL", 0.0
    
    if len(params) < 1:
        return False, "No parameters - not reusable", 0.0
    
    # Check for overly simple SQL
    if re.match(r'^\s*SELECT\s+\*\s+FROM\s+\w+\s*;?\s*$', sql, re.I):
        return False, "Too simple - just SELECT * FROM table", 0.0
    
    # Ensure parameters appear in the SQL
    params_in_sql = set(re.findall(r'\{\{\.(\w+)\}\}', sql))
    if not params_in_sql:
        return False, "Parameters defined but not used in SQL", 0.0
    
    # Require a meaningful description
    if not question or not isinstance(question, str) or len(question) < 5:
        return False, "No meaningful description", 0.0
    
    # Calculate overall quality score
    score, breakdown = calculate_tool_quality_score(sql, params, question)
    
    # Enforce minimum score threshold
    if score < min_score:
        details = ", ".join([f"{k}={v:.1f}" for k, v in breakdown.items()])
        return False, f"Quality score too low: {score:.1f}/100 ({details})", score
    
    return True, "", score

def create_tool(rec_norm: Dict[str,Any], kind: str, source_name: str, 
                parameterize_tables: bool = True, min_score: float = 50.0) -> Tuple[Dict[str,Any], str]:
    """Create an MCP tool definition from a normalized record"""
    from .parameterizer import SQLParameterizer
    
    # Parameterize the SQL statement
    parameterizer = SQLParameterizer(
        parameterize_tables=parameterize_tables,
        parameterize_columns=True
    )
    parameterized_sql, params = parameterizer.parameterize(rec_norm["sql"])
    
    # Run quality validation
    is_valid, err_msg, quality_score = validate_tool_advanced(
        parameterized_sql, params, rec_norm["question"], min_score=min_score
    )
    
    if not is_valid:
        return {}, err_msg
    
    # Generate a tool name
    smart_name = generate_smart_tool_name(parameterized_sql, rec_norm["question"])
    key = f"{smart_name}_{sha(rec_norm['sql'] + rec_norm['question'], n=4)}"
    
    # Build description (without reusing the question verbatim)
    base_desc = generate_semantic_description(parameterized_sql, rec_norm["question"], params)
    labels_str = generate_labels(rec_norm["sql"])  # Original SQL for labels
    desc = f"{base_desc} [Labels: {labels_str}]" if labels_str else base_desc
    
    # Assemble the tool payload
    tool = {
        key: {
            "kind": kind,
            "source": source_name,
            "statement": parameterized_sql,
            "description": desc,
            "templateParameters": params
        }
    }
    
    return tool, key
