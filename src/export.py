#!/usr/bin/env python3
"""Export functions for ToolMint - supports JSON, CSV, YAML formats"""

import json
import csv
import yaml
import os
from typing import Dict, Any, List

def export_tools_to_json(yaml_path: str, output_path: str):
    """Export tools from YAML file to JSON format"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        if data is None or not isinstance(data, dict):
            data = {}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def export_tools_to_csv(yaml_path: str, output_path: str):
    """Export tools from YAML file to CSV format"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        if data is None or not isinstance(data, dict):
            data = {}
    
    tools = data.get('tools', {})
    
    if not tools:
        # Create empty CSV with headers
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['tool_name', 'description', 'sql', 'param_count', 'quality_score', 'labels', 'db_id', 'source'])
        return
    
    # Flatten tools data
    rows = []
    for tool_name, tool_data in tools.items():
        params = tool_data.get('parameters', [])
        row = [
            tool_name,
            tool_data.get('description', ''),
            tool_data.get('sql', ''),
            len(params),
            tool_data.get('quality_score', 0),
            tool_data.get('labels', ''),
            tool_data.get('db_id', ''),
            tool_data.get('source', '')
        ]
        rows.append(row)
    
    # Write CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tool_name', 'description', 'sql', 'param_count', 'quality_score', 'labels', 'db_id', 'source'])
        writer.writerows(rows)

def export_tools_to_yaml(yaml_path: str, output_path: str):
    """Copy tools from source YAML to output YAML"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        if data is None or not isinstance(data, dict):
            data = {}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=1000)

def export_results_to_txt(results_dict: Dict[str, Any], output_path: str):
    """Export processing results summary to text file"""
    text = f"""Processing Results:
========================

Input File: {results_dict.get('input_file', 'N/A')}
Items Processed: {results_dict.get('items_processed', 0)}
Tools Created: {results_dict.get('tools_created', 0)}
Processing Time: {results_dict.get('processing_time', 'N/A')}

Configuration:
- Output File: {results_dict.get('output_file', 'N/A')}
- Tool Name: {results_dict.get('tool_name', 'N/A')}
- Description: {results_dict.get('description', 'N/A')}
- Author: {results_dict.get('author', 'N/A')}
- Version: {results_dict.get('version', 'N/A')}
- License: {results_dict.get('license', 'N/A')}

Processing Options:
- Quality Scoring: {results_dict.get('use_quality_scoring', False)}
- Parameterization: {results_dict.get('use_parameterization', False)}
- Labeling: {results_dict.get('use_labeling', False)}
- Min Quality Score: {results_dict.get('min_quality_score', 50)}
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

def export_results_to_json(results_dict: Dict[str, Any], output_path: str):
    """Export processing results summary to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)

