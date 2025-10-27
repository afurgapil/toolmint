import os
import sys
import glob
import time
from typing import List, Dict, Any, Tuple, Set, Optional

ANSI_ENABLED = (
    sys.stdout.isatty()
    and os.getenv("NO_COLOR") is None
    and os.getenv("RETRO_NO_COLOR") is None
)


def _ansi(code: str) -> str:
    """Return ANSI escape code if coloring is enabled."""
    return code if ANSI_ENABLED else ""

from src.parameterizer import SQLParameterizer
from src.quality import calculate_tool_quality_score, generate_semantic_description
from src.labels import generate_labels
from src.validation import validate_tool_advanced, create_tool
from src.io_operations import load_jsonl, save_jsonl, merge_yaml, normalize
from src.utils import sha, generate_smart_tool_name

# ======  8-BIT RETRO DESIGN ======
class RetroColors:
    """8-bit arcade terminal renkleri - ULTRA RETRO MODE"""
    # 8-bit arcade colors
    CYAN = _ansi('\033[96m')      # Electric cyan
    MAGENTA = _ansi('\033[95m')   # Neon magenta
    GREEN = _ansi('\033[92m')     # Matrix green
    YELLOW = _ansi('\033[93m')    # Arcade yellow
    RED = _ansi('\033[91m')       # Laser red
    BLUE = _ansi('\033[94m')      # Cyber blue
    WHITE = _ansi('\033[97m')     # Pure white
    GRAY = _ansi('\033[90m')      # Dark gray
    ORANGE = _ansi('\033[38;5;208m')  # 8-bit orange
    PURPLE = _ansi('\033[38;5;129m')  # 8-bit purple
    PINK = _ansi('\033[38;5;201m')    # 8-bit pink
    LIME = _ansi('\033[38;5;154m')    # 8-bit lime

    # 8-bit styles
    BOLD = _ansi('\033[1m')
    DIM = _ansi('\033[2m')
    UNDERLINE = _ansi('\033[4m')
    BLINK = _ansi('\033[5m')      # Retro blink!
    REVERSE = _ansi('\033[7m')    # Reverse video
    ITALIC = _ansi('\033[3m')     # Italic
    STRIKE = _ansi('\033[9m')     # Strikethrough

    END = _ansi('\033[0m')

    # 8-bit arcade combinations
    TITLE = BOLD + CYAN
    PROMPT = BOLD + WHITE
    SUCCESS = BOLD + GREEN
    ERROR = BOLD + RED
    WARNING = BOLD + YELLOW
    INFO = BOLD + WHITE
    HIGHLIGHT = BOLD + MAGENTA
    ARCADE = BOLD + CYAN
    NEON = BOLD + WHITE
    CYBER = BOLD + CYAN

