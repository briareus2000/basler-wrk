# 2025-08-25
# Advanced Basler acA4024-8gc Color Difference Analysis Dashboard
# PyQt5-based advanced color difference analysis with 3D graphs and CIEDE2000

import os
import sys
import time
import math
import traceback
from typing import Optional, Dict, Any

import numpy as np
import cv2

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QSlider, QCheckBox, QPushButton, QComboBox, QSpinBox, 
    QDoubleSpinBox, QGroupBox, QSplitter, QMessageBox, QProgressBar, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor, QPalette

# PyQtGraph for advanced graphing
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore
from collections import deque

# Local modules
try:
    from . import glob_basler_cmd_delta_2v as gb
    from . import lib_basler_cmd_delta_2v as lb
except ImportError:
    import glob_basler_cmd_delta_2v as gb
    import lib_basler_cmd_delta_2v as lb

# =============================================================================
# DeltaEGraph Class - Advanced Real-time Graph
# =============================================================================

class DeltaEGraph(QWidget):
    """Advanced graph widget to display DE values over time with pyqtgraph"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Initialize graph widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("Delta E Time Series Analysis", color="k", size="14pt")
        self.plot_widget.setLabel("left", "Delta E", color="k", size="12pt")
        self.plot_widget.setLabel("bottom", "Time (seconds)", color="k", size="12pt")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setBackground(gb.GRAPH_BACKGROUND_COLOR)  # White background
        
        # Set Y axis range from global settings
        self.plot_widget.setYRange(gb.GRAPH_MIN_RANGE, gb.GRAPH_MAX_RANGE)
        
        # Add quality grade regions (4-level quality grade regions)
        # 1. Excellent grade region (DE ≤ 1.0) - Dark green
        self.excellent_region_pos = pg.LinearRegionItem(
            [0, gb.QUALITY_GRADE_EXCELLENT], 
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['excellent'], 
            movable=False
        )
        self.plot_widget.addItem(self.excellent_region_pos)
        
        self.excellent_region_neg = pg.LinearRegionItem(
            [-gb.QUALITY_GRADE_EXCELLENT, 0], 
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['excellent'], 
            movable=False
        )
        self.plot_widget.addItem(self.excellent_region_neg)
        
        # 2. Good grade region (1.0 < DE ≤ 2.0) - Light green
        self.good_region_pos = pg.LinearRegionItem(
            [gb.QUALITY_GRADE_EXCELLENT, gb.QUALITY_GRADE_GOOD],
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['good'],
            movable=False
        )
        self.plot_widget.addItem(self.good_region_pos)
        
        self.good_region_neg = pg.LinearRegionItem(
            [-gb.QUALITY_GRADE_GOOD, -gb.QUALITY_GRADE_EXCELLENT],
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['good'],
            movable=False
        )
        self.plot_widget.addItem(self.good_region_neg)
        
        # 3. Acceptable grade region (2.0 < DE ≤ 3.0) - Yellow
        self.acceptable_region_pos = pg.LinearRegionItem(
            [gb.QUALITY_GRADE_GOOD, gb.QUALITY_GRADE_ACCEPTABLE],
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['acceptable'],
            movable=False
        )
        self.plot_widget.addItem(self.acceptable_region_pos)
        
        self.acceptable_region_neg = pg.LinearRegionItem(
            [-gb.QUALITY_GRADE_ACCEPTABLE, -gb.QUALITY_GRADE_GOOD],
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['acceptable'],
            movable=False
        )
        self.plot_widget.addItem(self.acceptable_region_neg)
        
        # 4. Defective grade region (3.0 < DE ≤ 5.0) - Red
        self.defective_region_pos = pg.LinearRegionItem(
            [gb.QUALITY_GRADE_ACCEPTABLE, gb.GRAPH_MAX_RANGE],
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['defective'],
            movable=False
        )
        self.plot_widget.addItem(self.defective_region_pos)
        
        self.defective_region_neg = pg.LinearRegionItem(
            [gb.GRAPH_MIN_RANGE, -gb.QUALITY_GRADE_ACCEPTABLE],
            orientation=pg.LinearRegionItem.Horizontal,
            brush=gb.GRADE_COLORS['defective'],
            movable=False
        )
        self.plot_widget.addItem(self.defective_region_neg)
        
        # Add baseline (zero line)
        self.zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(gb.GRAPH_TEXT_COLOR, width=1))
        self.plot_widget.addItem(self.zero_line)
        
        # Add quality grade threshold lines (quality grade dividing lines)
        # Excellent-Good dividing line (DE = 1.0)
        self.excellent_line_pos = pg.InfiniteLine(
            pos=gb.QUALITY_GRADE_EXCELLENT, angle=0, 
            pen=pg.mkPen('darkgreen', width=1, style=Qt.DotLine)
        )
        self.plot_widget.addItem(self.excellent_line_pos)
        
        self.excellent_line_neg = pg.InfiniteLine(
            pos=-gb.QUALITY_GRADE_EXCELLENT, angle=0, 
            pen=pg.mkPen('darkgreen', width=1, style=Qt.DotLine)
        )
        self.plot_widget.addItem(self.excellent_line_neg)
        
        # Good-Acceptable dividing line (DE = 2.0)
        self.good_line_pos = pg.InfiniteLine(
            pos=gb.QUALITY_GRADE_GOOD, angle=0, 
            pen=pg.mkPen('green', width=1, style=Qt.DashLine)
        )
        self.plot_widget.addItem(self.good_line_pos)
        
        self.good_line_neg = pg.InfiniteLine(
            pos=-gb.QUALITY_GRADE_GOOD, angle=0, 
            pen=pg.mkPen('green', width=1, style=Qt.DashLine)
        )
        self.plot_widget.addItem(self.good_line_neg)
        
        # Acceptable-Defective dividing line (DE = 3.0) - Important defective threshold line
        self.defective_line_pos = pg.InfiniteLine(
            pos=gb.QUALITY_GRADE_ACCEPTABLE, angle=0, 
            pen=pg.mkPen('red', width=2, style=Qt.SolidLine)
        )
        self.plot_widget.addItem(self.defective_line_pos)
        
        self.defective_line_neg = pg.InfiniteLine(
            pos=-gb.QUALITY_GRADE_ACCEPTABLE, angle=0, 
            pen=pg.mkPen('red', width=2, style=Qt.SolidLine)
        )
        self.plot_widget.addItem(self.defective_line_neg)
        
        # Add graph to layout
        self.layout.addWidget(self.plot_widget)
        
        # Initialize data
        self.max_points = gb.HISTORY_SIZE
        self.times = deque(maxlen=self.max_points)
        self.de_values = deque(maxlen=self.max_points)
        self.start_time = time.time()
        
        # Initialize plot data line
        self.data_line = self.plot_widget.plot(
            [], [], 
            pen=pg.mkPen(gb.GRAPH_LINE_COLOR, width=gb.PLOT_LINE_WIDTH), 
            symbolBrush=gb.GRAPH_LINE_COLOR, 
            symbolPen='w', 
            symbol=gb.PLOT_SYMBOL, 
            symbolSize=gb.PLOT_SYMBOL_SIZE
        )
        
        # Visualization mode
        self.heatmap_mode = False
        self.scatter_plot = None
        
        # Animation timer
        if gb.ANIMATION_ENABLED:
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self.update_animation)
            self.animation_timer.start(gb.ANIMATION_UPDATE_INTERVAL)
        
        # Load saved history
        self.load_history()
    
    def load_history(self):
        """Load saved history data from file if available"""
        try:
            if os.path.exists(gb.HISTORY_FILE):
                history_data = np.load(gb.HISTORY_FILE, allow_pickle=True).item()
                saved_times = history_data.get('times', [])
                saved_values = history_data.get('values', [])
                
                if len(saved_times) > 0 and len(saved_values) > 0:
                    # Adjust timestamps to current session
                    time_offset = self.start_time - history_data.get('start_time', self.start_time)
                    
                    for t, v in zip(saved_times, saved_values):
                        self.times.append(t - time_offset)
                        self.de_values.append(v)
                    
                    print(f"Loaded {len(saved_times)} history data points")
                    self.update_plot()
        except Exception as e:
            print(f"Error loading history data: {e}")
    
    def save_history(self):
        """Save history data to file for persistence"""
        try:
            history_data = {
                'start_time': self.start_time,
                'times': list(self.times),
                'values': list(self.de_values)
            }
            
            np.save(gb.HISTORY_FILE, history_data)
            print(f"Saved {len(self.times)} history data points")
        except Exception as e:
            print(f"Error saving history data: {e}")
    
    def update_animation(self):
        """Update animation effects"""
        if gb.ANIMATION_SMOOTH and len(self.de_values) > 0:
            # Implement smooth animation if needed
            pass
    
    def toggle_view_mode(self):
        """Toggle between line and heatmap visualization modes"""
        self.heatmap_mode = not self.heatmap_mode
        
        if self.heatmap_mode:
            # Hide line graph
            self.data_line.setData([], [])
            
            # Create heatmap visualization (colors by quality grade)
            if len(self.times) > 0:
                colors = []
                for de in self.de_values:
                    # Apply colors by quality grade
                    grade_color = gb.get_grade_color_rgba(de)
                    colors.append(pg.mkColor(*grade_color))
                
                # Remove existing scatter plot
                if self.scatter_plot is not None:
                    self.plot_widget.removeItem(self.scatter_plot)
                
                # Create new scatter plot
                self.scatter_plot = pg.ScatterPlotItem(
                    x=list(self.times), 
                    y=list(self.de_values),
                    brush=colors,
                    size=15,
                    pen=None
                )
                self.plot_widget.addItem(self.scatter_plot)
        else:
            # Return to line graph mode
            if self.scatter_plot is not None:
                self.plot_widget.removeItem(self.scatter_plot)
                self.scatter_plot = None
            
            # Restore line graph
            self.data_line.setData(list(self.times), list(self.de_values))
    
    def add_point(self, de_value: float) -> bool:
        """Add new DE value to graph"""
        current_time = time.time() - self.start_time
        self.times.append(current_time)
        self.de_values.append(de_value)
        
        # Update graph
        self.update_plot()
        
        # Save history periodically
        if len(self.de_values) % gb.HISTORY_AUTO_SAVE_INTERVAL == 0:
            self.save_history()
        
        # Check if DE value exceeds quality thresholds (quality grade determination)
        grade = gb.get_quality_grade(de_value)
        # Return warning if defective or higher (defective: defective, out of range: out_of_range)
        return grade in ['defective', 'out_of_range']
    
    def update_plot(self):
        """Update graph display"""
        if len(self.times) > 0:
            if self.heatmap_mode and self.scatter_plot is not None:
                # Update heatmap (apply colors by quality grade)
                colors = []
                for de in self.de_values:
                    grade_color = gb.get_grade_color_rgba(de)
                    colors.append(pg.mkColor(*grade_color))
                
                self.scatter_plot.setData(x=list(self.times), y=list(self.de_values), brush=colors)
            else:
                # Update line graph
                self.data_line.setData(list(self.times), list(self.de_values))
            
            # Auto-adjust x-axis range (show last time window)
            if len(self.times) > 1 and gb.GRAPH_AUTO_RANGE:
                self.plot_widget.setXRange(
                    max(0, self.times[-1] - gb.GRAPH_TIME_WINDOW), 
                    max(gb.GRAPH_TIME_WINDOW, self.times[-1] + 2)
                )

# =============================================================================
# ColorAnalyzerTab Class - Advanced Color Analysis Interface
# =============================================================================

class ColorAnalyzerTab(QWidget):
    """Advanced color difference analysis tab with CIEDE2000 support"""
    
    def __init__(self):
        super().__init__()
        
        # Core components
        self.color_analyzer = lb.AdvancedColorAnalyzer()
        self.data_manager = lb.AdvancedDataManager()
        
        # UI state
        self.last_warning_time = 0
        self.warning_cooldown = gb.WARNING_COOLDOWN
        
        # Current measurements
        self.current_lab_values = None
        self.current_analysis = None
        
        # Initialize UI
        self.init_ui()
        
        # Update timer for status display
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_display)
        self.status_timer.start(gb.STATUS_UPDATE_INTERVAL)
    
    def init_ui(self):
        """Initialize UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Top display area
        display_layout = QHBoxLayout()
        
        # Camera display
        self.display_label = QLabel("Camera Display")
        self.display_label.setMinimumSize(640, 480)
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setStyleSheet("border: 2px solid #CCCCCC; background-color: #F5F5F5;")
        display_layout.addWidget(self.display_label, 2)
        
        # Delta E graph
        try:
            self.de_graph = DeltaEGraph(self)
            self.de_graph.setMinimumSize(400, 400)
            display_layout.addWidget(self.de_graph, 2)
        except Exception as e:
            print(f"Graph initialization error: {e}")
            self.de_graph = QLabel("Graph initialization failed")
            self.de_graph.setAlignment(Qt.AlignCenter)
            self.de_graph.setStyleSheet("border: 2px solid red; color: red; font-size: 16px;")
            display_layout.addWidget(self.de_graph, 2)
        
        layout.addLayout(display_layout)
        
        # Control panels
        controls_layout = QHBoxLayout()
        
        # Measurement settings
        measure_group = QGroupBox("Measurement Settings")
        measure_layout = QGridLayout(measure_group)
        
        # Sample size control
        measure_layout.addWidget(QLabel("Sample Size (cm):"), 0, 0)
        self.sample_size_spin = QDoubleSpinBox()
        self.sample_size_spin.setRange(gb.MIN_SAMPLE_SIZE_CM, gb.MAX_SAMPLE_SIZE_CM)
        self.sample_size_spin.setSingleStep(gb.SAMPLE_SIZE_STEP)
        self.sample_size_spin.setValue(gb.DEFAULT_SAMPLE_SIZE_CM)
        self.sample_size_spin.valueChanged.connect(self.update_sample_size)
        measure_layout.addWidget(self.sample_size_spin, 0, 1)
        
        # Delta E calculation method
        measure_layout.addWidget(QLabel("Delta E Method:"), 1, 0)
        self.de_method_combo = QComboBox()
        self.de_method_combo.addItems([gb.DE_METHOD_CIE76, gb.DE_METHOD_CIE2000])
        self.de_method_combo.setCurrentText(gb.DEFAULT_DE_METHOD)
        self.de_method_combo.currentTextChanged.connect(self.update_de_method)
        measure_layout.addWidget(self.de_method_combo, 1, 1)
        
        # Calibration button
        self.calibrate_btn = QPushButton("Set Reference Color (C)")
        self.calibrate_btn.clicked.connect(self.calibrate)
        self.calibrate_btn.setStyleSheet("font-weight: bold; min-height: 30px;")
        measure_layout.addWidget(self.calibrate_btn, 2, 0, 1, 2)
        
        # Calibration status
        self.calibration_status = QLabel("Reference Status: Not Set")
        self.calibration_status.setStyleSheet("color: #FF8800;")
        measure_layout.addWidget(self.calibration_status, 3, 0, 1, 2)
        
        # Graph mode toggle
        self.toggle_view_btn = QPushButton("Toggle Graph Mode (V)")
        self.toggle_view_btn.clicked.connect(self.toggle_graph_mode)
        measure_layout.addWidget(self.toggle_view_btn, 4, 0, 1, 2)
        
        controls_layout.addWidget(measure_group)
        
        # Color difference results
        results_group = QGroupBox("Color Difference Results")
        results_layout = QGridLayout(results_group)
        
        # Result labels
        self.result_labels = {}
        result_items = [
            ('dl', "DL (Lightness):"),
            ('da', "Da (Red-Green):"),
            ('db', "Db (Yellow-Blue):"),
            ('dc', "DC (Chroma):"),
            ('dh', "Dh (Hue):"),
            ('de76', "DE (CIE76):"),
            ('de2000', "DE (CIEDE2000):")
        ]
        
        for i, (key, label_text) in enumerate(result_items):
            results_layout.addWidget(QLabel(label_text), i, 0)
            self.result_labels[key] = QLabel("0.0")
            self.result_labels[key].setMinimumWidth(80)
            self.result_labels[key].setStyleSheet(f"font-size: {gb.FONT_SIZE_VALUE}px; font-weight: bold;")
            results_layout.addWidget(self.result_labels[key], i, 1)
        
        controls_layout.addWidget(results_group)
        
        # Current values and status
        status_group = QGroupBox("Current Values & Status")
        status_layout = QGridLayout(status_group)
        
        # Current color values
        self.current_labels = {}
        current_items = [
            ('rgb', "RGB:"),
            ('lab', "LAB:")
        ]
        
        for i, (key, label_text) in enumerate(current_items):
            status_layout.addWidget(QLabel(label_text), i, 0)
            self.current_labels[key] = QLabel("0, 0, 0")
            self.current_labels[key].setStyleSheet(f"font-size: {gb.FONT_SIZE_VALUE}px;")
            status_layout.addWidget(self.current_labels[key], i, 1)
        
        # Status display
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet(f"color: {gb.STATUS_NORMAL}; font-weight: bold; font-size: {gb.FONT_SIZE_STATUS}px;")
        status_layout.addWidget(self.status_label, 2, 0, 1, 2)
        
        # Statistics display
        self.stats_label = QLabel("Statistics: No data")
        self.stats_label.setStyleSheet(f"font-size: {gb.FONT_SIZE_LABEL}px;")
        status_layout.addWidget(self.stats_label, 3, 0, 1, 2)
        
        controls_layout.addWidget(status_group)
        
        layout.addLayout(controls_layout)
        
        # Data management buttons
        data_buttons_layout = QHBoxLayout()
        
        self.save_data_btn = QPushButton("Save Data (S)")
        self.save_data_btn.clicked.connect(self.save_data)
        data_buttons_layout.addWidget(self.save_data_btn)
        
        self.load_data_btn = QPushButton("Load Data (L)")
        self.load_data_btn.clicked.connect(self.load_data)
        data_buttons_layout.addWidget(self.load_data_btn)
        
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        data_buttons_layout.addWidget(self.export_csv_btn)
        
        self.reset_btn = QPushButton("Reset History (R)")
        self.reset_btn.clicked.connect(self.reset_history)
        data_buttons_layout.addWidget(self.reset_btn)
        
        data_buttons_layout.addStretch()
        
        layout.addLayout(data_buttons_layout)
    
    def update_sample_size(self, value: float):
        """Update sampling area size"""
        if self.color_analyzer.set_sample_size(value):
            print(f"Sample size updated to {value} cm")
    
    def update_de_method(self, method: str):
        """Update Delta E calculation method"""
        self.color_analyzer.de_method = method
        print(f"Delta E method changed to {method}")
    
    def calibrate(self):
        """Calibrate reference color using current measurement"""
        if self.current_lab_values is not None:
            if self.color_analyzer.calibrate(self.current_lab_values):
                self.calibration_status.setText(
                    f"Reference Set: L={self.current_lab_values[0]:.1f}, "
                    f"a={self.current_lab_values[1]:.1f}, b={self.current_lab_values[2]:.1f}"
                )
                self.calibration_status.setStyleSheet(f"color: {gb.STATUS_NORMAL}; font-weight: bold;")
                print("Calibration successful")
            else:
                print("Calibration failed")
        else:
            print("No current measurement available for calibration")
    
    def toggle_graph_mode(self):
        """Toggle graph visualization mode"""
        if hasattr(self.de_graph, 'toggle_view_mode'):
            self.de_graph.toggle_view_mode()
            mode_name = "Heatmap" if self.de_graph.heatmap_mode else "Line"
            self.toggle_view_btn.setText(f"Graph Mode: {mode_name}")
    
    def save_data(self):
        """Save current data"""
        if self.data_manager.save_history():
            print("Data saved successfully")
        else:
            print("Data save failed")
    
    def load_data(self):
        """Load saved data"""
        if self.data_manager.load_history():
            print("Data loaded successfully")
        else:
            print("Data load failed")
    
    def export_csv(self):
        """Export data to CSV"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(gb.DATA_DIR, f"basler_color_data_{timestamp}.csv")
        
        if self.data_manager.export_csv(filename):
            print(f"Data exported to {filename}")
        else:
            print("CSV export failed")
    
    def reset_history(self):
        """Reset all history data"""
        reply = QMessageBox.question(
            self, "Reset History", 
            "Are you sure you want to reset all history data?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_manager.clear_history()
            if hasattr(self.de_graph, 'times'):
                self.de_graph.times.clear()
                self.de_graph.de_values.clear()
                self.de_graph.update_plot()
            print("History reset")
    
    def update_status_display(self):
        """Update status and statistics display"""
        try:
            # Update statistics
            stats = self.data_manager.get_statistics()
            if stats:
                stats_text = f"Count: {stats['count']}, Mean DE: {stats['de_mean']:.2f}, Std: {stats['de_std']:.2f}"
                if stats.get('warning_count', 0) > 0:
                    stats_text += f", Warnings: {stats['warning_count']}"
                if stats.get('critical_count', 0) > 0:
                    stats_text += f", Critical: {stats['critical_count']}"
                
                self.stats_label.setText(f"Statistics: {stats_text}")
            
        except Exception as e:
            print(f"Status update error: {e}")
    
    @pyqtSlot(object)
    def process_color_analysis(self, analysis_result: Dict[str, Any]):
        """Process color analysis results from camera thread"""
        try:
            if analysis_result is None:
                return
            
            self.current_analysis = analysis_result
            self.current_lab_values = np.array([
                analysis_result['lab']['l'],
                analysis_result['lab']['a'], 
                analysis_result['lab']['b']
            ])
            
            # Add to data manager
            self.data_manager.add_data_point(analysis_result)
            
            # Update UI
            self.update_results_display(analysis_result)
            
            # Add to graph and check for warnings
            de_value = analysis_result['color_diffs']['de']
            is_warning = self.de_graph.add_point(de_value)
            
            # Handle warning display
            if is_warning and gb.SHOW_WARNING_POPUP:
                current_time = time.time()
                if current_time - self.last_warning_time > self.warning_cooldown:
                    self.show_warning_message(de_value)
                    self.last_warning_time = current_time
            
        except Exception as e:
            print(f"Color analysis processing error: {e}")
    
    def update_results_display(self, analysis_result: Dict[str, Any]):
        """Update UI with analysis results"""
        try:
            # Update current color values
            rgb = analysis_result['rgb']
            lab = analysis_result['lab']
            
            self.current_labels['rgb'].setText(f"R={rgb['r']:.1f}, G={rgb['g']:.1f}, B={rgb['b']:.1f}")
            self.current_labels['lab'].setText(f"L={lab['l']:.1f}, a={lab['a']:.1f}, b={lab['b']:.1f}")
            
            # Update color difference results
            color_diffs = analysis_result['color_diffs']
            for key, label in self.result_labels.items():
                if key in color_diffs:
                    value = color_diffs[key]
                    label.setText(f"{value:.1f}")
                    
                    # Quality grade based color coding
                    if key in ['de76', 'de2000', 'de']:
                        grade = gb.get_quality_grade(value)
                        if grade == 'excellent':
                            label.setStyleSheet(f"color: {gb.STATUS_NORMAL}; font-weight: bold; background-color: #E8F5E8;")
                        elif grade == 'good':
                            label.setStyleSheet(f"color: {gb.STATUS_NORMAL}; font-weight: bold;")
                        elif grade == 'acceptable':
                            label.setStyleSheet(f"color: {gb.STATUS_WARNING}; font-weight: bold;")
                        elif grade == 'defective':
                            label.setStyleSheet(f"color: {gb.STATUS_ERROR}; font-weight: bold; background-color: #FFE8E8;")
                        else:  # out_of_range
                            label.setStyleSheet(f"color: {gb.STATUS_ERROR}; font-weight: bold; background-color: #E8E8FF;")
                    else:
                        label.setStyleSheet(f"font-size: {gb.FONT_SIZE_VALUE}px; font-weight: bold;")
            
            # Update status (status message by quality grade)
            de_value = color_diffs['de']
            grade = gb.get_quality_grade(de_value)
            
            # Status message and color settings by quality grade
            status_msg = gb.get_status_message(de_value)
            
            if grade == 'excellent':
                status_color = gb.STATUS_NORMAL
                bg_style = "background-color: #E8F5E8; border-radius: 3px; padding: 2px;"
            elif grade == 'good':
                status_color = gb.STATUS_NORMAL
                bg_style = ""
            elif grade == 'acceptable':
                status_color = gb.STATUS_WARNING
                bg_style = "background-color: #FFF8E1; border-radius: 3px; padding: 2px;"
            elif grade == 'defective':
                status_color = gb.STATUS_ERROR
                bg_style = "background-color: #FFE8E8; border-radius: 3px; padding: 2px;"
            else:  # out_of_range
                status_color = gb.STATUS_ERROR
                bg_style = "background-color: #E8E8FF; border-radius: 3px; padding: 2px;"
            
            self.status_label.setText(status_msg)
            self.status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: {gb.FONT_SIZE_STATUS}px; {bg_style}")
            
        except Exception as e:
            print(f"Results display update error: {e}")
    
    def show_warning_message(self, de_value: float):
        """Display quality grade based warning message"""
        try:
            grade = gb.get_quality_grade(de_value)
            
            msg = QMessageBox()
            
            if grade == 'defective':
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Poor Quality Warning")
                msg.setText(f"Color difference is in defective grade: DE = {de_value:.2f}")
                msg.setInformativeText(f"Defective threshold: DE > ±{gb.QUALITY_GRADE_ACCEPTABLE}\nPlease check product quality immediately.")
            elif grade == 'out_of_range':
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Color Difference Out of Range")
                msg.setText(f"Color difference exceeded measurement range: DE = {de_value:.2f}")
                msg.setInformativeText(f"Measurement range: ±{gb.QUALITY_GRADE_DEFECTIVE}\nPlease check the system immediately.")
            else:
                # Should not happen, but just in case
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Color Difference Alert")
                msg.setText(f"Color difference: DE = {de_value:.2f}")
                msg.setInformativeText("Please check quality status.")
            
            msg.setStandardButtons(QMessageBox.Ok)
            
            # Show message asynchronously
            QTimer.singleShot(0, msg.exec_)
            
        except Exception as e:
            print(f"Warning message error: {e}")
    
    @pyqtSlot(object)
    def process_frames(self, color_image):
        """Process camera frames and display"""
        try:
            if color_image is None:
                return
            
            # Create display copy
            display_image = color_image.copy()
            height, width = display_image.shape[:2]
            
            # Add sampling area visualization if current analysis exists
            if self.current_analysis:
                area = self.current_analysis['sampling_area']
                de_value = self.current_analysis['color_diffs']['de']
                grade = gb.get_quality_grade(de_value)
                
                # Sampling area colors by quality grade
                if grade == 'excellent':
                    rect_color = (0, 200, 0)  # Dark green
                elif grade == 'good':
                    rect_color = (0, 255, 0)  # Bright green
                elif grade == 'acceptable':
                    rect_color = (0, 255, 255)  # Yellow
                elif grade == 'defective':
                    rect_color = (0, 0, 255)  # Red
                else:  # out_of_range
                    rect_color = (128, 0, 128)  # Purple
                
                cv2.rectangle(display_image, (area['x1'], area['y1']), (area['x2'], area['y2']), rect_color, 2)
                
                # Add sample info with quality grade
                cv2.putText(display_image, f"Sample: {self.current_analysis['sample_size_cm']:.1f}cm", 
                           (area['x1'], area['y1'] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, rect_color, 2)
                
                # Add quality grade and DE value
                grade_text = {
                    'excellent': 'Excellent',
                    'good': 'Good', 
                    'acceptable': 'Acceptable',
                    'defective': 'Defective',
                    'out_of_range': 'Out of Range'
                }
                cv2.putText(display_image, f"{grade_text[grade]}: DE={de_value:.2f}", 
                           (area['x1'], area['y1'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, rect_color, 2)
            
            # Add calibration status
            if self.color_analyzer.is_calibrated:
                cv2.putText(display_image, "Calibrated", (width - 150, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add DE method info
            cv2.putText(display_image, f"Method: {self.color_analyzer.de_method}", 
                       (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Convert and display
            self.display_label.setPixmap(self.convert_cv_qt(display_image))
            
        except Exception as e:
            print(f"Frame processing error: {e}")
    
    def convert_cv_qt(self, cv_img):
        """Convert OpenCV image to QPixmap"""
        try:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            return QPixmap.fromImage(convert_to_Qt_format)
        except Exception as e:
            print(f"Image conversion error: {e}")
            return QPixmap()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()
        
        if key in [gb.KEY_CALIBRATE, gb.KEY_CALIBRATE_ALT]:
            self.calibrate()
        elif key in [gb.KEY_TOGGLE_VIEW, gb.KEY_TOGGLE_VIEW_ALT]:
            self.toggle_graph_mode()
        elif key in [gb.KEY_SAVE_DATA, gb.KEY_SAVE_DATA_ALT]:
            self.save_data()
        elif key in [gb.KEY_LOAD_DATA, gb.KEY_LOAD_DATA_ALT]:
            self.load_data()
        elif key in [gb.KEY_RESET_HISTORY, gb.KEY_RESET_HISTORY_ALT]:
            self.reset_history()

# =============================================================================
# MainWindow Class - Main Application Window
# =============================================================================

class MainWindow(QMainWindow):
    """Main application window with advanced features"""
    
    def __init__(self):
        super().__init__()
        
        # Window settings
        self.setWindowTitle(gb.WINDOW_TITLE)
        self.setMinimumSize(gb.WINDOW_MIN_WIDTH, gb.WINDOW_MIN_HEIGHT)
        self.resize(gb.WINDOW_DEFAULT_WIDTH, gb.WINDOW_DEFAULT_HEIGHT)
        
        # Apply white theme
        self.setStyleSheet(gb.get_theme_stylesheet())
        
        # Camera thread
        self.camera_thread = None
        
        # Initialize UI
        self.init_ui()
        
        # Start camera thread
        self.start_camera_thread()
    
    def init_ui(self):
        """Initialize user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(gb.SPACING)
        main_layout.setContentsMargins(gb.MARGIN, gb.MARGIN, gb.MARGIN, gb.MARGIN)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMinimumHeight(gb.TAB_HEIGHT)
        
        # Color analysis tab
        self.color_analyzer_tab = ColorAnalyzerTab()
        self.tabs.addTab(self.color_analyzer_tab, "Color Analysis")
        
        # Add future tabs here (e.g., Settings, Data Export, etc.)
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        # Camera status
        self.camera_status = QLabel("Camera Status: Initializing...")
        self.camera_status.setStyleSheet(f"color: {gb.STATUS_WARNING}; font-size: {gb.FONT_SIZE_LABEL}px;")
        status_layout.addWidget(self.camera_status)
        
        # Sampling interval control
        status_layout.addWidget(QLabel("Sampling Interval:"))
        
        self.sampling_slider = QSlider(Qt.Horizontal)
        self.sampling_slider.setRange(gb.MIN_SAMPLING_INTERVAL, gb.MAX_SAMPLING_INTERVAL)
        self.sampling_slider.setValue(gb.SAMPLING_INTERVAL)
        self.sampling_slider.setInvertedAppearance(True)  # Right = faster
        self.sampling_slider.valueChanged.connect(self.update_sampling_interval)
        self.sampling_slider.setMaximumWidth(200)
        self.sampling_slider.setToolTip("Adjust sampling speed (right = faster)")
        status_layout.addWidget(self.sampling_slider)
        
        self.sampling_value_label = QLabel(f"{gb.SAMPLING_INTERVAL} ms")
        self.sampling_value_label.setMinimumWidth(50)
        status_layout.addWidget(self.sampling_value_label)
        
        status_layout.addStretch()
        
        # Version info
        version_label = QLabel(f"v{gb.VERSION}")
        version_label.setStyleSheet(f"color: gray; font-size: {gb.FONT_SIZE_LABEL}px;")
        status_layout.addWidget(version_label)
        
        main_layout.addLayout(status_layout)
        
        # GUI update timer
        self.gui_update_timer = QTimer()
        self.gui_update_timer.timeout.connect(self.update_gui)
        self.gui_update_timer.start(gb.GUI_UPDATE_INTERVAL)
    
    def start_camera_thread(self):
        """Start camera processing thread"""
        try:
            self.camera_thread = lb.BaslerCameraThread()
            
            # Set color analyzer
            self.camera_thread.set_color_analyzer(self.color_analyzer_tab.color_analyzer)
            
            # Connect signals
            self.camera_thread.frame_signal.connect(self.color_analyzer_tab.process_frames)
            self.camera_thread.color_analysis_signal.connect(self.color_analyzer_tab.process_color_analysis)
            self.camera_thread.error_signal.connect(self.handle_camera_error)
            self.camera_thread.status_signal.connect(self.handle_camera_status)
            
            # Start thread
            self.camera_thread.start()
            
            print("Camera thread started")
            
        except Exception as e:
            error_msg = f"Failed to start camera thread: {e}"
            print(error_msg)
            self.camera_status.setText("Camera Status: Failed to start")
            self.camera_status.setStyleSheet(f"color: {gb.STATUS_ERROR}; font-weight: bold;")
    
    def update_sampling_interval(self, value: int):
        """Update camera sampling interval"""
        self.sampling_value_label.setText(f"{value} ms")
        
        if self.camera_thread:
            self.camera_thread.set_sampling_interval(value)
    
    @pyqtSlot(str)
    def handle_camera_error(self, error_msg: str):
        """Handle camera error messages"""
        print(f"Camera error: {error_msg}")
        self.camera_status.setText(f"Camera Status: Error - {error_msg[:30]}...")
        self.camera_status.setStyleSheet(f"color: {gb.STATUS_ERROR}; font-weight: bold;")
    
    @pyqtSlot(str)
    def handle_camera_status(self, status_msg: str):
        """Handle camera status updates"""
        print(f"Camera status: {status_msg}")
        
        if "connected" in status_msg.lower() or "ready" in status_msg.lower():
            self.camera_status.setText(f"Camera Status: {status_msg}")
            self.camera_status.setStyleSheet(f"color: {gb.STATUS_NORMAL}; font-weight: bold;")
        else:
            self.camera_status.setText(f"Camera Status: {status_msg}")
            self.camera_status.setStyleSheet(f"color: {gb.STATUS_WARNING};")
    
    def update_gui(self):
        """Update GUI elements periodically"""
        try:
            # Update FPS display if available
            if self.camera_thread and hasattr(self.camera_thread, 'fps') and gb.SHOW_FPS:
                if self.camera_thread.fps > 0:
                    fps_text = f" | FPS: {self.camera_thread.fps:.1f}"
                    current_text = self.camera_status.text()
                    if " | FPS:" in current_text:
                        current_text = current_text.split(" | FPS:")[0]
                    self.camera_status.setText(current_text + fps_text)
        
        except Exception as e:
            if gb.DEBUG_MODE:
                print(f"GUI update error: {e}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        print("Shutting down application...")
        
        try:
            # Save history data
            if hasattr(self.color_analyzer_tab, 'data_manager'):
                self.color_analyzer_tab.data_manager.save_history()
            
            if hasattr(self.color_analyzer_tab, 'de_graph'):
                self.color_analyzer_tab.de_graph.save_history()
            
            # Stop camera thread
            if self.camera_thread:
                self.camera_thread.stop()
            
        except Exception as e:
            print(f"Shutdown error: {e}")
        
        event.accept()

# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main application function"""
    # Set PyQtGraph configuration
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName(gb.PROGRAM_TITLE)
    app.setApplicationVersion(gb.VERSION)
    app.setStyle('Fusion')  # Use Fusion style for better appearance
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        
        print(f"=== {gb.PROGRAM_TITLE} v{gb.VERSION} ===")
        print("Application started successfully")
        
        # Run application
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Application startup failed: {e}")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()