#!/usr/bin/env python3
"""SQL labeling functions for ToolMint"""

import re
from typing import List

def generate_sql_operation_labels(sql: str) -> List[str]:
    """Generate operation labels (SELECT, INSERT, UPDATE, etc.)"""
    labels = []
    sql_upper = sql.upper().strip()
    
    if sql_upper.startswith('SELECT'):
        labels.append('select')
    elif sql_upper.startswith('INSERT'):
        labels.append('insert')
    elif sql_upper.startswith('UPDATE'):
        labels.append('update')
    elif sql_upper.startswith('DELETE'):
        labels.append('delete')
    elif sql_upper.startswith('CREATE'):
        labels.append('create')
    elif sql_upper.startswith('ALTER'):
        labels.append('alter')
    elif sql_upper.startswith('DROP'):
        labels.append('drop')
    
    return labels

def generate_sql_structure_labels(sql: str) -> List[str]:
    """Generate structure labels (join, group, filter, etc.)"""
    labels = []
    sql_upper = sql.upper()
    
    # JOINs
    if 'INNER JOIN' in sql_upper or 'JOIN' in sql_upper:
        labels.append('join')
    if 'LEFT JOIN' in sql_upper:
        labels.append('left_join')
    if 'RIGHT JOIN' in sql_upper:
        labels.append('right_join')
    
    # Aggregates
    if re.search(r'\bCOUNT\s*\(', sql_upper):
        labels.append('count')
    if re.search(r'\bSUM\s*\(', sql_upper):
        labels.append('sum')
    if re.search(r'\bAVG\s*\(', sql_upper):
        labels.append('avg')
    if re.search(r'\b(MAX|MIN)\s*\(', sql_upper):
        labels.append('minmax')
    
    # Grouping and ordering
    if 'GROUP BY' in sql_upper:
        labels.append('grouped')
    if 'ORDER BY' in sql_upper:
        labels.append('sorted')
    if 'HAVING' in sql_upper:
        labels.append('having')
    
    # Filtering
    if 'WHERE' in sql_upper:
        labels.append('filtered')
    if 'DISTINCT' in sql_upper:
        labels.append('distinct')
    
    # Pagination
    if 'LIMIT' in sql_upper:
        labels.append('limited')
    if 'OFFSET' in sql_upper:
        labels.append('offset')
    
    # Subqueries
    if sql_upper.count('SELECT') > 1:
        labels.append('subquery')
    
    return labels

def generate_labels(sql: str) -> str:
    """Generate all labels and return as comma-separated string"""
    operation_labels = generate_sql_operation_labels(sql)
    structure_labels = generate_sql_structure_labels(sql)
    all_labels = operation_labels + structure_labels
    return ', '.join(all_labels) if all_labels else ''