def print_8bit_ascii_art():
    """MEGA 8-bit ASCII art banner with animation effect"""
    import time
    
    # Animated loading effect
    print(f"{RetroColors.CYBER}🎮 Initializing 8-bit arcade mode...{RetroColors.END}")
    for i in range(3):
        print(f"{RetroColors.NEON}⚡ Loading{'...' * (i + 1)}{RetroColors.END}", end='\r')
        time.sleep(0.3)
    print()
    
    art = f"""
{RetroColors.CYBER}    ███████╗ ███████╗██╗     ███████╗ ██████╗ ███████╗██████╗ 
{RetroColors.CYBER}    ██╔════╝██╔════╝██║     ██╔════╝██╔═══██╗██╔════╝██╔══██╗
{RetroColors.CYBER}    ███████╗███████╗██║     █████╗  ██║   ██║█████╗  ██████╔╝
{RetroColors.CYBER}    ╚════██║╚════██║██║     ██╔══╝  ██║   ██║██╔══╝  ██╔══██╗
{RetroColors.CYBER}    ███████║███████║███████╗███████╗╚██████╔╝███████╗██║  ██║
{RetroColors.CYBER}    ╚══════╝╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
{RetroColors.END}
{RetroColors.NEON}    ╔══════════════════════════════════════════════════════════╗
{RetroColors.NEON}    ║  ██████╗ ██╗   ██╗ ██████╗ ██████╗ ██╗   ██╗███████╗  ║
{RetroColors.NEON}    ║  ██╔══██╗██║   ██║██╔════╝██╔═══██╗██║   ██║██╔════╝  ║
{RetroColors.NEON}    ║  ██████╔╝██║   ██║██║     ██║   ██║██║   ██║█████╗    ║
{RetroColors.NEON}    ║  ██╔══██╗██║   ██║██║     ██║   ██║╚██╗ ██╔╝██╔══╝    ║
{RetroColors.NEON}    ║  ██║  ██║╚██████╔╝╚██████╗╚██████╔╝ ╚████╔╝ ███████╗  ║
{RetroColors.NEON}    ║  ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═════╝   ╚═══╝  ╚══════╝  ║
{RetroColors.NEON}    ╚══════════════════════════════════════════════════════════╝
{RetroColors.END}
{RetroColors.ARCADE}    ╔══════════════════════════════════════════════════════════╗
{RetroColors.ARCADE}    ║  ██╗  ██╗██╗   ██╗███╗   ██╗████████╗██╗███╗   ██╗ ██████╗  ║
{RetroColors.ARCADE}    ║  ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝  ║
{RetroColors.ARCADE}    ║  ███████║██║   ██║██╔██╗ ██║   ██║   ██║██╔██╗ ██║██║  ███╗ ║
{RetroColors.ARCADE}    ║  ██╔══██║██║   ██║██║╚██╗██║   ██║   ██║██║╚██╗██║██║   ██║ ║
{RetroColors.ARCADE}    ║  ██║  ██║╚██████╔╝██║ ╚████║   ██║   ██║██║ ╚████║╚██████╔╝ ║
{RetroColors.ARCADE}    ║  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝  ║
{RetroColors.ARCADE}    ╚══════════════════════════════════════════════════════════╝
{RetroColors.END}
"""
    print(art)

def print_loading_animation():
    """8-bit loading animation"""
    import time
    frames = [
        f"{RetroColors.CYBER}🎮 Loading{RetroColors.END}",
        f"{RetroColors.NEON}⚡ Loading.{RetroColors.END}",
        f"{RetroColors.ARCADE}🚀 Loading..{RetroColors.END}",
        f"{RetroColors.CYBER}🎯 Loading...{RetroColors.END}",
    ]
    
    for _ in range(2):
        for frame in frames:
            print(f"\r{frame}", end='', flush=True)
            time.sleep(0.2)
    print()

def print_progress_bar(current: int, total: int, width: int = 50):
    """8-bit style progress bar"""
    import time
    
    progress = current / total
    filled = int(width * progress)
    bar = f"{RetroColors.CYBER}█{RetroColors.END}" * filled + f"{RetroColors.GRAY}░{RetroColors.END}" * (width - filled)
    percentage = int(progress * 100)
    
    print(f"\r{RetroColors.ARCADE}🎮 Progress: {RetroColors.END}[{bar}] {percentage}%", end='', flush=True)
    if current == total:
        print(f"\n{RetroColors.SUCCESS}✅ Complete!{RetroColors.END}")

def print_retro_header(title: str):
    """MEGA 8-bit retro style header"""
    print(f"\n{RetroColors.CYAN}╔{'═' * 58}╗{RetroColors.END}")
    print(f"{RetroColors.CYAN}║{RetroColors.END} {RetroColors.TITLE}{title:^56}{RetroColors.END} {RetroColors.CYAN}║{RetroColors.END}")
    print(f"{RetroColors.CYAN}╚{'═' * 58}╝{RetroColors.END}")

def print_question(question: str):
    """8-bit style question with mega effects"""
    print(f"\n{RetroColors.PROMPT}🎮 {question}{RetroColors.END}")
    print(f"{RetroColors.DIM}   {'─' * (len(question) + 3)}{RetroColors.END}")

def print_8bit_step(step_num: int, total_steps: int, title: str):
    """MEGA 8-bit step header with enhanced box drawing"""
    # Top border with corners
    print(f"\n{RetroColors.ARCADE}┌{'─' * 58}┐{RetroColors.END}")
    # Title line with side borders
    print(f"{RetroColors.ARCADE}│{RetroColors.END} {RetroColors.TITLE}STEP [{step_num}/{total_steps}] {title:^40}{RetroColors.END} {RetroColors.ARCADE}│{RetroColors.END}")
    # Bottom border with corners
    print(f"{RetroColors.ARCADE}└{'─' * 58}┘{RetroColors.END}")

