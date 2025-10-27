#!/usr/bin/env python3
"""
Modern PyQt5 GUI for SQL Tool Generator
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
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.io_operations import load_jsonl, merge_yaml
from src.parameterizer import SQLParameterizer
from src.quality import calculate_tool_quality_score
from src.labels import generate_labels
from src.validation import validate_tool_advanced

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
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
    def run(self):
        try:
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
                    
                except Exception as e:
                    print(f"Error processing item {i}: {e}")
                    continue
            
            # Save to YAML file
            self.status.emit("Saving results...")
            output_file = self.config.get("output_file", "tools.yaml")
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
            print(error_msg)  # Console'a da yazdır
            self.error.emit(error_msg)

class ModernSQLToolGenerator(QMainWindow):
    """Modern PyQt5 GUI application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 SQL Tool Generator - Modern GUI")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Configure modern styling
        self.setup_style()
        
        # Variables
        self.config = {
            "output_file": "tools.yaml",
            "tool_name": "sql-tools", 
            "description": "SQL Tools for Database Operations",
            "author": "SQL Tool Generator",
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
            "input_file": ""
        }
        
        self.processing = False
        self.results = {}
        
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
                spacing: 8px;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QCheckBox::indicator:hover {
                border-color: #4CAF50;
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
        
        # Title
        title_label = QLabel("🎮 SQL Tool Generator")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2E86AB; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (Configuration)
        left_panel = self.create_config_panel()
        splitter.addWidget(left_panel)
        
        # Right panel (Results)
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([600, 800])
        
        # Status bar
        self.status_label = QLabel("Ready")
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.addWidget(self.status_label)
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        if status_bar is not None:
            status_bar.addPermanentWidget(self.progress_bar)
        
    def create_config_panel(self):
        """Create configuration panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # File Selection Group
        file_group = QGroupBox("📁 Input File")
        file_layout = QGridLayout(file_group)
        
        # File path
        file_layout.addWidget(QLabel("Dataset File:"), 0, 0)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a dataset file...")
        file_layout.addWidget(self.file_path_edit, 0, 1)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn, 0, 2)
        
        # View dataset button
        view_dataset_btn = QPushButton("👁️ View")
        view_dataset_btn.clicked.connect(self.view_dataset)
        view_dataset_btn.setToolTip("View dataset contents in a table")
        file_layout.addWidget(view_dataset_btn, 0, 3)
        
        # Quick select
        file_layout.addWidget(QLabel("Quick Select:"), 1, 0)
        self.dataset_combo = QComboBox()
        self.dataset_combo.currentTextChanged.connect(self.on_dataset_selected)
        file_layout.addWidget(self.dataset_combo, 1, 1, 1, 2)
        
        # Open dataset button
        open_dataset_btn = QPushButton("📂 Open Dataset")
        open_dataset_btn.clicked.connect(self.open_dataset_from_list)
        open_dataset_btn.setToolTip("Open and view selected dataset")
        file_layout.addWidget(open_dataset_btn, 1, 3)
        
        # Load datasets
        self.load_datasets()
        
        layout.addWidget(file_group)
        
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
        
        # Processing Options Group
        options_group = QGroupBox("🔄 Processing Options")
        options_layout = QVBoxLayout(options_group)
        
        # Checkboxes
        checkbox_layout = QVBoxLayout()
        
        self.use_quality_check = QCheckBox("Use Quality Scoring")
        self.use_quality_check.setChecked(self.config["use_quality_scoring"])
        self.use_quality_check.stateChanged.connect(self.on_checkbox_changed)
        checkbox_layout.addWidget(self.use_quality_check)
        
        self.use_param_check = QCheckBox("Use Parameterization")
        self.use_param_check.setChecked(self.config["use_parameterization"])
        self.use_param_check.stateChanged.connect(self.on_checkbox_changed)
        checkbox_layout.addWidget(self.use_param_check)
        
        self.use_label_check = QCheckBox("Use Labeling")
        self.use_label_check.setChecked(self.config["use_labeling"])
        self.use_label_check.stateChanged.connect(self.on_checkbox_changed)
        checkbox_layout.addWidget(self.use_label_check)
        
        options_layout.addLayout(checkbox_layout)
        
        # Quality score slider
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Min Quality Score:"))
        
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(self.config["min_quality_score"])
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        quality_layout.addWidget(self.quality_slider)
        
        self.quality_label = QLabel(str(self.config["min_quality_score"]))
        quality_layout.addWidget(self.quality_label)
        
        options_layout.addLayout(quality_layout)
        
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
        self.results_text.setPlaceholderText("Processing results will appear here...")
        results_layout.addWidget(self.results_text)
        
        # Results buttons
        button_layout = QHBoxLayout()
        
        view_tools_btn = QPushButton("🛠️ View Generated Tools")
        view_tools_btn.clicked.connect(self.view_generated_tools)
        view_tools_btn.setToolTip("View the generated tools YAML file")
        view_tools_btn.setStyleSheet("QPushButton { background-color: #FF9800; }")
        button_layout.addWidget(view_tools_btn)
        
        copy_btn = QPushButton("📋 Copy Results")
        copy_btn.clicked.connect(self.copy_results)
        button_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("💾 Save Results")
        save_btn.clicked.connect(self.save_results)
        button_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(clear_btn)
        
        results_layout.addLayout(button_layout)
        
        layout.addWidget(results_group)
        
        return panel
        
    def load_datasets(self):
        """Load available datasets"""
        datasets_dir = os.path.join(os.getcwd(), "datasets")
        if os.path.exists(datasets_dir):
            files = [f for f in os.listdir(datasets_dir) if f.endswith('.jsonl')]
            self.dataset_combo.addItems(files)
            if files:
                self.file_path_edit.setText(os.path.join(datasets_dir, files[0]))
        else:
            self.dataset_combo.addItem("No datasets found")
            
    def on_dataset_selected(self, text):
        """Handle dataset selection"""
        if text and text != "No datasets found":
            datasets_dir = os.path.join(os.getcwd(), "datasets")
            self.file_path_edit.setText(os.path.join(datasets_dir, text))
            
    def browse_file(self):
        """Browse for file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Dataset File", "", "JSONL files (*.jsonl);;All files (*.*)"
        )
        if filename:
            self.file_path_edit.setText(filename)
            
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
        
    def open_dataset_from_list(self):
        """Open and view dataset from the quick select combo box"""
        selected_text = self.dataset_combo.currentText()
        if not selected_text or selected_text == "No datasets found":
            QMessageBox.warning(self, "No Dataset", "Please select a dataset from the list")
            return
        
        datasets_dir = os.path.join(os.getcwd(), "datasets")
        file_path = os.path.join(datasets_dir, selected_text)
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file does not exist:\n{file_path}")
            return
        
        # Update the file path edit
        self.file_path_edit.setText(file_path)
        
        # Open viewer dialog
        dialog = DatasetViewerDialog(file_path, self)
        dialog.exec_()
            
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
        if self.progress_bar is not None:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
        
        # Create and start worker thread
        self.worker = ProcessingWorker(self.config)
        if self.progress_bar is not None:
            self.worker.progress.connect(self.progress_bar.setValue)
        if self.status_label is not None:
            self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.processing_error)
        self.worker.start()
        
    def update_config(self):
        """Update config from UI"""
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
            "min_quality_score": self.quality_slider.value()
        })
        
    def processing_finished(self, results):
        """Handle processing finished"""
        self.processing = False
        self.process_btn.setText("🚀 Start Processing")
        self.process_btn.setEnabled(True)
        if self.progress_bar is not None:
            self.progress_bar.setVisible(False)
        
        self.results = results
        self.update_results()
        
    def processing_error(self, error_msg):
        """Handle processing error"""
        self.processing = False
        self.process_btn.setText("🚀 Start Processing")
        self.process_btn.setEnabled(True)
        if self.progress_bar is not None:
            self.progress_bar.setVisible(False)
        
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
        
    def save_results(self):
        """Save results to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", "Text files (*.txt);;All files (*.*)"
        )
        if filename and self.results_text is not None:
            with open(filename, 'w') as f:
                f.write(self.results_text.toPlainText())
            if self.status_label is not None:
                self.status_label.setText(f"Results saved to {filename}")
            
    def clear_results(self):
        """Clear results"""
        if self.results_text is not None:
            self.results_text.clear()
        self.results = {}
        if self.status_label is not None:
            self.status_label.setText("Results cleared")
            
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
    app.setApplicationName("SQL Tool Generator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SQL Tool Generator")
    
    # Create and show main window
    window = ModernSQLToolGenerator()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
