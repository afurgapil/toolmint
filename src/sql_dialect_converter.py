#!/usr/bin/env python3
"""SQL Dialect Converter for ToolMint - Converts SQL between different dialects"""

import re
from typing import Dict, Any, List, Tuple

class SQLDialectConverter:
    """Converts SQL queries from one dialect to another"""
    
    def __init__(self, target_dialect: str):
        """
        Initialize converter for target dialect
        
        Args:
            target_dialect: One of 'mysql', 'postgres', 'sqlite', 'sql_server'
        """
        self.target_dialect = target_dialect.lower()
        
        # Dialect mappings
        self.dialects = {
            'mysql': 'mysql',
            'postgres': 'postgres',
            'postgresql': 'postgres',
            'sqlite': 'sqlite',
            'sql_server': 'sql_server',
            'mssql': 'sql_server'
        }
        
        # Normalize dialect name
        self.target_dialect = self.dialects.get(self.target_dialect, 'mysql')
        
        # Parameter styles for each dialect
        self.param_styles = {
            'mysql': '?',
            'postgres': '$',
            'sqlite': '?',
            'sql_server': '@'
        }
    
    def convert(self, sql: str, params: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        Convert SQL and parameters to target dialect
        
        Args:
            sql: SQL query with {{.param}} placeholders
            params: List of parameter dictionaries
            
        Returns:
            Tuple of (converted_sql, converted_params)
        """
        if not sql:
            return sql, params
        
        # Start with original
        converted_sql = sql
        converted_params = params.copy()
        
        # 1. Convert parameter style (highest priority)
        converted_sql, converted_params = self._convert_parameter_style(converted_sql, converted_params)
        
        # 2. Convert LIMIT/OFFSET syntax
        converted_sql = self._convert_limit_offset(converted_sql)
        
        # 3. Convert date functions
        converted_sql = self._convert_date_functions(converted_sql)
        
        # 4. Convert string functions
        converted_sql = self._convert_string_functions(converted_sql)
        
        # 5. Convert data types (if schema statements detected)
        if re.search(r'\b(CREATE|ALTER)\b', converted_sql, re.I):
            converted_sql = self._convert_data_types(converted_sql)
        
        return converted_sql, converted_params
    
    def _convert_parameter_style(self, sql: str, params: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        Convert {{.param_name}} to dialect-specific parameter style
        
        - MySQL: ?
        - PostgreSQL: $1, $2, $3
        - SQLite: ?
        - SQL Server: @param_name
        """
        # Extract all parameter placeholders
        placeholders = re.findall(r'\{\{\.(\w+)\}\}', sql)
        
        if not placeholders:
            return sql, params
        
        style = self.param_styles.get(self.target_dialect, '?')
        converted_params = params.copy()
        
        if self.target_dialect in ['mysql', 'sqlite']:
            # MySQL/SQLite: Use ? for each parameter
            # Replace in order
            param_counter = 0
            for param_name in placeholders:
                placeholder_pattern = f'{{{{.{param_name}}}}}'
                sql = sql.replace(placeholder_pattern, '?', 1)
                param_counter += 1
        
        elif self.target_dialect == 'postgres':
            # PostgreSQL: Use $1, $2, $3, etc.
            param_counter = 1
            param_map = {}
            for param_name in placeholders:
                if param_name not in param_map:
                    param_map[param_name] = f'${param_counter}'
                    param_counter += 1
            
            # Replace placeholders with numbered parameters
            for param_name, pg_param in param_map.items():
                placeholder_pattern = f'{{{{.{param_name}}}}}'
                sql = sql.replace(placeholder_pattern, pg_param)
        
        elif self.target_dialect == 'sql_server':
            # SQL Server: Use @param_name
            for param_name in placeholders:
                placeholder_pattern = f'{{{{.{param_name}}}}}'
                sql = sql.replace(placeholder_pattern, f'@{param_name}')
            
            # Update parameter metadata to include @ prefix hint
            for param in converted_params:
                if param.get('name'):
                    param['_sql_server_name'] = f'@{param["name"]}'
        
        return sql, converted_params
    
    def _convert_limit_offset(self, sql: str) -> str:
        """
        Convert LIMIT/OFFSET syntax for different databases
        
        - MySQL/PostgreSQL/SQLite: LIMIT n OFFSET m
        - SQL Server: OFFSET m ROWS FETCH NEXT n ROWS ONLY
        """
        if self.target_dialect != 'sql_server':
            # MySQL/PostgreSQL/SQLite already use LIMIT/OFFSET - no change needed
            return sql
        
        # SQL Server conversion
        # Pattern: LIMIT n [OFFSET m] or OFFSET m LIMIT n
        def replace_limit_offset(match):
            limit_value = match.group(1)
            offset_match = re.search(r'OFFSET\s+(\d+)', sql[max(0, match.start()-30):match.end()+30], re.I)
            
            if offset_match:
                offset_value = offset_match.group(1)
                return f"OFFSET {offset_value} ROWS FETCH NEXT {limit_value} ROWS ONLY"
            else:
                return f"OFFSET 0 ROWS FETCH NEXT {limit_value} ROWS ONLY"
        
        # Replace LIMIT n (with optional OFFSET m)
        sql = re.sub(r'\bLIMIT\s+(\d+)', replace_limit_offset, sql, flags=re.I)
        
        # Replace standalone OFFSET (without LIMIT before it)
        sql = re.sub(r'\bOFFSET\s+(\d+)(?!\s+ROWS)', r'OFFSET \1 ROWS', sql, flags=re.I)
        
        return sql
    
    def _convert_date_functions(self, sql: str) -> str:
        """
        Convert date/time functions between dialects
        
        Common conversions:
        - NOW() -> GETDATE() (SQL Server)
        - CURDATE() -> CURRENT_DATE or GETDATE()
        - DATE_ADD/DATE_SUB -> DATEADD/DATEDIFF or INTERVAL
        """
        if self.target_dialect == 'sql_server':
            # MySQL to SQL Server
            sql = re.sub(r'\bNOW\(\)', 'GETDATE()', sql, flags=re.I)
            sql = re.sub(r'\bCURDATE\(\)', 'CAST(GETDATE() AS DATE)', sql, flags=re.I)
            sql = re.sub(r'\bCURTIME\(\)', 'CAST(GETDATE() AS TIME)', sql, flags=re.I)
            
            # DATE_ADD/DATE_SUB conversion (simplified - keep for basic cases)
            # DATE_ADD(date, INTERVAL n DAY) -> DATEADD(DAY, n, date)
            def date_add_converter(match):
                date_expr = match.group(1)
                interval_val = match.group(2)
                interval_type = match.group(3).upper()
                
                # Map MySQL INTERVAL types to SQL Server datepart
                datepart_map = {
                    'DAY': 'day', 'MONTH': 'month', 'YEAR': 'year',
                    'HOUR': 'hour', 'MINUTE': 'minute', 'SECOND': 'second'
                }
                datepart = datepart_map.get(interval_type, 'day')
                
                return f"DATEADD({datepart}, {interval_val}, {date_expr})"
            
            sql = re.sub(
                r'DATE_ADD\(([^,]+),\s*INTERVAL\s+(\d+)\s+(\w+)\)',
                date_add_converter,
                sql,
                flags=re.I
            )
        
        elif self.target_dialect == 'postgres':
            # MySQL to PostgreSQL
            sql = re.sub(r'\bCURDATE\(\)', 'CURRENT_DATE', sql, flags=re.I)
            sql = re.sub(r'\bCURTIME\(\)', 'CURRENT_TIME', sql, flags=re.I)
        
        elif self.target_dialect == 'sqlite':
            # MySQL to SQLite
            sql = re.sub(r'\bNOW\(\)', "datetime('now')", sql, flags=re.I)
            sql = re.sub(r'\bCURDATE\(\)', "date('now')", sql, flags=re.I)
            sql = re.sub(r'\bCURTIME\(\)', "time('now')", sql, flags=re.I)
            
            # DATE_ADD/DATE_SUB to SQLite strftime/date
            sql = re.sub(
                r'DATE_ADD\(([^,]+),\s*INTERVAL\s+(\d+)\s+DAY\)',
                r"date(\1, '+\\2 days')",
                sql,
                flags=re.I
            )
        
        return sql
    
    def _convert_string_functions(self, sql: str) -> str:
        """
        Convert string functions between dialects
        
        Common conversions:
        - CONCAT() vs || vs +
        - LENGTH() vs LEN()
        - SUBSTRING() vs SUBSTR()
        """
        if self.target_dialect == 'sql_server':
            # MySQL to SQL Server
            sql = re.sub(r'\bLENGTH\(', 'LEN(', sql, flags=re.I)
            
            # CONCAT is supported in SQL Server (2012+)
            # Keep CONCAT as is if it exists
        
        elif self.target_dialect == 'postgres':
            # PostgreSQL supports both CONCAT and ||
            # Keep as is
            pass
        
        elif self.target_dialect == 'sqlite':
            # SQLite uses || for concatenation
            # LENGTH is supported
            # Keep as is for most cases
            pass
        
        return sql
    
    def _convert_data_types(self, sql: str) -> str:
        """
        Convert data types in schema statements (CREATE, ALTER)
        
        Common conversions:
        - BOOLEAN types
        - AUTO_INCREMENT vs SERIAL vs IDENTITY
        - TEXT types
        """
        if self.target_dialect == 'sql_server':
            # BOOLEAN -> BIT
            sql = re.sub(r'\bBOOLEAN\b', 'BIT', sql, flags=re.I)
            
            # AUTO_INCREMENT -> IDENTITY(1,1)
            sql = re.sub(
                r'\bAUTO_INCREMENT\b',
                'IDENTITY(1,1)',
                sql,
                flags=re.I
            )
            
            # TINYINT(n) -> TINYINT
            sql = re.sub(r'\bTINYINT\(\d+\)', 'TINYINT', sql, flags=re.I)
        
        elif self.target_dialect == 'postgres':
            # BOOLEAN -> BOOLEAN (same, but handle syntax)
            # AUTO_INCREMENT -> SERIAL or IDENTITY
            sql = re.sub(
                r'\s+AUTO_INCREMENT',
                ' SERIAL',
                sql,
                flags=re.I
            )
        
        elif self.target_dialect == 'sqlite':
            # BOOLEAN -> INTEGER (SQLite doesn't have BOOLEAN)
            sql = re.sub(r'\bBOOLEAN\b', 'INTEGER', sql, flags=re.I)
            
            # AUTO_INCREMENT -> AUTOINCREMENT
            sql = re.sub(
                r'\bAUTO_INCREMENT\b',
                'AUTOINCREMENT',
                sql,
                flags=re.I
            )
        
        return sql