def print_8bit_box(title: str, content: str = ""):
    """MEGA 8-bit box with rounded corners"""
    print(f"\n{RetroColors.CYBER}╭{'─' * 58}╮{RetroColors.END}")
    print(f"{RetroColors.CYBER}│{RetroColors.END} {RetroColors.TITLE}{title:^56}{RetroColors.END} {RetroColors.CYBER}│{RetroColors.END}")
    if content:
        print(f"{RetroColors.CYBER}├{'─' * 58}┤{RetroColors.END}")
        for line in content.split('\n'):
            print(f"{RetroColors.CYBER}│{RetroColors.END} {line:<56} {RetroColors.CYBER}│{RetroColors.END}")
    print(f"{RetroColors.CYBER}╰{'─' * 58}╯{RetroColors.END}")

def print_8bit_table(headers: list, rows: list):
    """MEGA 8-bit table with box drawing"""
    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Top border
    border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
    print(f"{RetroColors.ARCADE}{border}{RetroColors.END}")
    
    # Header row
    header_row = "│" + "│".join(f" {str(h):^{w}} " for h, w in zip(headers, col_widths)) + "│"
    print(f"{RetroColors.ARCADE}{header_row}{RetroColors.END}")
    
    # Separator
    separator = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
    print(f"{RetroColors.ARCADE}{separator}{RetroColors.END}")
    
    # Data rows
    for row in rows:
        data_row = "│" + "│".join(f" {str(cell):^{w}} " for cell, w in zip(row, col_widths)) + "│"
        print(f"{RetroColors.CYBER}{data_row}{RetroColors.END}")
    
    # Bottom border
    border = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
    print(f"{RetroColors.ARCADE}{border}{RetroColors.END}")

def ask_yes_no(question: str, default: bool = True) -> bool:
    """Evet/Hayır sorusu sor"""
    default_text = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{RetroColors.PROMPT}   {question} [{default_text}]: {RetroColors.END}").strip().lower()
        if not answer:
            return default
        if answer in ['y', 'yes', 'evet', 'e']:
            return True
        if answer in ['n', 'no', 'hayır', 'h']:
            return False
        print(f"{RetroColors.ERROR}   Please enter y/yes or n/no{RetroColors.END}")

def ask_number(question: str, default: int = None, min_val: int = None, max_val: int = None) -> int:
    """Sayı sorusu sor"""
    while True:
        prompt = f"{RetroColors.PROMPT}   {question}"
        if default is not None:
            prompt += f" [{default}]"
        prompt += f": {RetroColors.END}"
        
        answer = input(prompt).strip()
        if not answer and default is not None:
            return default
        
        try:
            num = int(answer)
            if min_val is not None and num < min_val:
                print(f"{RetroColors.ERROR}   Value must be >= {min_val}{RetroColors.END}")
                continue
            if max_val is not None and num > max_val:
                print(f"{RetroColors.ERROR}   Value must be <= {max_val}{RetroColors.END}")
                continue
            return num
        except ValueError:
            print(f"{RetroColors.ERROR}   Please enter a valid number{RetroColors.END}")

def ask_text(question: str, default: str = None) -> str:
    """Metin sorusu sor"""
    prompt = f"{RetroColors.PROMPT}   {question}"
    if default:
        prompt += f" [{default}]"
    prompt += f": {RetroColors.END}"
    
    answer = input(prompt).strip()
    return answer if answer else (default or "")

