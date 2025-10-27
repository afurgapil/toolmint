#!/usr/bin/env python3
"""I/O operations for ToolMint"""

import os
import json
import yaml
from typing import Dict, Any, List

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load records from JSONL file"""
    arr = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: 
                continue
            try: 
                arr.append(json.loads(line))
            except: 
                pass
    return arr

def save_jsonl(path: str, arr: List[Dict[str, Any]]):
    """Save records to JSONL file"""
    with open(path, "w", encoding="utf-8") as f:
        for r in arr:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def normalize(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize record structure from different datasets"""
    q = rec.get("question") or rec.get("prompt") or rec.get("nl") or rec.get("instruction") or ""
    sql = rec.get("sql") or rec.get("query") or rec.get("gold_sql") or rec.get("gold") or rec.get("pred_sql") or ""
    db = rec.get("db_id") or rec.get("db") or rec.get("schema") or ""
    src = rec.get("source") or rec.get("origin") or "unknown"
    return {"question": q.strip(), "sql": sql.strip(), "db_id": db, "source": src}

def merge_yaml(out_path: str, tools: List[Dict[str, Any]]):
    """Merge tools into YAML file"""
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                data = {}
    else:
        data = {}
    
    if "tools" not in data:
        data["tools"] = {}
    
    for t in tools:
        data["tools"].update(t)
    
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=1000)
