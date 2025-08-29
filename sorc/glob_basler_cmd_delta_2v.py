# 2025-08-25
# Global settings for Basler acA4024-8gc Advanced Color Difference Dashboard
# Basler camera advanced color difference measurement dashboard global settings

import os

# =============================================================================
# Program Information
# =============================================================================

VERSION = "1.0.0"
BUILD_DATE = "2025-08-25"
PROGRAM_TITLE = "Basler acA4024-8gc ColorMasterBatch Analysis Solution"

# =============================================================================
# Camera Settings
# =============================================================================

# Default camera configuration
DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 1200
DEFAULT_FRAME_RATE = 15.0
SAFE_RESOLUTION_RATIO = 0.33
ALIGNMENT_SIZE = 16

# Pixel format priority
PIXEL_FORMATS_PRIORITY = ["BGR8Packed", "BayerRG8", "BayerGB8", "Mono8", "RGB8Packed"]

# =============================================================================
# Color Analysis Settings
# =============================================================================

# Default reference color (mid-gray in CIE LAB)
REFERENCE_LAB = [50.0, 0.0, 0.0]  # L=50, a=0, b=0

# Sample area settings
DEFAULT_SAMPLE_SIZE_CM = 1.0  # 1cm square area
MIN_SAMPLE_SIZE_CM = 0.1
MAX_SAMPLE_SIZE_CM = 5.0
SAMPLE_SIZE_STEP = 0.1

# Color difference calculation settings
COLOR_DIFF_PRECISION = 1  # Decimal places for display

# Calibration settings
CALIBRATION_STATUS_TIMEOUT = 5.0  # seconds

# =============================================================================
# Graph Settings
# =============================================================================

# Graph range settings - Optimized for practical color difference analysis
GRAPH_MIN_RANGE = -5   # Minimum value for Delta E graph (practical range)
GRAPH_MAX_RANGE = 5    # Maximum value for Delta E graph (practical range)

# History settings
HISTORY_SIZE = 1000    # Maximum number of history points to maintain

# Quality Grade Thresholds (reflects user requirements)
QUALITY_GRADE_EXCELLENT = 1.0    # Excellent: DE ≤ 1.0
QUALITY_GRADE_GOOD = 2.0         # Good: DE ≤ 2.0  
QUALITY_GRADE_ACCEPTABLE = 3.0   # Acceptable: DE ≤ 3.0 (defective threshold)
QUALITY_GRADE_DEFECTIVE = 5.0    # Defective: DE > 3.0, Out of range: DE > 5.0

# Warning thresholds (adjusted based on quality grade criteria)
WARNING_THRESHOLD_DE = 3.0  # Defective threshold (user requirement)
CRITICAL_THRESHOLD_DE = 5.0  # Out of range threshold

# Graph display settings
GRAPH_TIME_WINDOW = 30  # seconds to display
GRAPH_AUTO_RANGE = False  # Use fixed range

# Graph colors (RGB values)
GRAPH_LINE_COLOR = (0, 255, 255)  # Cyan
GRAPH_BACKGROUND_COLOR = (255, 255, 255)  # White background
GRAPH_GRID_COLOR = (200, 200, 200)  # Light gray grid
GRAPH_TEXT_COLOR = (0, 0, 0)  # Black text

# Quality Grade Colors (color definitions by quality grade)
GRADE_COLORS = {
    'excellent': (0, 200, 0, 80),      # Dark green (Excellent: DE ≤ 1.0)
    'good': (150, 255, 150, 60),       # Light green (Good: DE ≤ 2.0)
    'acceptable': (255, 255, 0, 60),   # Yellow (Acceptable: DE ≤ 3.0)
    'defective': (255, 0, 0, 80),      # Red (Defective: DE > 3.0)
    'out_of_range': (128, 0, 128, 80)  # Purple (Out of range: DE > 5.0)
}

# Legacy tolerance regions (for compatibility)
ACCEPTABLE_REGION_COLOR = GRADE_COLORS['good']      # Good grade color
WARNING_REGION_COLOR = GRADE_COLORS['acceptable']   # Acceptable grade color  
CRITICAL_REGION_COLOR = GRADE_COLORS['defective']   # Defective grade color

# =============================================================================
# Sampling Settings
# =============================================================================

# Frame sampling intervals (milliseconds)
SAMPLING_INTERVAL = 100      # Default sampling interval
MIN_SAMPLING_INTERVAL = 10   # Minimum (fastest)
MAX_SAMPLING_INTERVAL = 1000 # Maximum (slowest)