def interactive_setup() -> Dict[str, Any]:
    """MEGA 8-bit interactive setup"""
    print_8bit_ascii_art()
    print(f"{RetroColors.INFO}🎮 Welcome to the ULTRA RETRO SQL tool generator!{RetroColors.END}")
    print(f"{RetroColors.DIM}⚡ This tool will help you create reusable SQL tools from your dataset.{RetroColors.END}")
    print(f"{RetroColors.CYBER}🚀 Powered by 8-bit arcade technology!{RetroColors.END}")
    
    # Step 1: Input file
    print_8bit_step(1, 9, "INPUT FILE SELECTION")
    
    # JSONL dosyalarını bul
    jsonl_files = glob.glob("*.jsonl")
    if jsonl_files:
        print(f"{RetroColors.INFO}Found JSONL files:{RetroColors.END}")
        for i, file in enumerate(jsonl_files, 1):
            print(f"   {i}. {file}")
        
        while True:
            choice = ask_text("Select file number or enter path", "1")
            try:
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(jsonl_files):
                        input_file = jsonl_files[idx]
                        break
                else:
                    input_file = choice
                    if os.path.exists(input_file):
                        break
                    print(f"{RetroColors.ERROR}File not found: {input_file}{RetroColors.END}")
            except (ValueError, IndexError):
                print(f"{RetroColors.ERROR}Invalid selection{RetroColors.END}")
    else:
        input_file = ask_text("Enter path to JSONL file")
        if not os.path.exists(input_file):
            print(f"{RetroColors.ERROR}File not found: {input_file}{RetroColors.END}")
            sys.exit(1)
    
    # Step 2: Output file
    print_8bit_step(2, 9, "OUTPUT CONFIGURATION")
    output_file = ask_text("Output YAML file", "tools.yaml")
    
    # Step 3: Tool metadata
    print_8bit_step(3, 9, "TOOL METADATA")
    source_name = ask_text("Source name", "interactive")
    kind = ask_text("Tool kind", "mysql-sql")
    
    # Step 4: Processing options
    print_8bit_step(4, 9, "PROCESSING OPTIONS")
    batch_size = ask_number("Batch size (0 = all)", 0, 0, 10000)
    if batch_size == 0:
        batch_size = None
    
    # Step 5: Parameterization options
    print_8bit_step(5, 9, "PARAMETERIZATION OPTIONS")
    parameterize_tables = ask_yes_no("Parameterize table names?", True)
    parameterize_columns = ask_yes_no("Parameterize column names?", True)
    
    # Step 6: Quality settings
    print_8bit_step(6, 9, "QUALITY SETTINGS")
    print(f"{RetroColors.INFO}   Quality score determines how good a SQL tool is (0-100){RetroColors.END}")
    print(f"{RetroColors.INFO}   Higher score = better tool (more parameters, complex SQL, etc.){RetroColors.END}")
    min_quality_score = ask_number("Minimum quality score to accept", 50, 0, 100)
    
    # Step 7: Advanced Quality Settings (NEW)
    print_8bit_step(7, 9, "ADVANCED QUALITY SETTINGS")
    print(f"{RetroColors.INFO}   You can set a maximum quality score to filter out 'too perfect' tools{RetroColors.END}")
    print(f"{RetroColors.INFO}   This is useful if you want tools of a specific complexity level{RetroColors.END}")
    use_max_score = ask_yes_no("Set maximum quality score limit?", False)
    
    if use_max_score:
        max_quality_score = ask_number("Maximum quality score to accept", 100, min_quality_score, 100)
    else:
        max_quality_score = 100
    
    # Optional: Set minimum parameters
    print(f"{RetroColors.INFO}   Minimum parameters: How many parameters a tool must have{RetroColors.END}")
    min_params = ask_number("Minimum parameters required", 1, 0, 10)
    
    # Step 8: Confirmation
    print_8bit_step(8, 9, "CONFIGURATION SUMMARY")
    print(f"{RetroColors.INFO}Configuration:{RetroColors.END}")
    print(f"   📁 Input file:        {input_file}")
    print(f"   📄 Output file:       {output_file}")
    print(f"   🏷️  Source name:       {source_name}")
    print(f"   🔧 Tool kind:         {kind}")
    print(f"   📦 Batch size:        {batch_size or 'All'}")
    print(f"   🗃️  Parameterize tables: {'Yes' if parameterize_tables else 'No'}")
    print(f"   📊 Parameterize columns: {'Yes' if parameterize_columns else 'No'}")
    print(f"   ⭐ Min quality score:  {min_quality_score}")
    print(f"   📈 Max quality score:  {max_quality_score}")
    print(f"   🔢 Min parameters:     {min_params}")
    
    if not ask_yes_no("Proceed with this configuration?", True):
        print(f"{RetroColors.WARNING}Operation cancelled by user{RetroColors.END}")
        sys.exit(0)
    
    # Step 9: Processing
    print_8bit_step(9, 9, "PROCESSING")
    print(f"{RetroColors.INFO}🚀 Starting MEGA 8-bit processing...{RetroColors.END}")
    print(f"{RetroColors.CYBER}⚡ Initializing arcade mode...{RetroColors.END}")
    
    return {
        "input_file": input_file,
        "output_file": output_file,
        "source_name": source_name,
        "kind": kind,
        "batch_size": batch_size,
        "parameterize_tables": parameterize_tables,
        "parameterize_columns": parameterize_columns,
        "min_quality_score": min_quality_score,
        "max_quality_score": max_quality_score,
        "min_params": min_params
    }

