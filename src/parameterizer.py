#!/usr/bin/env python3
"""SQL Parameterizer class for ToolMint"""

import re
from typing import Dict, Any, List, Tuple, Set

class SQLParameterizer:
    """Parse SQL and parameterize literal values"""
    
    def __init__(self, parameterize_tables=True, parameterize_columns=True, min_params=2):
        self.parameterize_tables = parameterize_tables
        self.parameterize_columns = parameterize_columns
        self.min_params = min_params
        self.params = []
        self.param_names: Set[str] = set()
        
    def _make_param_name(self, base: str, typ: str) -> str:
        """Generate a unique parameter name without registering it"""
        # Map special keywords to context-free names
        name_map = {
            "limit": "limit_n",
            "offset": "offset_n",
        }
        base = name_map.get(base, base)
        
        if base not in self.param_names:
            return base
        
        # Append a numeric suffix if the name already exists
        i = 1
        while f"{base}_{i}" in self.param_names:
            i += 1
        return f"{base}_{i}"
    
    def _add_param(self, name: str, typ: str, desc: str, default_value: Any = None):
        """Register a parameter"""
        if name in self.param_names:
            return  # Already present
        self.param_names.add(name)
        param = {"name": name, "type": typ, "description": desc}
        if default_value is not None:
            param["description"] = f"{desc} (e.g., {default_value})"
        self.params.append(param)
    
    def parameterize(self, sql: str) -> Tuple[str, List[Dict[str,Any]]]:
        """Parameterize the SQL statement"""
        if not sql or not sql.strip():
            return sql, []
        
        self.params = []
        self.param_names = set()
        
        # 1. Parameterize string literals
        sql = self._parameterize_strings(sql)
        
        # 2. Parameterize numeric values
        sql = self._parameterize_numbers(sql)
        
        # 3. Parameterize table names (optional)
        if self.parameterize_tables:
            sql = self._parameterize_tables_names(sql)
        
        # 4. Parameterize column names in the SELECT clause
        if self.parameterize_columns:
            sql = self._parameterize_select_columns(sql)
        
        # 5. Parameterize column names in WHERE clauses
        if self.parameterize_columns:
            sql = self._parameterize_where_columns(sql)
        
        # 6. Parameterize column names in JOIN ON clauses
        if self.parameterize_columns:
            sql = self._parameterize_join_columns(sql)
        
        # 7. Parameterize GROUP BY clauses
        sql = self._parameterize_group_by(sql)
        
        # 8. Handle special cases: LIMIT, OFFSET, ORDER BY
        sql = self._parameterize_special_clauses(sql)
        
        return sql, self.params
    
    def _parameterize_strings(self, sql: str) -> str:
        """Parameterize string literals wrapped in single or double quotes"""
        def replacer(match):
            value = match.group(1)
            
            # Skip values that are too short or represent sentinel keywords
            if len(value) <= 1 or value.upper() in ['ASC', 'DESC', 'YES', 'NO', 'Y', 'N']:
                return match.group(0)
            
            # Handle LIKE patterns containing % specially
            if '%' in value:
                # Covers patterns like "8/%"
                base_value = value.replace('%', '').replace('/', '_').strip('_')
                safe_value = re.sub(r'[^a-z0-9]+', '_', base_value.lower()).strip('_')[:20]
                param_name = self._make_param_name(safe_value or "pattern", "string")
                # Preserve the original pattern in the description
                self._add_param(param_name, "string", f"String pattern for LIKE", value)
                return f"{{{{.{param_name}}}}}"
            
            # Derive a meaningful parameter name
            safe_value = re.sub(r'[^a-z0-9]+', '_', value.lower()).strip('_')[:20]
            param_name = self._make_param_name(safe_value or "str_value", "string")
            
            self._add_param(param_name, "string", f"String value", value)
            return f"{{{{.{param_name}}}}}"
        
        # Process double quotes first
        sql = re.sub(r'"([^"]+)"', replacer, sql)
        # Then handle single quotes
        sql = re.sub(r"'([^']+)'", replacer, sql)
        
        return sql
    
    def _parameterize_numbers(self, sql: str) -> str:
        """Parameterize numeric literals in WHERE/HAVING/BETWEEN contexts"""
        # LIMIT and OFFSET are handled separately
        pattern = r'\b(\d+(?:\.\d+)?)\b'
        
        def replacer(match):
            value = match.group(1)
            pos = match.start()
            
            # Inspect the previous 40 characters to determine context
            before = sql[max(0, pos-40):pos].upper()
            
            # Skip LIMIT/OFFSET occurrences
            if 'LIMIT' in before or 'OFFSET' in before:
                return match.group(0)
            
            # Check for WHERE/HAVING/BETWEEN or comparison operators
            if any(kw in before for kw in ['WHERE', 'HAVING', 'BETWEEN', '>', '<', '=', '!=', '<>', '>=', '<=']):
                # Generate a parameter name for the numeric value
                if '.' in value:
                    param_name = self._make_param_name("threshold", "string")
                    typ = "string"
                else:
                    param_name = self._make_param_name("value", "string")
                    typ = "string"
                
                self._add_param(param_name, typ, f"Numeric value", value)
                return f"{{{{.{param_name}}}}}"
            
            return match.group(0)
        
        return re.sub(pattern, replacer, sql)
    
    def _parameterize_tables_names(self, sql: str) -> str:
        """Parameterize table names following FROM/JOIN/INTO/UPDATE"""
        # Use generic context-free names like table, table_1, table_2
        
        def from_replacer(match):
            keyword = match.group(1)
            table = match.group(2)
            
            # Skip subqueries or function calls
            if '(' in table or table.upper() in ['SELECT', 'VALUES']:
                return match.group(0)
            
            # Use a neutral table parameter name
            param_name = self._make_param_name("table", "string")
            self._add_param(param_name, "string", f"Table name", table)
            return f"{keyword} {{{{.{param_name}}}}}"
        
        sql = re.sub(r'\b(FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][\w]*)', from_replacer, sql, flags=re.I)
        return sql
    
    def _parameterize_select_columns(self, sql: str) -> str:
        """Parameterize column names inside SELECT clauses"""
        # Targets simple column lists (non-aggregate expressions)
        
        def select_replacer(match):
            select_kw = match.group(1)
            columns_str = match.group(2)
            from_kw = match.group(3)
            
            # Leave SELECT * unchanged
            if columns_str.strip() == '*':
                return match.group(0)
            
            # Avoid modifying aggregates such as COUNT, SUM, etc.
            if re.search(r'\b(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT|DISTINCT)\s*\(', columns_str, re.I):
                return match.group(0)
            
            # Split comma-separated columns
            columns = [c.strip() for c in columns_str.split(',')]
            
            parameterized_cols = []
            for i, col in enumerate(columns, 1):
                # Keep aliases and table.column references intact
                if ' AS ' in col.upper() or '.' in col:
                    parameterized_cols.append(col)
                    continue
                
                # Parameterize simple identifiers
                if re.match(r'^[a-zA-Z_][\w]*$', col):
                    param_name = self._make_param_name(f"select_col_{i}" if i > 1 else "select_col", "string")
                    self._add_param(param_name, "string", f"Column to select", col)
                    parameterized_cols.append(f"{{{{.{param_name}}}}}")
                else:
                    parameterized_cols.append(col)
            
            return f"{select_kw} {', '.join(parameterized_cols)} {from_kw}"
        
        # SELECT ... FROM pattern'i yakala
        sql = re.sub(
            r'\b(SELECT)\s+(.*?)\s+(FROM)\b',
            select_replacer,
            sql,
            flags=re.I | re.DOTALL
        )
        
        return sql
    
    def _parameterize_group_by(self, sql: str) -> str:
        """Parameterize column names inside GROUP BY clauses"""
        
        def group_replacer(match):
            group_kw = match.group(1)
            columns_str = match.group(2)
            
            # Leave untouched if already parameterized
            if '{{.' in columns_str:
                return match.group(0)
            
            # Split comma-separated column list
            columns = [c.strip() for c in columns_str.split(',')]
            
            parameterized_cols = []
            for i, col in enumerate(columns, 1):
                # Skip when functions are present
                if '(' in col:
                    parameterized_cols.append(col)
                    continue
                
                # For table.column formats, parameterize only the column part
                if '.' in col:
                    parts = col.split('.')
                    if len(parts) == 2:
                        table_ref = parts[0]
                        col_name = parts[1]
                        param_name = self._make_param_name(f"group_col_{i}" if i > 1 else "group_col", "string")
                        self._add_param(param_name, "string", f"Column to group by", col_name)
                        parameterized_cols.append(f"{table_ref}.{{{{.{param_name}}}}}")
                    else:
                        parameterized_cols.append(col)
                    continue
                
                # Handle simple identifiers
                if re.match(r'^[a-zA-Z_][\w]*$', col):
                    param_name = self._make_param_name(f"group_col_{i}" if i > 1 else "group_col", "string")
                    self._add_param(param_name, "string", f"Column to group by", col)
                    parameterized_cols.append(f"{{{{.{param_name}}}}}")
                else:
                    parameterized_cols.append(col)
            
            return f"{group_kw} {', '.join(parameterized_cols)}"
        
        # GROUP BY pattern stops before ORDER BY/LIMIT/OFFSET
        sql = re.sub(
            r'\b(GROUP\s+BY)\s+([^;]+?)(?=\s+(?:ORDER|HAVING|LIMIT|;|$))',
            group_replacer,
            sql,
            flags=re.I
        )
        
        return sql
    
    def _parameterize_special_clauses(self, sql: str) -> str:
        """Parameterize special clauses such as LIMIT, OFFSET, and ORDER BY"""
        
        # LIMIT n
        def limit_replacer(match):
            value = match.group(1)
            if '{{.' in value:  # Already parameterized
                return match.group(0)
            param_name = "limit_n"
            self._add_param(param_name, "string", f"Maximum number of rows", value)
            return f"LIMIT {{{{.{param_name}}}}}"
        
        sql = re.sub(r'\bLIMIT\s+(\d+)', limit_replacer, sql, flags=re.I)
        
        # OFFSET n
        def offset_replacer(match):
            value = match.group(1)
            if '{{.' in value:
                return match.group(0)
            param_name = "offset_n"
            self._add_param(param_name, "string", f"Number of rows to skip", value)
            return f"OFFSET {{{{.{param_name}}}}}"
        
        sql = re.sub(r'\bOFFSET\s+(\d+)', offset_replacer, sql, flags=re.I)
        
        # ORDER BY column/expression [ASC|DESC]
        def order_replacer(match):
            expr = match.group(1).strip()
            direction = match.group(2) if match.lastindex >= 2 else ""
            
            if '{{.' in expr:  # Already parameterized
                return match.group(0)
            
            # If the expression is a function (COUNT(*), MAX(col), etc.) leave it as-is
            if '(' in expr and ')' in expr:
                # Allow direction to be parameterized
                if direction and direction.strip():
                    dir_param = "order_dir"
                    self._add_param(dir_param, "string", f"Sort direction (ASC/DESC)", direction.strip())
                    return f"ORDER BY {expr} {{{{.{dir_param}}}}}"
                return match.group(0)
            
            # Parameterize simple column identifiers
            param_name = "order_col"
            self._add_param(param_name, "string", f"Column to order by", expr)
            
            result = f"ORDER BY {{{{.{param_name}}}}}"
            
            # Parameterize the direction token if present
            if direction and direction.strip():
                dir_param = "order_dir"
                self._add_param(dir_param, "string", f"Sort direction (ASC/DESC)", direction.strip())
                result += f" {{{{.{dir_param}}}}}"
            
            return result
        
        # Match: ORDER BY expression [ASC|DESC]
        # expression can be: column_name, COUNT(*), MAX(col), AVG(field), etc.
        # Regex explanation:
        # - [a-zA-Z_][\w\.]* : column or function name prefix
        # - (?:\([^)]*\))? : optional parentheses and contents for functions
        # Non-greedy to correctly capture COUNT(*) DESC patterns
        sql = re.sub(
            r'\bORDER\s+BY\s+([a-zA-Z_][\w\.]*(?:\([^)]*\))?)\s*(ASC|DESC)?',
            order_replacer,
            sql,
            flags=re.I
        )
        
        return sql
    
    def _parameterize_where_columns(self, sql: str) -> str:
        """Parameterize column names that appear in WHERE clauses"""
        # Handles patterns like WHERE column = value, WHERE column IN (...), etc.
        
        def where_replacer(match):
            where_kw = match.group(1)
            column = match.group(2)
            operator = match.group(3)
            
            # Skip columns that are already parameterized
            if '{{.' in column:
                return match.group(0)
            
            # Skip function expressions such as COUNT(*)
            if '(' in column:
                return match.group(0)
            
            # For table.column references, only parameterize the column part
            if '.' in column:
                parts = column.split('.')
                if len(parts) == 2:
                    table_ref = parts[0]
                    col_name = parts[1]
                    param_name = self._make_param_name("where_col", "string")
                    self._add_param(param_name, "string", f"Column to filter on", col_name)
                    return f"{where_kw} {table_ref}.{{{{.{param_name}}}}} {operator}"
                return match.group(0)
            
            # Handle simple column identifiers
            if re.match(r'^[a-zA-Z_][\w]*$', column):
                param_name = self._make_param_name("where_col", "string")
                self._add_param(param_name, "string", f"Column to filter on", column)
                return f"{where_kw} {{{{.{param_name}}}}} {operator}"
            
            return match.group(0)
        
        # Supported operators: =, !=, <>, >, <, >=, <=, IN, NOT IN, LIKE, NOT LIKE, IS, IS NOT
        sql = re.sub(
            r'\b(WHERE)\s+([a-zA-Z_][\w\.]*)\s+(=|!=|<>|>=|<=|>|<|IN|NOT\s+IN|LIKE|NOT\s+LIKE|IS|IS\s+NOT)\b',
            where_replacer,
            sql,
            flags=re.I
        )
        
        return sql
    
    def _parameterize_join_columns(self, sql: str) -> str:
        """Parameterize column names in JOIN ... ON clauses"""
        # Example: JOIN table ON t1.col1 = t2.col2
        
        def join_replacer(match):
            on_kw = match.group(1)
            left_col = match.group(2)
            operator = match.group(3)
            right_col = match.group(4)
            
            # If either side is already parameterized, leave as-is
            if '{{.' in left_col or '{{.' in right_col:
                return match.group(0)
            
            # Left-hand side
            left_result = left_col
            if '.' in left_col:
                parts = left_col.split('.')
                if len(parts) == 2:
                    table_ref = parts[0]
                    col_name = parts[1]
                    param_name = self._make_param_name("join_col", "string")
                    self._add_param(param_name, "string", f"Column to join on", col_name)
                    left_result = f"{table_ref}.{{{{.{param_name}}}}}"
            elif re.match(r'^[a-zA-Z_][\w]*$', left_col):
                param_name = self._make_param_name("join_col", "string")
                self._add_param(param_name, "string", f"Column to join on", left_col)
                left_result = f"{{{{.{param_name}}}}}"
            
            # Right-hand side
            right_result = right_col
            if '.' in right_col:
                parts = right_col.split('.')
                if len(parts) == 2:
                    table_ref = parts[0]
                    col_name = parts[1]
                    param_name = self._make_param_name("join_col", "string")
                    self._add_param(param_name, "string", f"Column to join on", col_name)
                    right_result = f"{table_ref}.{{{{.{param_name}}}}}"
            elif re.match(r'^[a-zA-Z_][\w]*$', right_col):
                param_name = self._make_param_name("join_col", "string")
                self._add_param(param_name, "string", f"Column to join on", right_col)
                right_result = f"{{{{.{param_name}}}}}"
            
            return f"{on_kw} {left_result} {operator} {right_result}"
        
        # ON t1.col1 = t2.col2
        sql = re.sub(
            r'\b(ON)\s+([a-zA-Z_][\w\.]+)\s*(=|!=|<>|>=|<=|>|<)\s*([a-zA-Z_][\w\.]+)',
            join_replacer,
            sql,
            flags=re.I
        )
        
        return sql
