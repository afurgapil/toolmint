#!/usr/bin/env python3
"""
Modern PyQt5 GUI for ToolMint
With proper window controls and modern interface
"""

import sys
import os
import json
import threading
from typing import Dict, Any, List
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QProgressBar, QCheckBox,
                             QSlider, QComboBox, QFileDialog, QMessageBox,
                             QTabWidget, QGroupBox, QSplitter, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QMenu,
                             QScrollArea, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.io_operations import load_jsonl, merge_yaml
from src.parameterizer import SQLParameterizer
from src.quality import calculate_tool_quality_score
from src.labels import generate_labels
from src.validation import validate_tool_advanced
from src.export import (export_tools_to_json, export_tools_to_csv, 
                        export_results_to_txt, export_results_to_json)

class ToolsViewerDialog(QDialog):
    """Dialog for viewing generated tools"""
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(f"Tools Viewer - {os.path.basename(file_path)}")
        self.setGeometry(100, 100, 1400, 800)
        self.setup_ui()
        self.load_tools()
        
    def setup_ui(self):
        """Setup the UI for tools viewer"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"🛠️ Tools: {os.path.basename(self.file_path)}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2E86AB; padding: 10px;")
        layout.addWidget(title_label)
        
        # Search/filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Search by description, SQL, or labels...")
        self.filter_edit.textChanged.connect(self.filter_table)
        filter_layout.addWidget(self.filter_edit)
        layout.addLayout(filter_layout)
        
        # Table widget
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self.view_tool_details)
        layout.addWidget(self.table)
        
        # Info label and buttons
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Loading tools...")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        details_btn = QPushButton("📋 View Details")
        details_btn.clicked.connect(self.view_selected_tool_details)
        info_layout.addWidget(details_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close_dialog)
        info_layout.addWidget(close_btn)
        
        layout.addLayout(info_layout)
        
    def load_tools(self):
        """Load and display tools from YAML file"""
        try:
            import yaml
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            tools = {}
            if isinstance(data, dict):
                tools = data.get('tools', {})
            
            if not tools:
                self.info_label.setText("No tools found in file")
                return
            
            # Setup table
            columns = ['Tool Name', 'Description', 'SQL', 'Parameters', 'Quality Score', 'Labels']
            self.table.setRowCount(len(tools))
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            
            # Populate table
            for row_idx, (tool_name, tool_data) in enumerate(tools.items()):
                # Tool Name
                self.table.setItem(row_idx, 0, QTableWidgetItem(tool_name))
                
                # Description
                desc = str(tool_data.get('description', ''))
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                self.table.setItem(row_idx, 1, QTableWidgetItem(desc))
                
                # SQL
                sql = str(tool_data.get('sql', ''))
                if len(sql) > 100:
                    sql = sql[:100] + "..."
                self.table.setItem(row_idx, 2, QTableWidgetItem(sql))
                
                # Parameters
                params = tool_data.get('parameters', [])
                param_str = f"{len(params)} param(s)" if params else "No params"
                self.table.setItem(row_idx, 3, QTableWidgetItem(param_str))
                
                # Quality Score
                score = tool_data.get('quality_score', 0)
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(score)))
                
                # Labels
                labels = str(tool_data.get('labels', ''))
                if len(labels) > 50:
                    labels = labels[:50] + "..."
                self.table.setItem(row_idx, 5, QTableWidgetItem(labels))
                
                # Store full data for details view
                for col_idx in range(6):
                    item = self.table.item(row_idx, col_idx)
                    if item:
                        item.setData(Qt.ItemDataRole.UserRole, {tool_name: tool_data})
            
            # Resize columns
            self.table.resizeColumnsToContents()
            self.table.setColumnWidth(1, 300)  # Description
            self.table.setColumnWidth(2, 350)  # SQL
            self.table.setColumnWidth(3, 120)  # Parameters
            self.table.setColumnWidth(4, 100)  # Quality Score
            self.table.setColumnWidth(5, 150)  # Labels
            
            # Update info
            self.info_label.setText(f"Loaded {len(tools)} tools")
            
        except Exception as e:
            self.info_label.setText(f"Error loading tools: {str(e)}")
            
    def filter_table(self, text):
        """Filter table by search text"""
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            
    def view_selected_tool_details(self):
        """View details of selected tool"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a tool to view details")
            return
        
        # Get the first selected row
        row = selected_items[0].row()
        item = self.table.item(row, 0)
        if item:
            tool_data = item.data(Qt.ItemDataRole.UserRole)
            self.view_tool_details(item)
            
    def view_tool_details(self, item):
        """View detailed information about a tool"""
        tool_data = item.data(Qt.ItemDataRole.UserRole)
        if not tool_data:
            return
            
        tool_name = list(tool_data.keys())[0]
        tool_info = tool_data[tool_name]
        
        # Create detail dialog
        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle(f"Tool Details: {tool_name}")
        detail_dialog.setGeometry(150, 150, 900, 700)
        
        layout = QVBoxLayout(detail_dialog)
        
        # Title
        title = QLabel(f"🛠️ {tool_name}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Scrollable text area for details
        detail_text = QTextEdit()
        detail_text.setReadOnly(True)
        
        details = f"""Description:
{self._safe_get(tool_info, 'description', 'N/A')}

SQL Query:
{self._safe_get(tool_info, 'sql', 'N/A')}

Quality Score: {self._safe_get(tool_info, 'quality_score', 'N/A')}
Labels: {self._safe_get(tool_info, 'labels', 'N/A')}
Database ID: {self._safe_get(tool_info, 'db_id', 'N/A')}
Source: {self._safe_get(tool_info, 'source', 'N/A')}

Parameters:
{self._format_parameters(tool_info.get('parameters', []))}
"""
        
        detail_text.setPlainText(details)
        detail_text.setFont(QFont("Courier", 10))
        layout.addWidget(detail_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(lambda: detail_dialog.accept())
        layout.addWidget(close_btn)
        
        detail_dialog.exec_()
        
    def _safe_get(self, data, key, default):
        """Safely get value from dictionary"""
        return str(data.get(key, default))
        
    def _format_parameters(self, params):
        """Format parameters list for display"""
        if not params:
            return "No parameters"
        
        result = []
        for p in params:
            param_str = f"  - {p.get('name', 'N/A')} ({p.get('type', 'N/A')})"
            desc = p.get('description', '')
            if desc:
                param_str += f": {desc}"
            result.append(param_str)
        
        return "\n".join(result)
        
    def close_dialog(self):
        """Close the dialog"""
        self.accept()

class DatasetViewerDialog(QDialog):
    """Dialog for viewing dataset contents"""
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(f"Dataset Viewer - {os.path.basename(file_path)}")
        self.setGeometry(100, 100, 1200, 700)
        self.setup_ui()
        self.load_dataset()
        
    def setup_ui(self):
        """Setup the UI for dataset viewer"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"📊 Viewing: {os.path.basename(self.file_path)}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2E86AB; padding: 10px;")
        layout.addWidget(title_label)
        
        # Table widget
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Info label
        self.info_label = QLabel("Loading dataset...")
        layout.addWidget(self.info_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close_dialog)
        layout.addWidget(close_btn)
        
    def close_dialog(self):
        """Close the dialog"""
        self.accept()
        
    def load_dataset(self):
        """Load and display dataset"""
        try:
            from src.io_operations import load_jsonl
            data = load_jsonl(self.file_path)
            
            if not data:
                self.info_label.setText("Dataset is empty")
                return
            
            # Get first item keys to determine columns
            first_item = data[0]
            columns = list(first_item.keys())
            
            # Setup table
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            
            # Populate table
            for row_idx, item in enumerate(data):
                for col_idx, col_name in enumerate(columns):
                    value = str(item.get(col_name, ""))
                    # Truncate long values
                    if len(value) > 100:
                        value = value[:100] + "..."
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))
            
            # Resize columns to content
            self.table.resizeColumnsToContents()
            
            # Adjust column widths for readability
            for col in range(len(columns)):
                width = self.table.columnWidth(col)
                self.table.setColumnWidth(col, min(width, 300))
            
            # Update info
            self.info_label.setText(f"Loaded {len(data)} records with {len(columns)} columns")
            
        except Exception as e:
            self.info_label.setText(f"Error loading dataset: {str(e)}")

class ProcessingWorker(QThread):
    """Worker thread for processing data"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    stats = pyqtSignal(dict)  # Processing statistics
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def run(self):
        try:
            import time
            self.status.emit("Loading data...")
            self.progress.emit(10)
            
            # Load data
            data = load_jsonl(self.config["input_file"])
            self.status.emit(f"Loaded {len(data)} items")
            self.progress.emit(30)
            
            # Process data
            self.status.emit("Processing data...")
            self.progress.emit(50)
            
            # Real processing using existing modules
            from src.parameterizer import SQLParameterizer
            from src.quality import calculate_tool_quality_score
            from src.labels import generate_labels
            from src.validation import validate_tool_advanced
            
            # Initialize parameterizer
            param = SQLParameterizer(
                parameterize_tables=self.config.get("parameterize_tables", True),
                parameterize_columns=self.config.get("parameterize_columns", True),
                min_params=self.config.get("min_params", 1)
            )
            
            # Process each item
            tools = []
            processed_count = 0
            filtered_count = 0
            start_time = time.time()
            
            for i, item in enumerate(data):
                try:
                    # Normalize the item
                    from src.io_operations import normalize
                    normalized = normalize(item)
                    
                    if not normalized.get("sql") or not normalized.get("question"):
                        continue
                    
                    # Generate parameterized SQL
                    if self.config.get("use_parameterization", True):
                        param_sql, params = param.parameterize(normalized["sql"])
                    else:
                        param_sql = normalized["sql"]
                        params = []
                    
                    # Convert to target SQL dialect
                    dialect = self.config.get("sql_dialect", "mysql")
                    if dialect != "mysql":
                        from src.sql_dialect_converter import SQLDialectConverter
                        converter = SQLDialectConverter(dialect)
                        param_sql, params = converter.convert(param_sql, params)
                    
                    # Calculate quality score (simplified for now)
                    try:
                        if self.config.get("use_quality_scoring", True):
                            quality_score, _ = calculate_tool_quality_score(
                                param_sql, 
                                params, 
                                normalized["question"]
                            )
                        else:
                            quality_score = 100
                    except Exception as e:
                        print(f"Quality score error: {e}")
                        quality_score = 50  # Default score
                    
                    # Generate labels
                    if self.config.get("use_labeling", True):
                        labels = generate_labels(param_sql)
                    else:
                        labels = ""
                    
                    # Create tool
                    tool_name = f"sql_tool_{processed_count + 1}"
                    tool = {
                        tool_name: {
                            "description": normalized["question"],
                            "sql": param_sql,
                            "parameters": params,
                            "quality_score": quality_score,
                            "labels": labels,
                            "db_id": normalized.get("db_id", ""),
                            "source": normalized.get("source", "unknown")
                        }
                    }
                    
                    tools.append(tool)
                    processed_count += 1
                    
                    # Update progress
                    progress = 50 + int((i / len(data)) * 40)
                    self.progress.emit(progress)
                    
                    # Emit stats every 100 items or every 10 items after first 100
                    if i % 10 == 0 or (processed_count > 100 and i % 100 == 0):
                        elapsed = time.time() - start_time
                        remaining_items = len(data) - (i + 1)
                        
                        # Calculate ETA (only after processing > 10 items)
                        if processed_count > 10:
                            avg_time_per_item = elapsed / processed_count
                            eta_seconds = avg_time_per_item * remaining_items
                            eta_minutes = int(eta_seconds // 60)
                            eta_seconds = int(eta_seconds % 60)
                            eta_str = f"{eta_minutes}m {eta_seconds}s"
                        else:
                            eta_str = "Calculating..."
                        
                        stats = {
                            'processed': processed_count,
                            'total': len(data),
                            'filtered': filtered_count,
                            'eta': eta_str,
                            'elapsed': f"{int(elapsed)}s"
                        }
                        self.stats.emit(stats)
                    
                except Exception as e:
                    print(f"Error processing item {i}: {e}")
                    continue
            
            # Save to YAML file with dialect-specific naming
            self.status.emit("Saving results...")
            output_file = self.config.get("output_file", "tools.yaml")
            dialect = self.config.get("sql_dialect", "mysql")
            
            # Adjust output file name based on dialect
            if dialect != "mysql":
                base, ext = os.path.splitext(output_file)
                output_file = f"{base}_{dialect}{ext}"
            
            merge_yaml(output_file, tools)
            
            self.progress.emit(100)
            self.status.emit(f"Processing completed! Saved to {output_file}")
            
            # Return results
            results = {
                "input_file": self.config["input_file"],
                "items_processed": len(data),
                "tools_created": processed_count,
                "output_file": output_file,
                "processing_time": "Real processing completed"
            }
            
            self.finished.emit(results)
            
        except Exception as e:
            import traceback
            error_msg = f"Processing Error:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(error_msg)  # Mirror the message in the console
            self.error.emit(error_msg)

class ModernSQLToolGenerator(QMainWindow):
    """Modern PyQt5 GUI application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToolMint")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Configure modern styling
        self.setup_style()
        
        # Variables
        self.config = {
            "output_file": "tools.yaml",
            "tool_name": "sql-tools", 
            "description": "SQL Tools for Database Operations",
            "author": "ToolMint",
            "version": "1.0.0",
            "license": "MIT",
            "db_type": "mysql-sql",
            "batch_size": 0,
            "use_quality_scoring": True,
            "use_parameterization": True,
            "use_labeling": True,
            "parameterize_tables": True,
            "parameterize_columns": True,
            "param_style": "question_mark",
            "max_params": 5,
            "min_quality_score": 50,
            "max_quality_score": 100,
            "min_params": 1,
            "use_max_score": False,
            "input_file": "",
            "sql_dialect": "mysql"
        }
        
        self.processing = False
        self.results = {}
        self.processing_stats = {}  # Store processing statistics
        
        # Create UI
        self.create_ui()
        
    def setup_style(self):
        """Setup modern styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2E86AB;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
                background-color: white;
                color: #333;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #4CAF50;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
            QLabel {
                color: #333;
            }
            QCheckBox {
                color: #333;
                spacing: 10px;
                font-size: 14px;
                font-weight: 600;
                padding: 4px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #888;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #4CAF50;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #45a049;
                border-color: #45a049;
            }
            QToolTip {
                background-color: #e0e0e0;
                color: black;
                border: 1px solid #999;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                font-weight: 500;
            }
            QMessageBox {
                background-color: white;
                color: #333;
                font-size: 13px;
            }
            QMessageBox QLabel {
                color: #333;
                background-color: white;
                padding: 10px;
            }
            QMessageBox QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #45a049;
            }
            QMessageBox QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
    def create_ui(self):
        """Create the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
     
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (Configuration) with scroll area
        config_widget = self.create_config_panel()
        scroll_area = QScrollArea()
        scroll_area.setWidget(config_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set light gray background to match main window
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
        """)
        
        splitter.addWidget(scroll_area)
        
        # Right panel (Results)
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([600, 800])
        
        # Status bar
        status_bar = self.statusBar()
        if status_bar is not None:
            self.status_label = QLabel()  # Hidden label, just for internal tracking
            self.status_label.setVisible(False)
            status_bar.addWidget(self.status_label)
            
            # Progress bar removed - we use ASCII progress in results panel instead
            self.progress_bar = None
        
    def create_config_panel(self):
        """Create configuration panel"""
        panel = QWidget()
        panel.setMinimumWidth(500)  # Set minimum width to prevent squeezing
        panel.setStyleSheet("background-color: #f5f5f5;")  # Match main background
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)  # Add some margins
        
        # File Selection Group
        file_group = QGroupBox("📁 Input File")
        file_layout = QGridLayout(file_group)
        file_layout.setVerticalSpacing(8)
        file_layout.setHorizontalSpacing(8)
        
        # File path
        file_label = QLabel("Dataset File:")
        file_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        file_layout.addWidget(file_label, 0, 0)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a dataset file...")
        file_layout.addWidget(self.file_path_edit, 0, 1)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        file_layout.addWidget(browse_btn, 0, 2)
        
        # Hugging Face Import button
        hf_btn = QPushButton("🤗 HF")
        hf_btn.clicked.connect(self.import_from_hf)
        hf_btn.setToolTip("Import dataset from Hugging Face Hub")
        hf_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #FF5252;
                color: black;
            }
        """)
        file_layout.addWidget(hf_btn, 0, 3)
        
        # View dataset button
        view_dataset_btn = QPushButton("👁️ View")
        view_dataset_btn.clicked.connect(self.view_dataset)
        view_dataset_btn.setToolTip("View dataset contents in a table")
        view_dataset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                color: black;
            }
        """)
        file_layout.addWidget(view_dataset_btn, 0, 4)
        
        layout.addWidget(file_group)
        
        # Dataset Statistics Panel
        self.dataset_info_group = QGroupBox("📊 Dataset Information")
        dataset_info_layout = QVBoxLayout(self.dataset_info_group)
        self.dataset_info_label = QLabel("No dataset selected")
        self.dataset_info_label.setWordWrap(True)
        self.dataset_info_label.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
        dataset_info_layout.addWidget(self.dataset_info_label)
        self.dataset_info_group.setVisible(False)
        layout.addWidget(self.dataset_info_group)
        
        # Connect file path changes to analyze dataset
        self.file_path_edit.textChanged.connect(self.analyze_dataset)
        
        # Basic Configuration Group
        basic_group = QGroupBox("⚙️ Basic Configuration")
        basic_layout = QGridLayout(basic_group)
        
        # Output file
        basic_layout.addWidget(QLabel("Output File:"), 0, 0)
        self.output_file_edit = QLineEdit(self.config["output_file"])
        basic_layout.addWidget(self.output_file_edit, 0, 1)
        
        # Tool name
        basic_layout.addWidget(QLabel("Tool Name:"), 0, 2)
        self.tool_name_edit = QLineEdit(self.config["tool_name"])
        basic_layout.addWidget(self.tool_name_edit, 0, 3)
        
        # Description
        basic_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_edit = QLineEdit(self.config["description"])
        basic_layout.addWidget(self.description_edit, 1, 1, 1, 3)
        
        # Author, Version, License
        basic_layout.addWidget(QLabel("Author:"), 2, 0)
        self.author_edit = QLineEdit(self.config["author"])
        basic_layout.addWidget(self.author_edit, 2, 1)
        
        basic_layout.addWidget(QLabel("Version:"), 2, 2)
        self.version_edit = QLineEdit(self.config["version"])
        basic_layout.addWidget(self.version_edit, 2, 3)
        
        basic_layout.addWidget(QLabel("License:"), 3, 0)
        self.license_edit = QLineEdit(self.config["license"])
        basic_layout.addWidget(self.license_edit, 3, 1)
        
        layout.addWidget(basic_group)
        
        # Database Dialect Group
        dialect_group = QGroupBox("🗄️ Database Dialect")
        dialect_layout = QHBoxLayout(dialect_group)
        
        dialect_layout.addWidget(QLabel("Target Database:"))
        self.dialect_combo = QComboBox()
        self.dialect_combo.addItems(["MySQL", "PostgreSQL", "SQLite", "SQL Server"])
        self.dialect_combo.setCurrentText("MySQL")
        dialect_layout.addWidget(self.dialect_combo)
        
        # Info label
        dialect_info = QLabel("SQL syntax will be converted to selected dialect")
        dialect_info.setStyleSheet("color: #666; font-size: 11px; margin-left: 10px;")
        dialect_layout.addWidget(dialect_info)
        
        layout.addWidget(dialect_group)
        
        # Processing Options Group
        options_group = QGroupBox("🔄 Processing Options")
        options_layout = QVBoxLayout(options_group)
        
        # Checkboxes with help labels
        checkbox_layout = QVBoxLayout()
        
        # Quality scoring
        quality_container = QVBoxLayout()
        self.use_quality_check = QCheckBox("Use Quality Scoring")
        self.use_quality_check.setChecked(self.config["use_quality_scoring"])
        self.use_quality_check.stateChanged.connect(self.on_checkbox_changed)
        quality_container.addWidget(self.use_quality_check)
        quality_help = QLabel("Evaluates tools based on parameter diversity and SQL complexity")
        quality_help.setStyleSheet("color: #666; font-size: 11px; margin-left: 30px;")
        quality_container.addWidget(quality_help)
        checkbox_layout.addLayout(quality_container)
        
        # Parameterization
        param_container = QVBoxLayout()
        self.use_param_check = QCheckBox("Use Parameterization")
        self.use_param_check.setChecked(self.config["use_parameterization"])
        self.use_param_check.stateChanged.connect(self.on_checkbox_changed)
        param_container.addWidget(self.use_param_check)
        param_help = QLabel("Converts SQL to parameterized templates for reusability")
        param_help.setStyleSheet("color: #666; font-size: 11px; margin-left: 30px;")
        param_container.addWidget(param_help)
        checkbox_layout.addLayout(param_container)
        
        # Labeling
        label_container = QVBoxLayout()
        self.use_label_check = QCheckBox("Use Labeling")
        self.use_label_check.setChecked(self.config["use_labeling"])
        self.use_label_check.stateChanged.connect(self.on_checkbox_changed)
        label_container.addWidget(self.use_label_check)
        label_help = QLabel("Adds semantic labels for FAISS retrieval (SELECT, JOIN, etc.)")
        label_help.setStyleSheet("color: #666; font-size: 11px; margin-left: 30px;")
        label_container.addWidget(label_help)
        checkbox_layout.addLayout(label_container)
        
        options_layout.addLayout(checkbox_layout)
        
        # Quality score slider
        quality_container = QVBoxLayout()
        quality_container.setSpacing(5)
        
        quality_slider_layout = QHBoxLayout()
        quality_slider_layout.setSpacing(8)
        
        min_quality_label = QLabel("Min Quality Score:")
        min_quality_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        quality_slider_layout.addWidget(min_quality_label)
        
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(self.config["min_quality_score"])
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        quality_slider_layout.addWidget(self.quality_slider, 1)  # Give it stretch factor
        
        self.quality_label = QLabel(str(self.config["min_quality_score"]))
        self.quality_label.setStyleSheet("font-weight: bold; color: #2E86AB; min-width: 40px;")
        self.quality_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        quality_slider_layout.addWidget(self.quality_label)
        
        quality_container.addLayout(quality_slider_layout)
        
        quality_help_label = QLabel("Filter tools below this score. Lower = more tools, Higher = premium quality only")
        quality_help_label.setStyleSheet("color: #666; font-size: 11px; margin-left: 5px;")
        quality_container.addWidget(quality_help_label)
        
        options_layout.addLayout(quality_container)
        
        layout.addWidget(options_group)
        
        # Process Button
        self.process_btn = QPushButton("🚀 Start Processing")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                font-size: 16px;
                padding: 12px 24px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(self.process_btn)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
        
    def create_results_panel(self):
        """Create results panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Results Group
        results_group = QGroupBox("📊 Results")
        results_layout = QVBoxLayout(results_group)
        
        # Results text area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        
        # Welcome banner
        welcome_banner = """
                   Welcome to ToolMint                        
              SQL Tool Generation Platform                    


          Processing results will appear here...