# Auto-save settings
HISTORY_AUTO_SAVE_INTERVAL = 10  # Save every N data points
SAVE_ON_EXIT = True

# =============================================================================
# GUI Settings
# =============================================================================

# Window settings
WINDOW_TITLE = PROGRAM_TITLE
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 900
WINDOW_DEFAULT_WIDTH = 1400
WINDOW_DEFAULT_HEIGHT = 1000

# Theme settings - WHITE THEME
THEME_DARK = False  # Use white theme

# White theme colors
MAIN_BG_COLOR = "#FFFFFF"        # Pure white
SECONDARY_BG_COLOR = "#F5F5F5"   # Light gray
ACCENT_COLOR = "#0078D4"         # Blue accent
TEXT_COLOR = "#000000"           # Black text
BORDER_COLOR = "#CCCCCC"         # Light gray border

# Widget colors
BUTTON_BG = "#E1E1E1"
BUTTON_HOVER = "#D0D0D0"
BUTTON_PRESSED = "#C0C0C0"
INPUT_BG = "#FFFFFF"
INPUT_BORDER = "#CCCCCC"

# Status colors
STATUS_NORMAL = "#00AA00"   # Green
STATUS_WARNING = "#FF8800"  # Orange
STATUS_ERROR = "#FF0000"    # Red

# Font settings
FONT_FAMILY = "Arial"
FONT_SIZE_TITLE = 14
FONT_SIZE_LABEL = 10
FONT_SIZE_VALUE = 12
FONT_SIZE_STATUS = 11

# Layout settings
SPACING = 10
MARGIN = 15
TAB_HEIGHT = 40

# Update intervals
GUI_UPDATE_INTERVAL = 30      # milliseconds
ANIMATION_UPDATE_INTERVAL = 30
STATUS_UPDATE_INTERVAL = 100

# =============================================================================
# File and Path Settings
# =============================================================================

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directories
HIST_DIR = os.path.join(SCRIPT_DIR, "hist")
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")

# Create directories if they don't exist
for directory in [HIST_DIR, DATA_DIR, CONFIG_DIR]:
    os.makedirs(directory, exist_ok=True)

# File paths
HISTORY_FILE = os.path.join(HIST_DIR, "de_history_basler_advanced.npy")
CONFIG_FILE = os.path.join(CONFIG_DIR, "basler_advanced_config.json")
LOG_FILE = os.path.join(HIST_DIR, "basler_advanced_log.txt")

# Export settings
DEFAULT_EXPORT_FORMAT = "CSV"
CSV_DELIMITER = ","
CSV_ENCODING = "utf-8"

# =============================================================================
# Color Difference Calculation Settings
# =============================================================================

# Delta E calculation methods
DE_METHOD_CIE76 = "CIE76"
DE_METHOD_CIE2000 = "CIE2000"
DEFAULT_DE_METHOD = DE_METHOD_CIE76

# CIEDE2000 weighting factors
CIEDE2000_KL = 1.0  # Lightness weighting
CIEDE2000_KC = 1.0  # Chroma weighting  
CIEDE2000_KH = 1.0  # Hue weighting

# Color space conversion settings
LAB_ILLUMINANT = "D65"  # Standard illuminant
LAB_OBSERVER = "2"      # Standard observer

# =============================================================================
# Warning and Alert Settings
# =============================================================================

# Warning display settings
WARNING_COOLDOWN = 3.0  # seconds between warnings
SHOW_WARNING_POPUP = True
SHOW_WARNING_SOUND = False  # Audio alerts disabled by default

# Quality Grade Alert Levels (alert levels by quality grade)
ALERT_LEVELS = {
    'excellent': (0.0, QUALITY_GRADE_EXCELLENT),           # Excellent: 0.0 ~ 1.0
    'good': (QUALITY_GRADE_EXCELLENT, QUALITY_GRADE_GOOD), # Good: 1.0 ~ 2.0
    'acceptable': (QUALITY_GRADE_GOOD, QUALITY_GRADE_ACCEPTABLE), # Acceptable: 2.0 ~ 3.0
    'defective': (QUALITY_GRADE_ACCEPTABLE, QUALITY_GRADE_DEFECTIVE), # Defective: 3.0 ~ 5.0
    'out_of_range': (QUALITY_GRADE_DEFECTIVE, float('inf')) # Out of range: > 5.0
}

