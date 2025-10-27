<div align="center">
  <h3>AI-powered SQL Tool Generator with intelligent parameterization, quality scoring, and modern interfaces</h3>

<a href="https://www.python.org/" target="_blank"><img alt="Python" src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" /></a>
<a href="https://www.riverbankcomputing.com/software/pyqt/" target="_blank"><img alt="PyQt5" src="https://img.shields.io/badge/PyQt5-5.15-41CD52?style=for-the-badge&logo=qt&logoColor=white" /></a>
<a href="https://pyyaml.org/" target="_blank"><img alt="PyYAML" src="https://img.shields.io/badge/PyYAML-6.0-FFD700?style=for-the-badge&logo=yaml&logoColor=222222" /></a>
<a href="https://pandas.pydata.org/" target="_blank"><img alt="Pandas" src="https://img.shields.io/badge/Pandas-2.3-150458?style=for-the-badge&logo=pandas&logoColor=white" /></a>
<a href="https://numpy.org/" target="_blank"><img alt="NumPy" src="https://img.shields.io/badge/NumPy-2.3-013243?style=for-the-badge&logo=numpy&logoColor=white" /></a>
<a href="https://pillow.readthedocs.io/" target="_blank"><img alt="Pillow" src="https://img.shields.io/badge/Pillow-12.0-013243?style=for-the-badge&logo=python&logoColor=white" /></a>

<a href="https://github.com/" target="_blank"><img alt="Version" src="https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge" /></a>
<a href="https://opensource.org/licenses/MIT" target="_blank"><img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" /></a>

</div>

---

<h1 align="center">ToolMint - SQL Tool Generator</h1>

<p align="center">
An intelligent system for generating parameterized SQL tools from text-to-SQL datasets.<br/>
Transform natural language queries into reusable, parameterized SQL tools with built-in quality assessment and modern GUI interfaces.
</p>

---

## Overview

### The Vision

In the era of large language models and AI-powered applications, **retrieval-augmented generation (RAG)** has become the cornerstone of building intelligent, context-aware systems. ToolMint bridges the gap between public SQL datasets and production-ready AI toolkits by transforming raw SQL queries into **semantically searchable, parameterized, and quality-assessed tools**.

### Why ToolMint?

Traditional approaches to NL-to-SQL systems either rely on fine-tuning large models (expensive and dataset-specific) or use generic SQL parsers that lack domain knowledge. ToolMint takes a revolutionary approach:

**Harness the Power of Open Datasets**: Extract valuable patterns from publicly available SQL datasets (Spider, BIRD, and more) without expensive retraining.

**Semantic Retrieval Ready**: Generate tools that seamlessly integrate with embedding-based retrieval systems like FAISS, Pinecone, or Chroma. Every tool is parameterized, labeled, and quality-scored for optimal semantic matching.

**Production-Ready from Day One**: The generated tools follow consistent schemas with rich metadata, making them immediately usable in RAG pipelines, code generation systems, and AI agent frameworks.

### How It Works

Imagine having **thousands of high-quality SQL patterns** at your fingertips, each:

- **Parameterized** for maximum reusability across different databases
- **Quality-scored** to ensure reliability and correctness
- **Semantically labeled** for intelligent retrieval based on user intent
- **Validated** against best practices for SQL query construction

ToolMint transforms raw SQL queries into a **tool library** that AI systems can search, understand, and utilize. When a user asks _"Find all students from California"_, your RAG system can:

1. **Embed** the natural language query
2. **Retrieve** semantically similar tools from the FAISS index
3. **Execute** with context-aware parameter binding
4. **Return** accurate results

### Use Cases

**AI Agent Development**: Build conversational SQL interfaces that understand user intent and execute the right queries.

**Database API Generation**: Transform natural language requirements into secure, parameterized endpoints.

**Intelligent Code Assistants**: Help developers write database queries by suggesting proven patterns from quality datasets.

**Educational Platforms**: Teach SQL concepts through real-world examples extracted from industry-standard benchmarks.

### The Competitive Edge

Unlike frameworks that require massive computational resources or proprietary datasets, ToolMint democratizes access to production-grade SQL tools. Our parameterization engine ensures that tools generated from one database schema can be adapted to another with minimal effort, making it an ideal solution for:

