#!/usr/bin/env python3
"""Quality scoring functions for ToolMint"""

import re
from typing import Dict, Any, List, Tuple

def calculate_parameter_score(params: List[Dict]) -> float:
    """Parametre kalitesi: 0-40 puan"""
    if not params:
        return 0.0
    
    score = 0.0
    
    # Parametre sayısı (max 15 puan)
    param_count = len(params)
    if param_count >= 5:
        score += 15
    elif param_count >= 3:
        score += 10
    elif param_count >= 1:
        score += 5
    
    # Parametre çeşitliliği (max 15 puan)
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
    
    # Her farklı tür 3 puan (max 5 tür × 3 = 15)
    score += min(len(param_types) * 3, 15)
    
    # Type diversity (max 10 puan)
    type_set = {p['type'] for p in params}
    score += min(len(type_set) * 5, 10)
    
    return min(score, 40)

def calculate_complexity_score(sql: str) -> float:
    """SQL karmaşıklığı: 0-30 puan"""
    sql_upper = sql.upper()
    score = 0.0
    
    # Temel SELECT: 5 puan
    if 'SELECT' in sql_upper:
        score += 5
    
    # JOIN: +8 puan
    if 'JOIN' in sql_upper:
        score += 8
        # Multiple JOINs: +2 puan
        join_count = sql_upper.count('JOIN')
        score += min(join_count - 1, 2) * 2
    
    # GROUP BY: +7 puan
    if 'GROUP BY' in sql_upper:
        score += 7
    
    # Aggregate functions: +5 puan
    aggregates = ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']
    if any(agg in sql_upper for agg in aggregates):
        score += 5
    
    # WHERE + HAVING: +3 puan
    if 'WHERE' in sql_upper:
        score += 2
    if 'HAVING' in sql_upper:
        score += 3
    
    # Subquery: +5 puan
    if sql.count('SELECT') > 1:  # Nested SELECT
        score += 5
    
    # DISTINCT: +2 puan
    if 'DISTINCT' in sql_upper:
        score += 2
    
    return min(score, 30)

def calculate_description_score(question: str, sql: str) -> float:
    """Description kalitesi: 0-20 puan"""
    if not question:
        return 0.0
    
    score = 0.0
    
    # Uzunluk (min 10 puan)
    if len(question) >= 100:
        score += 10
    elif len(question) >= 50:
        score += 7
    elif len(question) >= 20:
        score += 4
    else:
        score += 2
    
    # Anahtar kelimeler içeriyor mu? (max 10 puan)
    keywords = ['how many', 'what', 'which', 'list', 'show', 'return', 'find', 
                'calculate', 'count', 'average', 'maximum', 'minimum', 'total']
    keyword_count = sum(1 for kw in keywords if kw in question.lower())
    score += min(keyword_count * 2, 10)
    
    return min(score, 20)

def calculate_reusability_score(sql: str, params: List[Dict]) -> float:
    """Yeniden kullanılabilirlik: 0-10 puan"""
    score = 10.0
    
    # Hardcoded değerler varsa puan kaybı
    # String literals (tek veya çift tırnak)
    if re.search(r"'[^']{2,}'", sql) or re.search(r'"[^"]{2,}"', sql):
        score -= 3
    
    # Hardcoded sayılar (LIMIT/OFFSET hariç)
    sql_without_params = re.sub(r'\{\{\.[\w]+\}\}', '', sql)
    if re.search(r'\b\d{2,}\b', sql_without_params):  # 10+ gibi sayılar
        score -= 2
    
    # Sabit tablo/sütun adları (parametreleştirilmemiş)
    if re.search(r'\bFROM\s+[a-zA-Z_]\w+(?!\s*\()', sql) and '{{.table' not in sql:
        score -= 2
    
    return max(score, 0)

def calculate_tool_quality_score(sql: str, params: List[Dict], question: str) -> Tuple[float, Dict[str, Any]]:
    """
    Tool kalitesini 0-100 arası puanla.
    Return: (score, breakdown_dict)
    """
    score = 0.0
    breakdown = {}
    
    # 1. PARAMETRE PUANI (40 puan)
    param_score = calculate_parameter_score(params)
    score += param_score
    breakdown["parameters"] = param_score
    
    # 2. SQL KARMAŞIKLIĞI PUANI (30 puan)
    complexity_score = calculate_complexity_score(sql)
    score += complexity_score
    breakdown["complexity"] = complexity_score
    
    # 3. AÇIKLAMA KALİTESİ (20 puan)
    description_score = calculate_description_score(question, sql)
    score += description_score
    breakdown["description"] = description_score
    
    # 4. YENİDEN KULLANILABİLİRLİK (10 puan)
    reusability_score = calculate_reusability_score(sql, params)
    score += reusability_score
    breakdown["reusability"] = reusability_score
    
    return score, breakdown

def describe_sql_structure(sql: str) -> str:
    """SQL'in ne yaptığını doğal dilde açıkla"""
    sql_upper = sql.upper()
    desc_parts = []
    
    # SELECT mi, INSERT mi, UPDATE mi?
    if 'SELECT' in sql_upper:
        desc_parts.append("Retrieves data")
        
        # Aggregate fonksiyonlar
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
    """Parametreleri kullanıcı dostu şekilde açıkla"""
    if not params:
        return ""
    
    # Parametre kategorileri
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
    Embedding LLM'ler için optimize edilmiş, zengin description oluştur.
    Amaç: Kullanıcı doğal dilde sorduğunda bu tool'u bulabilmek.
    Question kullanılmaz - sadece SQL yapısı ve parametreler.
    """
    parts = []
    
    # 1. SQL yapısını açıkla (ne yapıyor?)
    sql_desc = describe_sql_structure(sql)
    if sql_desc:
        parts.append(sql_desc)
    
    # 2. Parametreleri açıkla (ne özelleştirilebilir?)
    if params:
        param_desc = describe_parameters(params)
        if param_desc:
            parts.append(param_desc)
    
    # 3. Birleştir ve embedding-friendly yap
    description = ". ".join(parts)
    
    # Embedding için optimize et: 500 char limit
    return description[:500]
