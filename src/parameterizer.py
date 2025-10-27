#!/usr/bin/env python3
"""SQL Parameterizer class for SQL Tool Generator"""

import re
from typing import Dict, Any, List, Tuple, Set

class SQLParameterizer:
    """SQL'i parse edip tüm literalleri parametreleştirir"""
    
    def __init__(self, parameterize_tables=True, parameterize_columns=True, min_params=2):
        self.parameterize_tables = parameterize_tables
        self.parameterize_columns = parameterize_columns
        self.min_params = min_params
        self.params = []
        self.param_names: Set[str] = set()
        
    def _make_param_name(self, base: str, typ: str) -> str:
        """Unique parametre ismi oluştur - sadece isim üretir, eklemez!"""
        # Özel isimler için mapping - context-free isimlendirme
        name_map = {
            "limit": "limit_n",
            "offset": "offset_n",
        }
        base = name_map.get(base, base)
        
        if base not in self.param_names:
            return base
        
        # Conflict varsa numara ekle
        i = 1
        while f"{base}_{i}" in self.param_names:
            i += 1
        return f"{base}_{i}"
    
    def _add_param(self, name: str, typ: str, desc: str, default_value: Any = None):
        """Parametre ekle"""
        if name in self.param_names:
            return  # Zaten var
        self.param_names.add(name)
        param = {"name": name, "type": typ, "description": desc}
        if default_value is not None:
            param["description"] = f"{desc} (e.g., {default_value})"
        self.params.append(param)
    
    def parameterize(self, sql: str) -> Tuple[str, List[Dict[str,Any]]]:
        """SQL'i parametreleştir"""
        if not sql or not sql.strip():
            return sql, []
        
        self.params = []
        self.param_names = set()
        
        # 1. String literalleri parametreleştir
        sql = self._parameterize_strings(sql)
        
        # 2. Sayısal değerleri parametreleştir
        sql = self._parameterize_numbers(sql)
        
        # 3. Tablo adlarını parametreleştir (opsiyonel)
        if self.parameterize_tables:
            sql = self._parameterize_tables_names(sql)
        
        # 4. Sütun adlarını parametreleştir (SELECT clause)
        if self.parameterize_columns:
            sql = self._parameterize_select_columns(sql)
        
        # 5. WHERE clause'daki sütunları parametreleştir
        if self.parameterize_columns:
            sql = self._parameterize_where_columns(sql)
        
        # 6. JOIN ON clause'daki sütunları parametreleştir
        if self.parameterize_columns:
            sql = self._parameterize_join_columns(sql)
        
        # 7. GROUP BY clause'ını parametreleştir
        sql = self._parameterize_group_by(sql)
        
        # 8. Özel durumlar: LIMIT, OFFSET, ORDER BY
        sql = self._parameterize_special_clauses(sql)
        
        return sql, self.params
    
    def _parameterize_strings(self, sql: str) -> str:
        """String literalleri (tek ve çift tırnak) parametreleştir"""
        def replacer(match):
            value = match.group(1)
            
            # Çok kısa veya özel değerleri atla
            if len(value) <= 1 or value.upper() in ['ASC', 'DESC', 'YES', 'NO', 'Y', 'N']:
                return match.group(0)
            
            # % içeren LIKE pattern'leri özel işle
            if '%' in value:
                # "8/%" gibi pattern'ler için
                base_value = value.replace('%', '').replace('/', '_').strip('_')
                safe_value = re.sub(r'[^a-z0-9]+', '_', base_value.lower()).strip('_')[:20]
                param_name = self._make_param_name(safe_value or "pattern", "string")
                # Description'da % pattern'ini göster
                self._add_param(param_name, "string", f"String pattern for LIKE", value)
                return f"{{{{.{param_name}}}}}"
            
            # Anlamlı isim üret
            safe_value = re.sub(r'[^a-z0-9]+', '_', value.lower()).strip('_')[:20]
            param_name = self._make_param_name(safe_value or "str_value", "string")
            
            self._add_param(param_name, "string", f"String value", value)
            return f"{{{{.{param_name}}}}}"
        
        # Hem tek hem çift tırnak için
        # Önce çift tırnak
        sql = re.sub(r'"([^"]+)"', replacer, sql)
        # Sonra tek tırnak
        sql = re.sub(r"'([^']+)'", replacer, sql)
        
        return sql
    
    def _parameterize_numbers(self, sql: str) -> str:
        """Sayısal literalleri parametreleştir (WHERE, HAVING, BETWEEN context'inde)"""
        # LIMIT ve OFFSET hariç (onlar ayrı işlenecek)
        pattern = r'\b(\d+(?:\.\d+)?)\b'
        
        def replacer(match):
            value = match.group(1)
            pos = match.start()
            
            # Önceki 40 karakteri kontrol et
            before = sql[max(0, pos-40):pos].upper()
            
            # LIMIT/OFFSET ise atla (ayrı işlenecek)
            if 'LIMIT' in before or 'OFFSET' in before:
                return match.group(0)
            
            # WHERE, HAVING, BETWEEN, karşılaştırma operatörleri kontekstinde mi?
            if any(kw in before for kw in ['WHERE', 'HAVING', 'BETWEEN', '>', '<', '=', '!=', '<>', '>=', '<=']):
                # Parametre ismi üret
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
        """Tablo adlarını parametreleştir (FROM, JOIN, INTO, UPDATE sonrası)"""
        # FROM table_name
        # Genel isimlendirme kullan - context-free
        
        def from_replacer(match):
            keyword = match.group(1)
            table = match.group(2)
            
            # Alt-sorgu veya fonksiyon değilse parametreleştir
            if '(' in table or table.upper() in ['SELECT', 'VALUES']:
                return match.group(0)
            
            # Generic isim kullan - table, table_1, table_2 gibi
            param_name = self._make_param_name("table", "string")
            self._add_param(param_name, "string", f"Table name", table)
            return f"{keyword} {{{{.{param_name}}}}}"
        
        sql = re.sub(r'\b(FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][\w]*)', from_replacer, sql, flags=re.I)
        return sql
    
    def _parameterize_select_columns(self, sql: str) -> str:
        """SELECT clause'daki sütun adlarını parametreleştir"""
        # SELECT col1, col2, col3 FROM ...
        # Sadece basit column listelerini yakala (fonksiyon/aggregate olmayan)
        
        def select_replacer(match):
            select_kw = match.group(1)
            columns_str = match.group(2)
            from_kw = match.group(3)
            
            # * ise dokunma
            if columns_str.strip() == '*':
                return match.group(0)
            
            # Aggregate fonksiyonlar varsa (COUNT, SUM, AVG, etc.) parametreleştirme
            if re.search(r'\b(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT|DISTINCT)\s*\(', columns_str, re.I):
                return match.group(0)
            
            # Virgülle ayrılmış sütunları parse et
            columns = [c.strip() for c in columns_str.split(',')]
            
            parameterized_cols = []
            for i, col in enumerate(columns, 1):
                # Alias varsa (AS keyword) atla
                if ' AS ' in col.upper() or '.' in col:  # table.column formatı
                    parameterized_cols.append(col)
                    continue
                
                # Basit sütun adı - parametreleştir
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
        """GROUP BY clause'ındaki sütunları parametreleştir"""
        # GROUP BY col1, col2, col3
        
        def group_replacer(match):
            group_kw = match.group(1)
            columns_str = match.group(2)
            
            # Zaten parametreleştirilmiş mi?
            if '{{.' in columns_str:
                return match.group(0)
            
            # Virgülle ayrılmış sütunları parse et
            columns = [c.strip() for c in columns_str.split(',')]
            
            parameterized_cols = []
            for i, col in enumerate(columns, 1):
                # Fonksiyon içeriyorsa atla
                if '(' in col:
                    parameterized_cols.append(col)
                    continue
                
                # table.column formatı varsa - sadece sütun kısmını parametreleştir
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
                
                # Basit sütun adı
                if re.match(r'^[a-zA-Z_][\w]*$', col):
                    param_name = self._make_param_name(f"group_col_{i}" if i > 1 else "group_col", "string")
                    self._add_param(param_name, "string", f"Column to group by", col)
                    parameterized_cols.append(f"{{{{.{param_name}}}}}")
                else:
                    parameterized_cols.append(col)
            
            return f"{group_kw} {', '.join(parameterized_cols)}"
        
        # GROUP BY pattern - ORDER BY'dan önce biter
        sql = re.sub(
            r'\b(GROUP\s+BY)\s+([^;]+?)(?=\s+(?:ORDER|HAVING|LIMIT|;|$))',
            group_replacer,
            sql,
            flags=re.I
        )
        
        return sql
    
    def _parameterize_special_clauses(self, sql: str) -> str:
        """LIMIT, OFFSET, ORDER BY gibi özel clause'ları parametreleştir"""
        
        # LIMIT n
        def limit_replacer(match):
            value = match.group(1)
            if '{{.' in value:  # Zaten parametreleştirilmiş
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
            
            if '{{.' in expr:  # Zaten parametreleştirilmiş
                return match.group(0)
            
            # Fonksiyon mu? (COUNT(*), MAX(col), SUM(x), etc.)
            # Eğer fonksiyon ise, dokunma - fonksiyonları parametreleştirme
            if '(' in expr and ')' in expr:
                # Ama direction parametreleştirilebilir
                if direction and direction.strip():
                    dir_param = "order_dir"
                    self._add_param(dir_param, "string", f"Sort direction (ASC/DESC)", direction.strip())
                    return f"ORDER BY {expr} {{{{.{dir_param}}}}}"
                return match.group(0)
            
            # Basit sütun adı - parametreleştir
            param_name = "order_col"
            self._add_param(param_name, "string", f"Column to order by", expr)
            
            result = f"ORDER BY {{{{.{param_name}}}}}"
            
            # Direction varsa parametreleştir
            if direction and direction.strip():
                dir_param = "order_dir"
                self._add_param(dir_param, "string", f"Sort direction (ASC/DESC)", direction.strip())
                result += f" {{{{.{dir_param}}}}}"
            
            return result
        
        # Match: ORDER BY expression [ASC|DESC]
        # expression can be: column_name, COUNT(*), MAX(col), AVG(field), etc.
        # Regex açıklaması:
        # - [a-zA-Z_][\w\.]* : başlangıç (sütun adı veya fonksiyon adı)
        # - (?:\([^)]*\))? : opsiyonel parantez ve içeriği (fonksiyon için)
        # Ama greedy olmasın ki COUNT(*) DESC gibi şeyleri doğru yakalasın
        sql = re.sub(
            r'\bORDER\s+BY\s+([a-zA-Z_][\w\.]*(?:\([^)]*\))?)\s*(ASC|DESC)?',
            order_replacer,
            sql,
            flags=re.I
        )
        
        return sql
    
    def _parameterize_where_columns(self, sql: str) -> str:
        """WHERE clause'daki sütun isimlerini parametreleştir"""
        # WHERE column = value, WHERE column > value, WHERE column IN (...), etc.
        
        def where_replacer(match):
            where_kw = match.group(1)
            column = match.group(2)
            operator = match.group(3)
            
            # Zaten parametreleştirilmiş mi?
            if '{{.' in column:
                return match.group(0)
            
            # Fonksiyon mu? (COUNT(*), MAX(col), etc.)
            if '(' in column:
                return match.group(0)
            
            # table.column formatı varsa - sadece column kısmını parametreleştir
            if '.' in column:
                parts = column.split('.')
                if len(parts) == 2:
                    table_ref = parts[0]
                    col_name = parts[1]
                    param_name = self._make_param_name("where_col", "string")
                    self._add_param(param_name, "string", f"Column to filter on", col_name)
                    return f"{where_kw} {table_ref}.{{{{.{param_name}}}}} {operator}"
                return match.group(0)
            
            # Basit sütun adı
            if re.match(r'^[a-zA-Z_][\w]*$', column):
                param_name = self._make_param_name("where_col", "string")
                self._add_param(param_name, "string", f"Column to filter on", column)
                return f"{where_kw} {{{{.{param_name}}}}} {operator}"
            
            return match.group(0)
        
        # WHERE column operator pattern
        # Operatörler: =, !=, <>, >, <, >=, <=, IN, NOT IN, LIKE, NOT LIKE, IS, IS NOT
        sql = re.sub(
            r'\b(WHERE)\s+([a-zA-Z_][\w\.]*)\s+(=|!=|<>|>=|<=|>|<|IN|NOT\s+IN|LIKE|NOT\s+LIKE|IS|IS\s+NOT)\b',
            where_replacer,
            sql,
            flags=re.I
        )
        
        return sql
    
    def _parameterize_join_columns(self, sql: str) -> str:
        """JOIN ON clause'daki sütun isimlerini parametreleştir"""
        # JOIN table ON t1.col1 = t2.col2
        
        def join_replacer(match):
            on_kw = match.group(1)
            left_col = match.group(2)
            operator = match.group(3)
            right_col = match.group(4)
            
            # Zaten parametreleştirilmiş mi?
            if '{{.' in left_col or '{{.' in right_col:
                return match.group(0)
            
            # Sol taraf
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
            
            # Sağ taraf
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