def run_processing(config: Dict[str, Any]):
    """İşlemi çalıştır"""
    # Load dataset
    records = load_jsonl(config["input_file"])
    if not records:
        print(f"{RetroColors.ERROR}No records found in input file{RetroColors.END}")
        return
    
    print(f"{RetroColors.INFO}📂 Loaded {len(records)} records from {config['input_file']}{RetroColors.END}")
    
    # Batch processing
    if config["batch_size"]:
        records = records[:config["batch_size"]]
        print(f"{RetroColors.INFO}🔍 Processing first {len(records)} records{RetroColors.END}")
    
    print(f"{RetroColors.INFO}🔄 Processing with quality filter (min: {config['min_quality_score']}, max: {config['max_quality_score']})...{RetroColors.END}")
    print(f"{RetroColors.CYBER}🎯 Activating 8-bit arcade mode...{RetroColors.END}")
    print(f"{RetroColors.NEON}⚡ Powering up retro engines...{RetroColors.END}")
    print()
    
    # Statistics
    stats = {
        "success": 0,
        "empty_sql": 0,
        "quality_issues": 0,
        "low_score": 0,
        "high_score": 0,
        "errors": 0,
        "total_quality_score": 0.0,
        "label_counts": {}
    }
    
    tools = []
    
    for idx, rec in enumerate(records):
        # Show progress bar every 10 records
        if idx % 10 == 0:
            print_progress_bar(idx, len(records))
        
        try:
            n = normalize(rec)
            
            # Empty SQL check
            if not n["sql"]:
                stats["empty_sql"] += 1
                continue
            
            # Parameterize SQL
            parameterizer = SQLParameterizer(
                parameterize_tables=config["parameterize_tables"],
                parameterize_columns=config["parameterize_columns"]
            )
            parameterized_sql, params = parameterizer.parameterize(n["sql"])
            
            # Minimum parameters check
            if len(params) < config["min_params"]:
                stats["low_score"] += 1
                continue
            
            # Quality validation
            is_valid, err_msg, quality_score = validate_tool_advanced(
                parameterized_sql, params, n["question"], min_score=config["min_quality_score"]
            )
            
            if not is_valid:
                if "Quality score too low" in err_msg:
                    stats["low_score"] += 1
                else:
                    stats["quality_issues"] += 1
                continue
            
            # Check max quality score
            if quality_score > config["max_quality_score"]:
                stats["high_score"] += 1
                continue
            
            # Create tool with semantic description and labels
            base_desc = generate_semantic_description(parameterized_sql, n["question"], params)
            labels_str = generate_labels(n["sql"])  # Use original SQL for labels
            desc = f"{base_desc} [Labels: {labels_str}]" if labels_str else base_desc
            smart_name = generate_smart_tool_name(parameterized_sql, n["question"])
            key = f"{smart_name}_{sha(n['sql'] + n['question'], n=4)}"
            
            tool = {
                key: {
                    "kind": config["kind"],
                    "source": config["source_name"],
                    "statement": parameterized_sql,
                    "description": desc,
                    "templateParameters": params
                }
            }
            
            tools.append(tool)
            stats["success"] += 1
            stats["total_quality_score"] += quality_score
            
            # Track labels
            if labels_str:
                for label in labels_str.split(', '):
                    stats["label_counts"][label] = stats["label_counts"].get(label, 0) + 1
            
            # MEGA 8-bit progress styling
            print(f"{RetroColors.SUCCESS}🎮 [{stats['success']}] {key}{RetroColors.END}")
            print(f"   {RetroColors.CYBER}📝 {desc[:80]}{'...' if len(desc) > 80 else ''}{RetroColors.END}")
            print(f"   {RetroColors.ARCADE}🔧 {len(params)} parameters{RetroColors.END}")
            print(f"   {RetroColors.NEON}⭐ Quality: {quality_score:.1f}/100{RetroColors.END}")
            print(f"   {RetroColors.DIM}   {'─' * 60}{RetroColors.END}")
            print()
            
        except Exception as e:
            stats["errors"] += 1
            print(f"{RetroColors.ERROR}❌ Error processing record {idx}: {e}{RetroColors.END}")
    
    # MEGA 8-bit statistics with table
    print_8bit_box("🎮 PROCESSING STATISTICS", "")
    
    # Create statistics table
    stats_data = [
        ["Metric", "Count", "Status"],
        ["SUCCESS", f"{stats['success']:3d} tools", "✅"],
        ["EMPTY SQL", f"{stats['empty_sql']:3d} records", "⚠️"],
        ["QUALITY ISSUES", f"{stats['quality_issues']:3d} records", "⚠️"],
        ["LOW SCORE", f"{stats['low_score']:3d} records", "⚠️"],
        ["HIGH SCORE", f"{stats['high_score']:3d} records", "⚠️"],
        ["ERRORS", f"{stats['errors']:3d} records", "❌"]
    ]
    
    print_8bit_table(["Metric", "Count", "Status"], stats_data[1:])
    
    total_processed = sum(v for k, v in stats.items() if k not in ['total_quality_score', 'label_counts'])
    
    # Summary box
    summary_content = f"Total Processed: {total_processed} records"
    if stats['success'] > 0:
        avg_quality = stats['total_quality_score'] / stats['success']
        acceptance_rate = (stats['success'] / total_processed) * 100
        summary_content += f"\nAcceptance Rate: {acceptance_rate:.1f}%"
        summary_content += f"\nAverage Quality: {avg_quality:.1f}/100"
    
    print_8bit_box("📊 SUMMARY", summary_content)
    
    # MEGA 8-bit label statistics
    if stats.get('label_counts'):
        sorted_labels = sorted(stats['label_counts'].items(), key=lambda x: x[1], reverse=True)
        
        # Create label table
        label_data = []
        for label, count in sorted_labels:
            percentage = (count / stats['success']) * 100
            label_data.append([label, f"{count:3d}", f"{percentage:5.1f}%"])
        
        print_8bit_table(["Label", "Count", "Percentage"], label_data)
    
    # Save output
    if tools:
        merge_yaml(config["output_file"], tools)
        print(f"\n{RetroColors.SUCCESS}🎮 Wrote {len(tools)} tools to {config['output_file']}{RetroColors.END}")
        print(f"{RetroColors.CYBER}⚡ Tools saved with 8-bit precision!{RetroColors.END}")
    
    # Save remaining records
    if config["batch_size"] and len(records) > config["batch_size"]:
        remaining = records[config["batch_size"]:]
        remaining_file = config["input_file"].replace('.jsonl', '_remaining.jsonl')
        save_jsonl(remaining_file, remaining)
        print(f"{RetroColors.INFO}🧹 Consumed {config['batch_size']} records from input{RetroColors.END}")
        print(f"{RetroColors.INFO}📦 Remaining in input: {len(remaining)}{RetroColors.END}")

def main():
    """Ana fonksiyon"""
    try:
        config = interactive_setup()
        run_processing(config)
        print(f"\n{RetroColors.SUCCESS}🎉 MEGA 8-bit processing completed successfully!{RetroColors.END}")
        print(f"{RetroColors.CYBER}🚀 Arcade mode deactivated - Mission accomplished!{RetroColors.END}")
        print(f"{RetroColors.NEON}⚡ Thanks for using the ULTRA RETRO SQL tool generator!{RetroColors.END}")
    except KeyboardInterrupt:
        print(f"\n{RetroColors.WARNING}⚠️  Operation cancelled by user{RetroColors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RetroColors.ERROR}❌ Unexpected error: {e}{RetroColors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