# Quality Grade Status Messages
STATUS_MESSAGES = {
    'excellent': "Status: Excellent Quality (DE ≤ 1.0)",
    'good': "Status: Good Quality (DE ≤ 2.0)", 
    'acceptable': "Status: Acceptable (DE ≤ 3.0)",
    'defective': "Status: Defective - Quality Check Required (DE={:.1f})",
    'out_of_range': "Status: Out of Range - Immediate Check Required (DE={:.1f})",
    'calibrated': "Reference Status: Calibration Complete",
    'not_calibrated': "Reference Status: Reference Color Not Set"
}

# =============================================================================
# Performance Settings
# =============================================================================

# Processing optimization
MAX_PROCESSING_FPS = 30
SKIP_FRAME_THRESHOLD = 100  # Skip processing if queue is too full

# Memory management
MAX_MEMORY_USAGE_MB = 500
CLEANUP_INTERVAL = 1000  # frames

# Debug settings
DEBUG_MODE = False
SHOW_FPS = True
SHOW_PROCESSING_TIME = False
LOG_PERFORMANCE = False

# =============================================================================
# Keyboard Shortcuts
# =============================================================================

# Key mappings
KEY_CALIBRATE = ord('C')
KEY_CALIBRATE_ALT = ord('c')
KEY_TOGGLE_VIEW = ord('V')
KEY_TOGGLE_VIEW_ALT = ord('v')
KEY_SAVE_DATA = ord('S')
KEY_SAVE_DATA_ALT = ord('s')
KEY_LOAD_DATA = ord('L')
KEY_LOAD_DATA_ALT = ord('l')
KEY_RESET_HISTORY = ord('R')
KEY_RESET_HISTORY_ALT = ord('r')
KEY_SET_TARGET = ord('T')
KEY_SET_TARGET_ALT = ord('t')
KEY_EXIT = 27  # ESC
KEY_INFO = 32  # SPACE

# =============================================================================
# Graph Animation Settings
# =============================================================================

# Animation parameters
ANIMATION_ENABLED = True
ANIMATION_SPEED = 1.0
ANIMATION_SMOOTH = True

# Plot settings
PLOT_LINE_WIDTH = 2
PLOT_SYMBOL_SIZE = 8
PLOT_SYMBOL = 'o'

# 3D Graph settings (for future expansion)
ENABLE_3D_GRAPH = False
GRAPH_3D_ROTATION = True
GRAPH_3D_ZOOM = True

# =============================================================================
# Error Handling Settings
# =============================================================================

# Camera error handling
MAX_CAMERA_ERRORS = 10
CAMERA_RECONNECT_DELAY = 2.0  # seconds
CAMERA_TIMEOUT = 5000  # milliseconds

# Processing error handling
MAX_PROCESSING_ERRORS = 100
ERROR_LOG_MAX_SIZE = 1000  # lines

# Recovery settings
AUTO_RECOVERY = True
RECOVERY_ATTEMPTS = 3

# =============================================================================
# Export and Import Settings
# =============================================================================

# Data export formats
EXPORT_FORMATS = ["CSV", "JSON", "NPY"]

# CSV export settings
CSV_INCLUDE_HEADERS = True
CSV_INCLUDE_TIMESTAMP = True

# JSON export settings
JSON_PRETTY_PRINT = True
JSON_INDENT = 2

# Import validation
VALIDATE_IMPORTED_DATA = True
MAX_IMPORT_SIZE_MB = 100

# =============================================================================
# Utility Functions
# =============================================================================

def get_quality_grade(de_value):
    """Get quality grade based on DE value (quality grade determination function)"""
    abs_de = abs(de_value)
    
    if abs_de <= QUALITY_GRADE_EXCELLENT:
        return 'excellent'      # Excellent
    elif abs_de <= QUALITY_GRADE_GOOD:
        return 'good'          # Good
    elif abs_de <= QUALITY_GRADE_ACCEPTABLE:
        return 'acceptable'    # Acceptable
    elif abs_de <= QUALITY_GRADE_DEFECTIVE:
        return 'defective'     # Defective
    else:
        return 'out_of_range'  # Out of range

def get_color_for_de_value(de_value):
    """Get color based on DE value for visualization (return color by quality grade)"""
    grade = get_quality_grade(de_value)
    
    if grade == 'excellent':
        return STATUS_NORMAL    # Green - Excellent
    elif grade == 'good':
        return STATUS_NORMAL    # Green - Good
    elif grade == 'acceptable':
        return STATUS_WARNING   # Yellow - Acceptable
    elif grade == 'defective':
        return STATUS_ERROR     # Red - Defective
    else:
        return STATUS_ERROR     # Red - Out of range

