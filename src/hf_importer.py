#!/usr/bin/env python3
"""Hugging Face Dataset Importer for ToolMint"""

import os
import json
from typing import List, Dict, Any, Optional

def _convert_record_to_dict(record: Any) -> Dict[str, Any]:
    """Convert a record to dictionary"""
    result: Dict[str, Any] = {}
    for key, value in record.items():  # type: ignore
        result[key] = value
    return result

def import_from_hf_dataset(
    dataset_name: str,
    split: str = "train",
    cache_dir: Optional[str] = None,
    streaming: bool = False
) -> List[Dict[str, Any]]:
    """
    Import dataset from Hugging Face Hub
    
    Args:
        dataset_name: Hugging Face dataset name (e.g., "spider", "wikisql")
        split: Which split to download (train, validation, test)
        cache_dir: Directory to cache the dataset
        streaming: Whether to stream the dataset (for large datasets)
        
    Returns:
        List of records from the dataset
    """
    from datasets import load_dataset  # type: ignore
    
    # Load dataset from Hugging Face
    dataset = load_dataset(
        dataset_name,
        split=split,
        cache_dir=cache_dir,
        streaming=streaming
    )
    
    # Convert to list of dictionaries
    result_records = []
    
    # Handle both streaming and non-streaming datasets
    if streaming:
        for hf_record in dataset:
            result_records.append(_convert_record_to_dict(hf_record))
    else:
        # Use to_list() method if available, otherwise iterate
        if hasattr(dataset, 'to_list'):
            result_records = dataset.to_list()  # type: ignore
        else:
            for hf_record in dataset:
                result_records.append(_convert_record_to_dict(hf_record))
    
    return result_records


def search_available_datasets(query: str = "sql") -> List[Dict[str, str]]:
    """
    Search for available datasets on Hugging Face
    
    Args:
        query: Search query (e.g., "sql", "text-to-sql", "code")
        
    Returns:
        List of dataset info dicts with name, description, downloads
    """
    try:
        from huggingface_hub import HfApi
        
        api = HfApi()
        datasets_list = api.list_datasets(search=query, sort="downloads", direction=-1)
        
        results = []
        for dataset_info in datasets_list:
            results.append({
                "name": dataset_info.id,
                "description": dataset_info.gated,
                "downloads": getattr(dataset_info, "downloads", 0)
            })
        
        return results[:20]  # Return top 20 results
        
    except ImportError:
        raise ImportError(
            "huggingface_hub not installed. Install with: pip install huggingface_hub"
        )
    except Exception as e:
        raise Exception(f"Failed to search datasets: {str(e)}")


# Dataset profiles for known Hugging Face datasets
DATASET_PROFILES = {
    "spider": {
        "question_fields": ["question"],
        "sql_fields": ["query"],
        "db_id_fields": ["db_id"]
    },
    "gretelai/synthetic_text_to_sql": {
        "question_fields": ["sql_prompt"],
        "sql_fields": ["sql"],
        "db_id_fields": ["domain"]
    },
    # Add more profiles as needed
}

def _detect_sql_field(record: Dict[str, Any]) -> Optional[str]:
    """
    Intelligently detect which field contains SQL code.
    Returns the field name with highest SQL likelihood score.
    """
    sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", 
                   "WITH", "FROM", "WHERE", "JOIN", "GROUP", "ORDER", "HAVING", "UNION"]
    
    sql_operators = ["COUNT", "SUM", "AVG", "MAX", "MIN", "DISTINCT", "AS", "ON", "IN", "LIKE"]
    
    best_field = None
    best_score = 0
    
    for field_name, field_value in record.items():
        if not isinstance(field_value, str):
            continue
            
        score = 0
        
        # High priority: "sql" in field name
        if "sql" in field_name.lower():
            score += 20
        
        # Check for multiple SQL keywords (strong indicator)
        value_upper = field_value.upper()
        keyword_count = 0
        for keyword in sql_keywords:
            if keyword in value_upper:
                keyword_count += 1
                score += 3
        
        # Multiple keywords = very likely SQL
        if keyword_count >= 3:
            score += 15
        elif keyword_count >= 2:
            score += 8
        
        # Check for SQL operators
        operator_count = 0
        for operator in sql_operators:
            if operator in value_upper:
                operator_count += 1
                score += 2
        
        # Check for SQL-specific patterns
        if "FROM" in value_upper and "SELECT" in value_upper:
            score += 10
        if "JOIN" in value_upper:
            score += 5
        if "WHERE" in value_upper:
            score += 5
        if "GROUP BY" in value_upper or "ORDER BY" in value_upper:
            score += 5
        
        # Medium priority: "query" or "statement" in name
        if "query" in field_name.lower() and "sql" not in field_name.lower():
            score += 8
        elif "statement" in field_name.lower():
            score += 8
        
        # Check for schema elements that suggest SQL
        if any(word in value_upper for word in ["TABLE", "COLUMN", "INDEX", "VIEW"]):
            score += 5
        
        if score > best_score:
            best_score = score
            best_field = field_name
    
    return best_field if best_score > 0 else None

