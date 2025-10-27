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
    Gelişmiş kalite kontrolü with scoring.
    Returns: (is_valid, error_message, quality_score)
    """
    # Temel kontroller (hemen red)
    if not sql or not sql.strip():
        return False, "Empty SQL", 0.0
    
    if len(params) < 1:
        return False, "No parameters - not reusable", 0.0
    
    # SQL çok basit mi?
    if re.match(r'^\s*SELECT\s+\*\s+FROM\s+\w+\s*;?\s*$', sql, re.I):
        return False, "Too simple - just SELECT * FROM table", 0.0
    
    # Parametreler SQL'de kullanılıyor mu?
    params_in_sql = set(re.findall(r'\{\{\.(\w+)\}\}', sql))
    if not params_in_sql:
        return False, "Parameters defined but not used in SQL", 0.0
    
    # Description var mı?
    if not question or not isinstance(question, str) or len(question) < 5:
        return False, "No meaningful description", 0.0
    
    # Kalite puanı hesapla
    score, breakdown = calculate_tool_quality_score(sql, params, question)
    
    # Minimum skoru geçiyor mu?
    if score < min_score:
        details = ", ".join([f"{k}={v:.1f}" for k, v in breakdown.items()])
        return False, f"Quality score too low: {score:.1f}/100 ({details})", score
    
    return True, "", score

def create_tool(rec_norm: Dict[str,Any], kind: str, source_name: str, 
                parameterize_tables: bool = True, min_score: float = 50.0) -> Tuple[Dict[str,Any], str]:
    """Bir kayıttan MCP tool oluştur"""
    from .parameterizer import SQLParameterizer
    
    # SQL'i parametreleştir
    parameterizer = SQLParameterizer(
        parameterize_tables=parameterize_tables,
        parameterize_columns=True
    )
    parameterized_sql, params = parameterizer.parameterize(rec_norm["sql"])
    
    # Kalite kontrolü
    is_valid, err_msg, quality_score = validate_tool_advanced(
        parameterized_sql, params, rec_norm["question"], min_score=min_score
    )
    
    if not is_valid:
        return {}, err_msg
    
    # Tool ismi oluştur
    smart_name = generate_smart_tool_name(parameterized_sql, rec_norm["question"])
    key = f"{smart_name}_{sha(rec_norm['sql'] + rec_norm['question'], n=4)}"
    
    # Description oluştur (question kullanmadan)
    base_desc = generate_semantic_description(parameterized_sql, rec_norm["question"], params)
    labels_str = generate_labels(rec_norm["sql"])  # Original SQL for labels
    desc = f"{base_desc} [Labels: {labels_str}]" if labels_str else base_desc
    
    # Tool oluştur
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