- **Startups** building AI-powered applications on a budget
- **Enterprises** looking to leverage open-source datasets for internal tools
- **Researchers** studying SQL generation and retrieval systems
- **Developers** integrating conversational interfaces into their products

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Examples](#examples)
- [License](#license)

---

## Features

### Core Capabilities

- **Intelligent SQL Parameterization**: Automatically convert SQL queries into parameterized, reusable tools
- **Quality Scoring**: Built-in quality assessment system for generated tools
- **Smart Labeling**: Automatic categorization of SQL operations (SELECT, WHERE, JOIN, etc.)
- **Dataset Support**: Process various text-to-SQL datasets (Spider, BIRD, custom)
- **Modern GUI**: User-friendly PyQt5 interface with dataset and tool viewers

### User Interfaces

#### 1. **GUI Application** (`app_pyqt_gui.py`)

- Modern PyQt5 interface
- Dataset Viewer: Browse and inspect input datasets
- Tools Viewer: View and filter generated SQL tools
- Configurable processing options
- Real-time progress tracking

#### 2. **Interactive CLI** (`app_interactive.py`)

- Retro 8-bit terminal interface
- Color-coded output for easy reading
- Detailed processing statistics
- Step-by-step guidance

### Advanced Features

- **Multi-dataset Processing**: Merge tools from multiple datasets
- **Customizable Parameters**: Control parameterization depth and style
- **Quality Filters**: Filter tools by quality score thresholds
- **Export Formats**: YAML output for integration with AI frameworks

---

## Installation

### Prerequisites

- Python 3.13+ (compatible with 3.9+)
- pip package manager

### Setup Steps

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/toolmint.git
cd toolmint
```

2. **Create and activate virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

### Dependencies

- **PyQt5** 5.15.11 - GUI framework
- **PyYAML** 6.0.3 - YAML parsing
- **pandas** 2.3.3 - Data manipulation
- **numpy** 2.3.4 - Numerical operations
- **pillow** 12.0.0 - Image processing

---

## Quick Start

### Launch GUI Application

```bash
python app_pyqt_gui.py
```

### Launch Interactive CLI

```bash
python app_interactive.py
```

### Process a Dataset

```bash
# Using CLI
python app_interactive.py

# The tool will guide you through:
# 1. Select input dataset
# 2. Configure parameters
# 3. Process and generate tools
# 4. View results
```

---

## Usage

### GUI Application Workflow

#### Step 1: Select Input Dataset

- Use the "Browse" button to select a JSONL dataset file
- Or choose from the "Quick Select" dropdown (loads from `datasets/` folder)
- Click "View" to inspect dataset contents before processing

#### Step 2: Configure Processing Options

- **Output File**: Specify where to save generated tools (default: `tools.yaml`)
- **Processing Options**:
  - Enable/disable quality scoring
  - Enable/disable parameterization
  - Enable/disable auto-labeling
- **Quality Filter**: Set minimum quality score threshold (0-100)

#### Step 3: Generate Tools

- Click "Start Processing"
- Monitor progress in real-time
- Results will appear in the right panel

#### Step 4: View Generated Tools

- Click "View Generated Tools" to open the Tools Viewer
- Filter and search through generated tools
- Double-click any tool to view detailed information

### CLI Application Workflow

```bash
python app_interactive.py

# Interactive prompts:
> Select dataset file: datasets/spider.jsonl
> Use quality scoring? [Y/n]: y
> Use parameterization? [Y/n]: y
> Use labeling? [Y/n]: y
> Minimum quality score [0-100]: 50

# Processing...
# Tools generated successfully!
```

---

## Project Structure

```
toolmint/
├── src/                      # Core modules
│   ├── __init__.py
│   ├── parameterizer.py         # SQL parameterization engine
│   ├── quality.py                # Quality scoring system
│   ├── labels.py                 # Automatic labeling
│   ├── validation.py             # Tool validation
│   ├── io_operations.py          # File I/O utilities
│   └── utils.py                  # Helper functions
│
├── datasets/                  # Input datasets
│   ├── spider.jsonl              # Spider dataset
│   └── bird-mini.jsonl          # BIRD dataset
│
├── quality_analysis/         # Quality metrics
│   ├── quality_analysis.png
│   └── breakdown_analysis.png
│
├── assets/                    # GUI assets
│   ├── fonts/
│   ├── sounds/
│   └── sprites/
│
├── app_pyqt_gui.py              # GUI application
├── app_interactive.py           # CLI application
├── tools.yaml                    # Generated tools output
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

---

## Architecture

### Core Components

#### 1. **SQL Parameterizer** (`src/parameterizer.py`)

Intelligently transforms SQL queries into parameterized versions:

- Identifies literals (strings, numbers)
- Extracts tables and columns
- Creates reusable parameters with descriptions
- Supports various SQL constructs (SELECT, WHERE, JOIN, GROUP BY, ORDER BY, LIMIT, OFFSET)

#### 2. **Quality Assessor** (`src/quality.py`)

Evaluates tool quality based on:

- Parameter count and diversity
- SQL complexity
- Query structure
- Reusability potential

#### 3. **Label Generator** (`src/labels.py`)

Automatically categorizes tools:

- Operation types (SELECT, INSERT, UPDATE, DELETE)
- Query features (JOIN, GROUP BY, ORDER BY, etc.)
- Complexity indicators

#### 4. **Data Validator** (`src/validation.py`)

Ensures generated tools are:

- Syntactically correct
- Properly parameterized
- Non-destructive
- Well-structured

### Processing Pipeline

```
Input Dataset (JSONL)
    ↓
Normalize Records
    ↓
Parameterize SQL Queries
    ↓
Calculate Quality Scores
    ↓
Generate Labels
    ↓
Validate Tools
    ↓
Export to YAML
    ↓
Output (tools.yaml)
```

---

## Configuration

### Processing Options

Available in both GUI and CLI:

| Option                 | Description                 | Default |
| ---------------------- | --------------------------- | ------- |
| `use_quality_scoring`  | Enable quality assessment   | `True`  |
| `use_parameterization` | Enable SQL parameterization | `True`  |
| `use_labeling`         | Enable automatic labeling   | `True`  |
| `parameterize_tables`  | Parameterize table names    | `True`  |
| `parameterize_columns` | Parameterize column names   | `True`  |
| `min_quality_score`    | Minimum quality threshold   | `50`    |
| `min_params`           | Minimum parameters per tool | `2`     |

### Output Format

Generated tools are saved in YAML format:

```yaml
tools:
  sql_tool_1:
    description: "What are the names of all students?"
    sql: "SELECT {{.select_col}} FROM {{.table}} WHERE {{.where_col}} = {{.value}}"
    parameters:
      - name: table
        type: string
        description: "Table name (e.g., students)"
      - name: select_col
        type: string
        description: "Column to select (e.g., name)"
      - name: where_col
        type: string
        description: "Column to filter on"
      - name: value
        type: string
        description: "Filter value"
    quality_score: 85.5
    labels: "select, filtered"
    db_id: "student_db"
    source: "spider"
```

---

## Examples

### Example 1: Basic Usage

```bash
# Start GUI
python app_pyqt_gui.py

# Select: datasets/spider.jsonl
# Configure: Enable all options
# Quality Score: 60
# Click: Start Processing

# Result: tools.yaml with parameterized SQL tools
```

### Example 2: CLI with Custom Settings

```bash
python app_interactive.py

# Configuration:
# - Dataset: datasets/bird-mini.jsonl
# - Quality Scoring: Yes
# - Parameterization: Yes
# - Labeling: Yes
# - Min Quality: 70

# Output: High-quality tools only
```

### Example 3: Generating Specific Types

Focus on specific SQL patterns:

- **SELECT queries**: For data retrieval
- **JOIN operations**: For complex relationships
- **Aggregate queries**: For analytics
- **Filter queries**: For targeted searches

---

## Use Cases

### 1. **AI Agent Development**

Generate reusable SQL tools for LLM-based agents:

- Parameterized queries reduce hallucination
- Quality scoring ensures reliable tools
- Easy integration with frameworks

### 2. **Database API Generation**

Create parameterized endpoints from natural language:

- Transform business queries into APIs
- Maintain security through parameterization
- Enable flexible query execution

### 3. **Code Generation Systems**

Use as a component in larger code generation pipelines:

- Extract reusable patterns
- Generate database abstraction layers
- Create ORM-like functionality

### 4. **Educational Tools**

Teach SQL concepts:

- Demonstrate parameterization
- Show query optimization
- Explore database design

---

## Supported Datasets

### Tested Datasets

- **Spider Dataset**: Text-to-SQL benchmark
- **BIRD Dataset**: Business intelligence queries
- **Custom JSONL**: Your own datasets

### Dataset Format

```jsonl
{"question": "What are the names of all students?", "sql": "SELECT name FROM students", "db_id": "university_db"}
{"question": "Find students older than 25", "sql": "SELECT * FROM students WHERE age > 25", "db_id": "university_db"}
```

---

## Contributing

Contributions are welcome! Areas for improvement:

- Additional dataset support
- Enhanced quality metrics
- More SQL dialect support
- Performance optimizations
- UI/UX improvements

---

## License

This project is licensed under the MIT License.

---

## Acknowledgments

- Built with Python and PyQt5
- Inspired by text-to-SQL research
- Designed for AI agent development

---

## Contact & Support

For questions, issues, or contributions:

- Open an issue on GitHub
- Check the documentation
- Review example datasets

---

**Made for the AI community**