"""
        self.results_text.setPlainText(welcome_banner)
        self.results_text.setPlaceholderText("Processing results will appear here...")
        results_layout.addWidget(self.results_text)
        
        # Results buttons
        button_layout = QHBoxLayout()
        
        self.view_tools_btn = QPushButton("🛠️ View Generated Tools")
        self.view_tools_btn.clicked.connect(self.view_generated_tools)
        self.view_tools_btn.setToolTip("View the generated tools YAML file")
        self.view_tools_btn.setStyleSheet("QPushButton { background-color: #FF9800; }")
        self.view_tools_btn.setVisible(False)  # Initially hidden
        button_layout.addWidget(self.view_tools_btn)
        
        copy_btn = QPushButton("📋 Copy Results")
        copy_btn.clicked.connect(self.copy_results)
        button_layout.addWidget(copy_btn)
        
        # Export dropdown button
        self.export_btn = QPushButton("💾 Export")
        export_menu = QMenu(self)
        
        # Results export options
        export_menu.addSeparator()
        export_menu.addAction("📄 Export Summary as TXT", lambda: self.export_results('txt'))
        export_menu.addAction("📄 Export Summary as JSON", lambda: self.export_results('json'))
        
        # Tools export options (only shown when tools exist)
        export_menu.addSeparator()
        export_menu.addAction("🛠️ Export Tools as YAML", lambda: self.export_tools('yaml'))
        export_menu.addAction("🛠️ Export Tools as JSON", lambda: self.export_tools('json'))
        export_menu.addAction("🛠️ Export Tools as CSV", lambda: self.export_tools('csv'))
        
        self.export_btn.setMenu(export_menu)
        button_layout.addWidget(self.export_btn)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(clear_btn)
        
        results_layout.addLayout(button_layout)
        
        layout.addWidget(results_group)
        
        return panel
        
    def browse_file(self):
        """Browse for file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Dataset File", "", "JSONL files (*.jsonl);;All files (*.*)"
        )
        if filename:
            self.file_path_edit.setText(filename)
    
    def import_from_hf(self):
        """Import dataset from Hugging Face Hub"""
        try:
            # Simple input dialog for HF dataset name
            from src.hf_importer import import_from_hf_dataset, normalize_hf_dataset, save_hf_dataset_to_jsonl
            
            text, ok = QInputDialog.getText(
                self, 
                'Import from Hugging Face',
                'Enter Hugging Face dataset name:\n(e.g., spider, wikisql, text2sql-apps)\nor org/repo (e.g., gretelai/synthetic_text_to_sql)'
            )
            
            if not ok or not text:
                return
            
            # Clean the dataset name
            dataset_name = text.strip()
            
            # Remove common URL patterns if user pasted a URL
            import re
            if 'huggingface.co' in dataset_name:
                # Extract dataset name from URL - match org/repo format
                # Pattern: huggingface.co/datasets/org/repo or huggingface.co/datasets/org-repo
                match = re.search(r'huggingface\.co/datasets/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+|[a-zA-Z0-9_-]+)', dataset_name)
                if match:
                    dataset_name = match.group(1)
                else:
                    QMessageBox.warning(self, "Invalid URL", "Could not extract dataset name from URL")
                    return
            
            # Remove leading/trailing slashes, dots, and spaces
            dataset_name = dataset_name.strip('/').strip('.').strip()
            
            # Remove any query parameters or fragments (e.g., ?library=datasets, #anything)
            if '?' in dataset_name:
                dataset_name = dataset_name.split('?')[0]
            if '#' in dataset_name:
                dataset_name = dataset_name.split('#')[0]
            
            # Remove any trailing invalid characters
            while dataset_name.endswith(('.', '-', '/')):
                dataset_name = dataset_name[:-1]
            
            # Import from HF
            self.status_label.setText(f"Downloading '{dataset_name}' from Hugging Face...")
            QApplication.processEvents()
            
            try:
                records = import_from_hf_dataset(dataset_name)
            except RuntimeError as e:
                if "Dataset scripts are no longer supported" in str(e):
                    QMessageBox.warning(
                        self,
                        "Unsupported Dataset Format",
                        f"This dataset ('{dataset_name}') uses Python loading scripts which are no longer supported by Hugging Face.\n\n"
                        "Please try one of these recommended datasets:\n"
                        "• spider\n"
                        "• gretelai/synthetic_text_to_sql\n\n"
                        "For more details, visit:\n"
                        "https://huggingface.co/docs/datasets/v2.0.0/en/dataset_script#deprecated"
                    )
                elif "doesn't exist" in str(e) or "not found" in str(e).lower():
                    QMessageBox.warning(
                        self,
                        "Dataset Not Found",
                        f"The dataset '{dataset_name}' could not be found on Hugging Face Hub.\n\n"
                        "Please check:\n"
                        "• Dataset name is correct\n"
                        "• Dataset is public or you have access\n"
                        "• You have an internet connection"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Import Error",
                        f"Failed to load dataset '{dataset_name}':\n\n{str(e)}"
                    )
                self.status_label.setText("Ready")
                return
            except ImportError as e:
                QMessageBox.warning(
                    self,
                    "Missing Dependency",
                    f"Hugging Face datasets library error:\n\n{str(e)}\n\n"
                    "Please ensure 'datasets' is installed:\npip install datasets"
                )
                self.status_label.setText("Ready")
                return
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Unexpected Error",
                    f"An unexpected error occurred while loading '{dataset_name}':\n\n{str(e)}\n\n"
                    "Please check your internet connection and try again."
                )
                self.status_label.setText("Ready")
                return
            
            if not records:
                QMessageBox.warning(
                    self,
                    "Empty Dataset",
                    f"The dataset '{dataset_name}' is empty or has no records."
                )
                self.status_label.setText("Ready")
                return
            
            # Normalize records - pass dataset name for profile matching
            self.status_label.setText("Normalizing dataset...")
            QApplication.processEvents()
            
            normalized = normalize_hf_dataset(records, dataset_name=dataset_name)
            
            if not normalized:
                # Show detailed error message
                if records:
                    first_record_keys = list(records[0].keys())
                    error_msg = (
                        f"No valid records found in dataset '{dataset_name}'.\n\n"
                        f"Detected fields: {', '.join(first_record_keys)}\n\n"
                        f"This dataset may need a custom profile.\n"
                        f"Please ensure records contain both a question and SQL field."
                    )
                else:
                    error_msg = f"No records found in dataset '{dataset_name}'."
                
                QMessageBox.warning(self, "Import Failed", error_msg)
                return
            
            # Save to datasets directory
            safe_name = dataset_name.replace('/', '_').replace('.', '_')
            
            # Create datasets directory if it doesn't exist
            datasets_dir = "datasets"
            if not os.path.exists(datasets_dir):
                os.makedirs(datasets_dir)
            
            # Save dataset to datasets directory
            dataset_file = os.path.join(datasets_dir, f"{safe_name}.jsonl")
            save_hf_dataset_to_jsonl(normalized, dataset_file)
            
            # Set file path
            self.file_path_edit.setText(dataset_file)
            
            QMessageBox.information(
                self, 
                "Import Successful", 
                f"Imported {len(normalized)} records from Hugging Face dataset '{dataset_name}'"
            )
            
            self.status_label.setText("Ready")
            
        except Exception as e:
            # Catch any unexpected errors during import
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(
                self,
                "Import Error",
                f"An unexpected error occurred:\n\n{str(e)}\n\nDetails:\n{error_details}"
            )
            self.status_label.setText("Ready")
            
    def view_dataset(self):
        """View the currently selected dataset"""
        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "No File", "Please select a dataset file first")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file does not exist:\n{file_path}")
            return
        
        # Open viewer dialog
        dialog = DatasetViewerDialog(file_path, self)
        dialog.exec_()
    
    def analyze_dataset(self):
        """Analyze selected dataset and show statistics"""
        file_path = self.file_path_edit.text()
        
        # Hide panel if no file
        if not file_path:
            self.dataset_info_group.setVisible(False)
            return
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.dataset_info_group.setVisible(False)
            return
        
        try:
            import re
            # Load dataset
            data = load_jsonl(file_path)
            
            if not data:
                self.dataset_info_label.setText("Dataset is empty")
                self.dataset_info_group.setVisible(True)
                return
            
            # Calculate statistics
            total_records = len(data)
            
            # SQL feature analysis
            sql_keywords = {
                'SELECT': 0, 'WHERE': 0, 'JOIN': 0, 'GROUP BY': 0,
                'ORDER BY': 0, 'HAVING': 0, 'UNION': 0, 'WITH': 0
            }
            total_sql_length = 0
            valid_sql_count = 0
            
            for item in data:
                sql = item.get('sql', '')
                if sql:
                    valid_sql_count += 1
                    total_sql_length += len(sql)
                    sql_upper = sql.upper()
                    for keyword in sql_keywords.keys():
                        if keyword in sql_upper:
                            sql_keywords[keyword] += 1
            
            avg_sql_length = int(total_sql_length / valid_sql_count) if valid_sql_count > 0 else 0
            
            # Dataset quality indicator
            quality_features = sum(1 for count in sql_keywords.values() if count > total_records * 0.1)
            quality_score = min(100, (quality_features * 15 + (valid_sql_count / total_records) * 100))
            
            # Format statistics
            stats_text = f"""Total Records: {total_records:,}
Valid SQL Queries: {valid_sql_count:,}
Average SQL Length: {avg_sql_length} chars
Dataset Quality: {'High' if quality_score > 70 else 'Medium' if quality_score > 40 else 'Low'} ({quality_score:.0f}/100)

SQL Features:
- WHERE clauses: {sql_keywords['WHERE']} ({sql_keywords['WHERE']*100//total_records}%)
- JOIN operations: {sql_keywords['JOIN']} ({sql_keywords['JOIN']*100//total_records}%)
- GROUP BY: {sql_keywords['GROUP BY']} ({sql_keywords['GROUP BY']*100//total_records}%)
- ORDER BY: {sql_keywords['ORDER BY']} ({sql_keywords['ORDER BY']*100//total_records}%)
"""
            
            self.dataset_info_label.setText(stats_text)
            self.dataset_info_group.setVisible(True)
            
        except Exception as e:
            self.dataset_info_label.setText(f"Error analyzing dataset: {str(e)}")
            self.dataset_info_group.setVisible(True)
            
    def update_quality_label(self, value):
        """Update quality score label"""
        self.quality_label.setText(str(value))
        
    def on_checkbox_changed(self):
        """Handle checkbox state changes"""
        # This method is called when any checkbox changes
        # You can add specific logic here if needed
        pass
        
    def start_processing(self):
        """Start processing"""
        if self.processing:
            return
            
        # Validate input
        if not self.file_path_edit.text():
            QMessageBox.warning(self, "Error", "Please select an input file")
            return
            
        if not os.path.exists(self.file_path_edit.text()):
            QMessageBox.warning(self, "Error", "Input file does not exist")
            return
            
        # Update config
        self.update_config()
        
        # Start processing
        self.processing = True
        self.process_btn.setText("⏳ Processing...")
        self.process_btn.setEnabled(False)
        
        # Clear results panel and show "Starting..." message
        if self.results_text is not None:
            self.results_text.setPlainText("Starting processing...\nPlease wait...")
        
        # Create and start worker thread
        self.worker = ProcessingWorker(self.config)
        self.processing_stats = {}  # Reset stats
        
        if self.status_label is not None:
            self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.processing_error)
        self.worker.stats.connect(self.handle_stats)
        self.worker.start()
        
    def update_config(self):
        """Update config from UI"""
        # Get dialect and normalize it
        dialect = self.dialect_combo.currentText().lower().replace(" ", "_")
        if dialect == "sql_server":
            dialect = "sql_server"
        elif dialect == "postgresql":
            dialect = "postgres"
        
        self.config.update({
            "output_file": self.output_file_edit.text(),
            "tool_name": self.tool_name_edit.text(),
            "description": self.description_edit.text(),
            "author": self.author_edit.text(),
            "version": self.version_edit.text(),
            "license": self.license_edit.text(),
            "input_file": self.file_path_edit.text(),
            "use_quality_scoring": self.use_quality_check.isChecked(),
            "use_parameterization": self.use_param_check.isChecked(),
            "use_labeling": self.use_label_check.isChecked(),
            "min_quality_score": self.quality_slider.value(),
            "sql_dialect": dialect
        })
        
    def processing_finished(self, results):
        """Handle processing finished"""
        self.processing = False
        self.process_btn.setText("🚀 Start Processing")
        self.process_btn.setEnabled(True)
        
        self.results = results
        self.update_results()
        
        # Show View Generated Tools button
        self.view_tools_btn.setVisible(True)
        
    
    def handle_stats(self, stats):
        """Handle processing statistics"""
        self.processing_stats = stats
        self.update_processing_preview()
    
    def update_processing_preview(self):
        """Update results panel with processing preview"""
        if self.results_text is None:
            return
        
        # Build preview text with simple banner
        preview_text = """
                   Welcome to ToolMint                        
              SQL Tool Generation Platform                    


Processing in Progress...

"""
        
        # Add stats if available
        if self.processing_stats:
            stats = self.processing_stats
            processed = stats.get('processed', 0)
            total = stats.get('total', 0)
            filtered = stats.get('filtered', 0)
            elapsed = stats.get('elapsed', '0')
            eta = stats.get('eta', 'Calculating...')
            
            # Calculate progress percentage
            if total > 0:
                progress_pct = int((processed / total) * 100)
            else:
                progress_pct = 0
            
            # Create ASCII progress bar
            bar_width = 50
            filled = int((progress_pct / 100) * bar_width)
            progress_bar = "[" + "█" * filled + "░" * (bar_width - filled) + "]"
            
            preview_text += f"Progress: {processed}/{total} items processed ({progress_pct}%)\n"
            preview_text += f"{progress_bar}\n\n"
            preview_text += f"Filtered: {filtered} items\n"
            preview_text += f"Elapsed: {elapsed}s | ETA: {eta}\n"
        
        self.results_text.setPlainText(preview_text)
    
    def processing_error(self, error_msg):
        """Handle processing error"""
        self.processing = False
        self.process_btn.setText("🚀 Start Processing")
        self.process_btn.setEnabled(True)
        
        # Create a more detailed error dialog
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Processing Error")
        error_dialog.setText("An error occurred during processing:")
        error_dialog.setDetailedText(error_msg)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()
        
        # Also update status
        if self.status_label is not None:
            self.status_label.setText("Processing failed - see error dialog")
        
    def update_results(self):
        """Update results display"""
        if self.results_text is None:
            return
        output_file = self.results.get('output_file', self.config['output_file'])
        output_path = os.path.abspath(output_file)
        
        results_text = f"""Processing Results:
========================

Input File: {self.results['input_file']}
Items Processed: {self.results['items_processed']}
Tools Created: {self.results['tools_created']}
Processing Time: {self.results['processing_time']}

Configuration:
- Output File: {self.config['output_file']}
- Tool Name: {self.config['tool_name']}
- Description: {self.config['description']}
- Author: {self.config['author']}
- Version: {self.config['version']}
- License: {self.config['license']}

Processing Options:
- Quality Scoring: {self.config['use_quality_scoring']}
- Parameterization: {self.config['use_parameterization']}
- Labeling: {self.config['use_labeling']}
- Min Quality Score: {self.config['min_quality_score']}

📁 OUTPUT FILE LOCATION:
{output_path}

The tools have been generated and saved to the YAML file above.
You can open this file to view the generated SQL tools.
"""
        
        self.results_text.setPlainText(results_text)
        
    def copy_results(self):
        """Copy results to clipboard"""
        clipboard = QApplication.clipboard()
        if clipboard is not None and self.results_text is not None:
            clipboard.setText(self.results_text.toPlainText())
        if self.status_label is not None:
            self.status_label.setText("Results copied to clipboard")
        
    def export_results(self, format_type):
        """Export processing results summary"""
        if not self.results:
            QMessageBox.warning(self, "No Results", "No processing results to export")
            return
        
        # Combine config and results
        export_data = {**self.config, **self.results}
        
        if format_type == 'txt':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Results", "", "Text files (*.txt);;All files (*.*)"
            )
            if filename:
                export_results_to_txt(export_data, filename)
                if self.status_label is not None:
                    self.status_label.setText(f"Results exported to {filename}")
        elif format_type == 'json':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Results", "", "JSON files (*.json);;All files (*.*)"
            )
            if filename:
                export_results_to_json(export_data, filename)
                if self.status_label is not None:
                    self.status_label.setText(f"Results exported to {filename}")
    
    def export_tools(self, format_type):
        """Export generated tools"""
        output_file = self.config.get('output_file', 'tools.yaml')
        
        if not os.path.isabs(output_file):
            output_file = os.path.join(os.getcwd(), output_file)
        
        if not os.path.exists(output_file):
            QMessageBox.warning(
                self, 
                "No Tools", 
                "No generated tools found. Please generate tools first."
            )
            return
        
        if format_type == 'yaml':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Tools", "", "YAML files (*.yaml *.yml);;All files (*.*)"
            )
            if filename:
                from src.export import export_tools_to_yaml
                export_tools_to_yaml(output_file, filename)
                if self.status_label is not None:
                    self.status_label.setText(f"Tools exported to {filename}")
        elif format_type == 'json':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Tools", "", "JSON files (*.json);;All files (*.*)"
            )
            if filename:
                export_tools_to_json(output_file, filename)
                if self.status_label is not None:
                    self.status_label.setText(f"Tools exported to {filename}")
        elif format_type == 'csv':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Tools", "", "CSV files (*.csv);;All files (*.*)"
            )
            if filename:
                export_tools_to_csv(output_file, filename)
                if self.status_label is not None:
                    self.status_label.setText(f"Tools exported to {filename}")
            
    def clear_results(self):
        """Clear results"""
        if self.results_text is not None:
            self.results_text.clear()
        self.results = {}
        self.processing_stats = {}
        if self.status_label is not None:
            self.status_label.setText("Results cleared")
        
        # Hide View Generated Tools button
        self.view_tools_btn.setVisible(False)
            
    def view_generated_tools(self):
        """View the generated tools YAML file"""
        # Get output file path
        output_file = self.config.get('output_file', 'tools.yaml')
        
        # If not absolute path, make it relative to current directory
        if not os.path.isabs(output_file):
            output_file = os.path.join(os.getcwd(), output_file)
        
        # Check if file exists
        if not os.path.exists(output_file):
            QMessageBox.warning(
                self, 
                "File Not Found", 
                f"No generated tools file found.\n\nExpected location:\n{output_file}\n\nPlease generate tools first."
            )
            return
        
        # Open tools viewer dialog
        dialog = ToolsViewerDialog(output_file, self)
        dialog.exec_()

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ToolMint")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ToolMint")
    
    # Enable tooltips
    app.setStyle('Fusion')
    
    # Create and show main window
    window = ModernSQLToolGenerator()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