def _detect_question_field(record: Dict[str, Any]) -> Optional[str]:
    """
    Intelligently detect which field contains question/natural language.
    Returns the field name with highest question likelihood score.
    """
    question_words = ["what", "how", "which", "who", "when", "where", "why", "can", "could", "should", "would"]
    imperative_words = ["list", "show", "tell", "find", "get", "give", "display", "return", "retrieve", "fetch", "extract"]
    
    best_field = None
    best_score = 0
    
    for field_name, field_value in record.items():
        if not isinstance(field_value, str):
            continue
            
        score = 0
        value_lower = field_value.lower()
        value_stripped = value_lower.strip()
        
        # High priority: Check for question mark
        if "?" in field_value:
            score += 20
        
        # Check for question words (multiple = stronger indicator)
        question_word_count = 0
        for word in question_words:
            if word in value_lower:
                question_word_count += 1
                score += 3
        
        # Multiple question words = very likely natural language
        if question_word_count >= 2:
            score += 10
        elif question_word_count >= 1:
            score += 5
        
        # Check for imperative words (task-oriented language)
        imperative_count = 0
        for word in imperative_words:
            if word in value_lower:
                imperative_count += 1
                score += 2
        
        # Multiple imperative words = likely natural language instruction
        if imperative_count >= 2:
            score += 8
        
        # Check for natural language patterns
        if value_stripped.startswith(("what", "how", "which", "who", "when", "where", "why")):
            score += 10
        if " please " in value_lower or "please " in value_stripped:
            score += 5
        if any(phrase in value_lower for phrase in ["i want", "i need", "give me", "show me"]):
            score += 5
        
        # High priority: Fields with "question", "prompt", "instruction" in name
        if "question" in field_name.lower():
            score += 15
        elif "prompt" in field_name.lower():
            score += 12
        elif "instruction" in field_name.lower():
            score += 12
        # Medium priority: Natural language indicator fields
        elif "text" in field_name.lower():
            score += 5
        elif "nl" in field_name.lower() or "natural" in field_name.lower():
            score += 8
        # Check for user intent fields
        elif any(word in field_name.lower() for word in ["user", "input", "query", "request"]):
            score += 6
        
        # Negative scoring for fields that are clearly not natural language
        # SQL-like content in the field
        value_upper = field_value.upper()
        if any(sql_word in value_upper for sql_word in ["SELECT", "FROM", "WHERE", "JOIN"]):
            score -= 10
        if "CREATE TABLE" in value_upper or "INSERT INTO" in value_upper:
            score -= 10
        
        # Ensure non-negative score
        score = max(0, score)
        
        if score > best_score:
            best_score = score
            best_field = field_name
    
    return best_field if best_score > 0 else None

def normalize_hf_dataset(records: List[Dict], dataset_name: str = "auto", dataset_type: str = "auto") -> List[Dict[str, Any]]:
    """
    Normalize records from Hugging Face datasets to ToolMint format
    
    Args:
        records: List of records from HF dataset
        dataset_name: Dataset name for profile matching
        dataset_type: Type of dataset (auto, spider, wikisql, etc.) - deprecated
        
    Returns:
        Normalized records in ToolMint format
    """
    if not records:
        return []
    
    normalized = []
    
    # Detect if we have a profile for this dataset
    profile = None
    if dataset_name and dataset_name != "auto":
        # Try exact match first
        if dataset_name in DATASET_PROFILES:
            profile = DATASET_PROFILES[dataset_name]
        # Try partial match (e.g., "gretelai/synthetic_text_to_sql")
        else:
            for profile_name in DATASET_PROFILES:
                if profile_name in dataset_name or dataset_name in profile_name:
                    profile = DATASET_PROFILES[profile_name]
                    break
    
    # Use profile or detect fields from first record
    use_detection = profile is None
    if use_detection:
        # Detect fields from first record
        first_record = records[0]
        detected_question_field = _detect_question_field(first_record)
        detected_sql_field = _detect_sql_field(first_record)
    else:
        detected_question_field = None
        detected_sql_field = None
    
    for i, record in enumerate(records):
        try:
            question = ""
            sql = ""
            
            if profile:
                # Use profile field mappings
                question_fields = profile.get("question_fields", [])
                sql_fields = profile.get("sql_fields", [])
                
                for field in question_fields:
                    if field in record and record[field]:
                        question = str(record[field])
                        break
                
                for field in sql_fields:
                    if field in record and record[field]:
                        sql = str(record[field])
                        break
                        
            else:
                # Use detected fields
                if detected_question_field and detected_question_field in record:
                    question = str(record[detected_question_field])
                else:
                    # Fallback to old method for compatibility
                    question = (
                        record.get("question") or
                        record.get("query") or
                        record.get("nl") or
                        record.get("instruction") or
                        record.get("text") or
                        ""
                    )
                
                if detected_sql_field and detected_sql_field in record:
                    sql = str(record[detected_sql_field])
                else:
                    # Fallback to old method for compatibility
                    sql = (
                        record.get("sql") or
                        record.get("query") or
                        record.get("gold_sql") or
                        record.get("gold") or
                        record.get("pred_sql") or
                        ""
                    )
            
            # Get db_id
            if profile:
                db_id_fields = profile.get("db_id_fields", [])
                db_id = ""
                for field in db_id_fields:
                    if field in record and record[field]:
                        db_id = str(record[field])
                        break
            else:
                db_id = record.get("db_id") or record.get("db") or record.get("schema") or ""
            
            source = "huggingface"
            
            # Only add if both question and sql are present
            if question and sql:
                normalized.append({
                    "question": question.strip(),
                    "sql": sql.strip(),
                    "db_id": db_id,
                    "source": source
                })
                
        except Exception as e:
            print(f"Warning: Failed to normalize record {i}: {e}")
            continue
    
    return normalized


def save_hf_dataset_to_jsonl(records: List[Dict], output_path: str):
    """
    Save normalized records to JSONL file
    
    Args:
        records: List of normalized records
        output_path: Path to save JSONL file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