def get_grade_color_rgba(de_value):
    """Get RGBA color tuple for quality grade (RGBA color by quality grade)"""
    grade = get_quality_grade(de_value)
    return GRADE_COLORS.get(grade, GRADE_COLORS['out_of_range'])

def get_status_message(de_value):
    """Get status message for quality grade (status message by quality grade)"""
    grade = get_quality_grade(de_value)
    message_template = STATUS_MESSAGES.get(grade, STATUS_MESSAGES['out_of_range'])
    
    if '{}' in message_template or '{:.1f}' in message_template:
        return message_template.format(de_value)
    else:
        return message_template

def validate_settings():
    """Validate all settings are within acceptable ranges"""
    issues = []
    
    # Validate ranges
    if MIN_SAMPLING_INTERVAL >= MAX_SAMPLING_INTERVAL:
        issues.append("Invalid sampling interval range")
    
    if GRAPH_MIN_RANGE >= GRAPH_MAX_RANGE:
        issues.append("Invalid graph range")
    
    if WARNING_THRESHOLD_DE >= CRITICAL_THRESHOLD_DE:
        issues.append("Invalid threshold range")
    
    return issues

def get_theme_stylesheet():
    """Get complete stylesheet for white theme"""
    return f"""
    QMainWindow {{
        background-color: {MAIN_BG_COLOR};
        color: {TEXT_COLOR};
    }}
    
    QWidget {{
        background-color: {MAIN_BG_COLOR};
        color: {TEXT_COLOR};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_LABEL}px;
    }}
    
    QGroupBox {{
        font-weight: bold;
        font-size: {FONT_SIZE_TITLE}px;
        border: 2px solid {BORDER_COLOR};
        border-radius: 5px;
        margin-top: 1ex;
        padding-top: 10px;
        background-color: {SECONDARY_BG_COLOR};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        background-color: {MAIN_BG_COLOR};
    }}
    
    QPushButton {{
        background-color: {BUTTON_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 3px;
        padding: 5px 10px;
        min-height: 20px;
        font-size: {FONT_SIZE_LABEL}px;
    }}
    
    QPushButton:hover {{
        background-color: {BUTTON_HOVER};
    }}
    
    QPushButton:pressed {{
        background-color: {BUTTON_PRESSED};
    }}
    
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {INPUT_BG};
        border: 1px solid {INPUT_BORDER};
        border-radius: 3px;
        padding: 3px;
        font-size: {FONT_SIZE_VALUE}px;
    }}
    
    QSlider::groove:horizontal {{
        height: 8px;
        background: {SECONDARY_BG_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background: {ACCENT_COLOR};
        border: 1px solid {BORDER_COLOR};
        width: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }}
    
    QTabWidget::pane {{
        border: 1px solid {BORDER_COLOR};
        background-color: {MAIN_BG_COLOR};
    }}
    
    QTabBar::tab {{
        background-color: {SECONDARY_BG_COLOR};
        border: 1px solid {BORDER_COLOR};
        padding: 8px 16px;
        margin-right: 2px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {MAIN_BG_COLOR};
        border-bottom: none;
    }}
    
    QLabel {{
        color: {TEXT_COLOR};
        font-size: {FONT_SIZE_LABEL}px;
    }}
    
    QTextEdit {{
        background-color: {INPUT_BG};
        border: 1px solid {INPUT_BORDER};
        border-radius: 3px;
        font-family: Consolas, monospace;
        font-size: {FONT_SIZE_VALUE}px;
    }}
    """

# =============================================================================
# Initialize Settings
# =============================================================================

# Validate settings on import
validation_issues = validate_settings()
if validation_issues:
    print("Warning: Settings validation issues found:")
    for issue in validation_issues:
        print(f"  - {issue}")

# Print configuration loaded message
print(f"Basler Advanced Color Analysis Settings v{VERSION} loaded")
print(f"  Theme: {'Light' if not THEME_DARK else 'Dark'}")
print(f"  Graph Range: {GRAPH_MIN_RANGE} to {GRAPH_MAX_RANGE}")
print(f"  History Size: {HISTORY_SIZE}")
print(f"  Sampling: {MIN_SAMPLING_INTERVAL}-{MAX_SAMPLING_INTERVAL}ms")