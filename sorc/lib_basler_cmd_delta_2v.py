# 2025-08-25
# Advanced Basler acA4024-8gc Color Difference Analysis Library
# Core classes for camera threading, CIEDE2000 color analysis, and data management

import os
import sys
import time
import math
import json
import logging
import traceback
from collections import deque
from typing import Optional, Tuple, Dict, List, Any

import numpy as np
import cv2
from pypylon import pylon

# PyQt5 imports for threading
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox

# Global settings import
try:
    from . import glob_basler_cmd_delta_2v as gb
except ImportError:
    import glob_basler_cmd_delta_2v as gb

# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging():
    """Setup advanced logging system"""
    logger = logging.getLogger('BaslerAdvancedColorAnalysis')
    logger.setLevel(logging.INFO if not gb.DEBUG_MODE else logging.DEBUG)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(gb.LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Log file setup failed: {e}")
    
    return logger

# Initialize logger
logger = setup_logging()

# =============================================================================
# BaslerCameraThread Class
# =============================================================================

class BaslerCameraThread(QThread):
    """Background thread for Basler camera processing - equivalent to RealSenseThread"""
    
    # PyQt signals for thread communication
    frame_signal = pyqtSignal(object)  # color frame
    color_analysis_signal = pyqtSignal(object)  # color analysis results
    error_signal = pyqtSignal(str)  # error messages
    status_signal = pyqtSignal(str)  # status updates
    
    def __init__(self):
        super().__init__()
        self.running = False
        
        # Camera objects
        self.camera = None
        self.converter = None
        self.is_connected = False
        self.is_grabbing = False
        
        # Performance monitoring
        self.frame_count = 0
        self.error_count = 0
        self.last_fps_time = time.time()
        self.fps = 0.0
        
        # Processing settings
        self.sampling_interval = gb.SAMPLING_INTERVAL  # milliseconds
        self.apply_processing = True
        
        # Color analyzer
        self.color_analyzer = None
        
        logger.info("BaslerCameraThread created")
    
    def set_sampling_interval(self, interval_ms: int):
        """Set frame sampling interval in milliseconds"""
        interval_ms = max(gb.MIN_SAMPLING_INTERVAL, min(interval_ms, gb.MAX_SAMPLING_INTERVAL))
        self.sampling_interval = interval_ms
        logger.info(f"Sampling interval set to {self.sampling_interval} ms")
    
    def set_color_analyzer(self, analyzer):
        """Set color analyzer instance"""
        self.color_analyzer = analyzer
    
    def initialize_camera(self) -> bool:
        """Initialize Basler camera"""
        try:
            # Create camera factory
            tl_factory = pylon.TlFactory.GetInstance()
            
            # Check available devices
            devices = tl_factory.EnumerateDevices()
            if len(devices) == 0:
                error_msg = "No Basler cameras connected"
                logger.error(error_msg)
                self.error_signal.emit(error_msg)
                return False
            
            # Display device information
            for dev in devices:
                logger.info(f"Device found: {dev.GetModelName()}")
                logger.info(f"Serial number: {dev.GetSerialNumber()}")
            
            # Connect to first available camera
            self.camera = pylon.InstantCamera(tl_factory.CreateFirstDevice())
            self.camera.Open()
            
            # Setup image converter
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            
            self.is_connected = True
            
            # Apply camera settings
            self._configure_camera()
            
            logger.info("Camera initialization complete")
            self.status_signal.emit("Camera connected successfully")
            return True
            
        except Exception as e:
            error_msg = f"Camera initialization failed: {e}"
            logger.error(error_msg)
            self.error_signal.emit(error_msg)
            return False
    
    def _configure_camera(self):
        """Configure camera settings"""
        try:
            # Get maximum resolution
            max_w = self.camera.Width.GetMax()
            max_h = self.camera.Height.GetMax()
            logger.info(f"Camera max resolution: {max_w} x {max_h}")
            
            # Set safe resolution
            target_w = min(gb.DEFAULT_WIDTH, int(max_w * gb.SAFE_RESOLUTION_RATIO))
            target_h = min(gb.DEFAULT_HEIGHT, int(max_h * gb.SAFE_RESOLUTION_RATIO))
            
            safe_width = (target_w // gb.ALIGNMENT_SIZE) * gb.ALIGNMENT_SIZE
            safe_height = (target_h // gb.ALIGNMENT_SIZE) * gb.ALIGNMENT_SIZE
            
            self.camera.Width.SetValue(safe_width)
            self.camera.Height.SetValue(safe_height)
            
            # Center alignment
            offset_x = ((max_w - safe_width) // 2 // gb.ALIGNMENT_SIZE) * gb.ALIGNMENT_SIZE
            offset_y = ((max_h - safe_height) // 2 // gb.ALIGNMENT_SIZE) * gb.ALIGNMENT_SIZE
            
            if offset_x >= 0:
                self.camera.OffsetX.SetValue(offset_x)
            if offset_y >= 0:
                self.camera.OffsetY.SetValue(offset_y)
            
            # Frame rate settings
            try:
                self.camera.AcquisitionFrameRateEnable.SetValue(True)
                self.camera.AcquisitionFrameRate.SetValue(gb.DEFAULT_FRAME_RATE)
                logger.info(f"Frame rate set to {gb.DEFAULT_FRAME_RATE} fps")
            except:
                logger.warning("Frame rate setting failed")
            
            # Pixel format
            for fmt in gb.PIXEL_FORMATS_PRIORITY:
                try:
                    self.camera.PixelFormat.SetValue(fmt)
                    logger.info(f"Pixel format set to {fmt}")
                    break
                except:
                    continue
                    
            logger.info(f"Camera configured: {safe_width}x{safe_height}")
            
        except Exception as e:
            logger.warning(f"Camera configuration failed: {e}")
    
    def start_grabbing(self) -> bool:
        """Start frame acquisition"""
        try:
            if not self.is_connected:
                return False
                
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.is_grabbing = True
            
            # Reset performance counters
            self.frame_count = 0
            self.error_count = 0
            self.last_fps_time = time.time()
            
            logger.info("Frame grabbing started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start grabbing: {e}")
            return False
    
    def grab_frame(self) -> Optional[np.ndarray]:
        """Grab single frame"""
        try:
            if not self.is_grabbing:
                return None
                
            grab_result = self.camera.RetrieveResult(gb.CAMERA_TIMEOUT, pylon.TimeoutHandling_Return)
            
            if grab_result.GrabSucceeded():
                # Convert image
                image = self.converter.Convert(grab_result)
                img_array = image.GetArray()
                
                # Convert grayscale to BGR if needed
                if len(img_array.shape) == 2:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                
                self.frame_count += 1
                self.error_count = 0
                
                # Calculate FPS
                if gb.SHOW_FPS:
                    current_time = time.time()
                    if current_time - self.last_fps_time > 1.0:
                        self.fps = self.frame_count / (current_time - self.last_fps_time)
                        self.frame_count = 0
                        self.last_fps_time = current_time
                
                grab_result.Release()
                return img_array
            
            else:
                self.error_count += 1
                grab_result.Release()
                return None
                
        except Exception as e:
            self.error_count += 1
            if self.error_count % 10 == 1:  # Log every 10th error
                logger.error(f"Frame grab error: {e}")
            return None
    
    def stop_grabbing(self):
        """Stop frame acquisition"""
        try:
            if self.is_grabbing and self.camera:
                self.camera.StopGrabbing()
                self.is_grabbing = False
                logger.info("Frame grabbing stopped")
        except Exception as e:
            logger.error(f"Stop grabbing failed: {e}")
    
    def disconnect(self):
        """Disconnect camera"""
        try:
            self.stop_grabbing()
            
            if self.camera and self.camera.IsOpen():
                self.camera.Close()
                logger.info("Camera disconnected")
            
            self.camera = None
            self.converter = None
            self.is_connected = False
            
        except Exception as e:
            logger.error(f"Camera disconnect failed: {e}")
    
    def run(self):
        """Thread main execution loop"""
        logger.info("BaslerCameraThread started")
        
        if not self.initialize_camera():
            logger.error("Camera initialization failed")
            self.error_signal.emit("Camera initialization failed")
            return
        
        if not self.start_grabbing():
            logger.error("Failed to start frame grabbing")
            self.error_signal.emit("Failed to start frame grabbing")
            return
        
        self.running = True
        last_sample_time = 0
        
        # Camera warm-up
        self.status_signal.emit("Camera warming up...")
        time.sleep(2)
        self.status_signal.emit("Camera ready")
        
        while self.running:
            current_time = time.time() * 1000  # milliseconds
            time_since_last_sample = current_time - last_sample_time
            
            # Only process frames at specified interval
            if time_since_last_sample >= self.sampling_interval:
                try:
                    # Grab frame
                    color_image = self.grab_frame()
                    
                    if color_image is not None:
                        # Emit frame signal
                        self.frame_signal.emit(color_image)
                        
                        # Perform color analysis if analyzer is set
                        if self.color_analyzer and self.apply_processing:
                            analysis_result = self.color_analyzer.analyze_frame(color_image)
                            if analysis_result:
                                self.color_analysis_signal.emit(analysis_result)
                    
                    last_sample_time = current_time
                    
                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                    self.error_signal.emit(f"Frame processing error: {e}")
            
            # Thread sleep based on sampling interval
            wait_time = max(1, min(10, self.sampling_interval // 10))
            self.msleep(wait_time)
    
    def stop(self):
        """Stop thread"""
        self.running = False
        self.disconnect()
        self.wait()
        logger.info("BaslerCameraThread stopped")

# =============================================================================
# Advanced ColorAnalyzer Class
# =============================================================================

class AdvancedColorAnalyzer:
    """Advanced color analyzer with CIEDE2000 support"""
    
    def __init__(self):
        """Initialize advanced color analyzer"""
        self.reference_lab = np.array(gb.REFERENCE_LAB, dtype=np.float64)
        self.calibration_lab = None
        self.is_calibrated = False
        
        # Sample area settings
        self.sample_size_cm = gb.DEFAULT_SAMPLE_SIZE_CM
        self.pixels_per_cm = 50  # Default, will be calculated dynamically
        
        # Delta E calculation method
        self.de_method = gb.DEFAULT_DE_METHOD
        
        logger.info("AdvancedColorAnalyzer created")
    
    def set_sample_size(self, size_cm: float) -> bool:
        """Set sampling area size in centimeters"""
        if gb.MIN_SAMPLE_SIZE_CM <= size_cm <= gb.MAX_SAMPLE_SIZE_CM:
            self.sample_size_cm = size_cm
            logger.info(f"Sample size set to {size_cm} cm")
            return True
        else:
            logger.warning(f"Invalid sample size: {size_cm} cm")
            return False
    
    def calibrate(self, lab_value: np.ndarray) -> bool:
        """Calibrate reference color"""
        try:
            self.calibration_lab = np.array(lab_value, dtype=np.float64)
            self.is_calibrated = True
            
            logger.info(f"Calibration complete: L={self.calibration_lab[0]:.1f}, "
                       f"a={self.calibration_lab[1]:.1f}, b={self.calibration_lab[2]:.1f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return False
    
    def reset_calibration(self):
        """Reset calibration"""
        self.calibration_lab = None
        self.is_calibrated = False
        logger.info("Calibration reset")
    
    def convert_opencv_lab_to_standard(self, lab_opencv: np.ndarray) -> np.ndarray:
        """Convert OpenCV LAB to standard CIE LAB"""
        l = lab_opencv[0] * 100.0 / 255.0
        a = lab_opencv[1] - 128.0
        b = lab_opencv[2] - 128.0
        return np.array([l, a, b], dtype=np.float64)
    
    def calculate_color_differences(self, lab1: np.ndarray, lab2: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive color differences"""
        try:
            # Basic differences
            dl = lab2[0] - lab1[0]
            da = lab2[1] - lab1[1]
            db = lab2[2] - lab1[2]
            
            # Chroma calculations
            c1 = np.sqrt(lab1[1]**2 + lab1[2]**2)
            c2 = np.sqrt(lab2[1]**2 + lab2[2]**2)
            dc = c2 - c1
            
            # Hue calculations
            h1 = np.arctan2(lab1[2], lab1[1]) if c1 > 0 else 0
            h2 = np.arctan2(lab2[2], lab2[1]) if c2 > 0 else 0
            
            dhue = h2 - h1
            if dhue > np.pi:
                dhue -= 2 * np.pi
            elif dhue < -np.pi:
                dhue += 2 * np.pi
            
            # Hue difference (dh)
            if c1 * c2 == 0:
                dh = 0
            else:
                dh = 2 * np.sqrt(c1 * c2) * np.sin(dhue / 2)
            
            # Delta E calculations
            de_76 = self.calculate_delta_e_76(lab1, lab2)
            de_2000 = self.calculate_delta_e_2000(lab1, lab2) if self.de_method == gb.DE_METHOD_CIE2000 else de_76
            
            return {
                'dl': round(dl, gb.COLOR_DIFF_PRECISION),
                'da': round(da, gb.COLOR_DIFF_PRECISION),
                'db': round(db, gb.COLOR_DIFF_PRECISION),
                'dc': round(dc, gb.COLOR_DIFF_PRECISION),
                'dh': round(dh, gb.COLOR_DIFF_PRECISION),
                'de76': round(de_76, gb.COLOR_DIFF_PRECISION),
                'de2000': round(de_2000, gb.COLOR_DIFF_PRECISION),
                'de': round(de_2000 if self.de_method == gb.DE_METHOD_CIE2000 else de_76, gb.COLOR_DIFF_PRECISION)
            }
            
        except Exception as e:
            logger.error(f"Color difference calculation error: {e}")
            return {
                'dl': 0.0, 'da': 0.0, 'db': 0.0,
                'dc': 0.0, 'dh': 0.0, 'de76': 0.0, 'de2000': 0.0, 'de': 0.0
            }
    
    def calculate_delta_e_76(self, lab1: np.ndarray, lab2: np.ndarray) -> float:
        """Calculate Delta E using CIE76 formula"""
        return np.sqrt((lab2[0] - lab1[0])**2 + 
                       (lab2[1] - lab1[1])**2 + 
                       (lab2[2] - lab1[2])**2)
    
    def calculate_delta_e_2000(self, lab1: np.ndarray, lab2: np.ndarray, 
                              k_L: float = None, k_C: float = None, k_H: float = None) -> float:
        """Calculate Delta E using CIEDE2000 formula"""
        # Use global settings if not specified
        k_L = k_L or gb.CIEDE2000_KL
        k_C = k_C or gb.CIEDE2000_KC
        k_H = k_H or gb.CIEDE2000_KH
        
        try:
            # Unpack Lab values
            L1, a1, b1 = lab1
            L2, a2, b2 = lab2
            
            # Step 1: Calculate C1, C2, C_avg
            C1 = np.sqrt(a1**2 + b1**2)
            C2 = np.sqrt(a2**2 + b2**2)
            C_avg = (C1 + C2) / 2.0
            
            # Step 2: Calculate G
            C_avg_pow7 = C_avg**7
            G = 0.5 * (1 - np.sqrt(C_avg_pow7 / (C_avg_pow7 + 25**7)))
            
            # Step 3: Calculate a'1, a'2
            a_prime1 = (1 + G) * a1
            a_prime2 = (1 + G) * a2
            
            # Step 4: Calculate C'1, C'2
            C_prime1 = np.sqrt(a_prime1**2 + b1**2)
            C_prime2 = np.sqrt(a_prime2**2 + b2**2)
            
            # Step 5: Calculate h'1, h'2
            h_prime1 = 0.0
            if not (a_prime1 == 0 and b1 == 0):
                h_prime1 = np.arctan2(b1, a_prime1)
                if h_prime1 < 0:
                    h_prime1 += 2 * np.pi
                h_prime1 = np.degrees(h_prime1)
            
            h_prime2 = 0.0
            if not (a_prime2 == 0 and b2 == 0):
                h_prime2 = np.arctan2(b2, a_prime2)
                if h_prime2 < 0:
                    h_prime2 += 2 * np.pi
                h_prime2 = np.degrees(h_prime2)
            
            # Step 6: Calculate ΔL', ΔC', ΔH'
            delta_L_prime = L2 - L1
            delta_C_prime = C_prime2 - C_prime1
            
            delta_h_prime = 0.0
            if C_prime1 * C_prime2 != 0:
                delta_h_prime = h_prime2 - h_prime1
                if delta_h_prime > 180:
                    delta_h_prime -= 360
                elif delta_h_prime < -180:
                    delta_h_prime += 360
            
            delta_H_prime = 2 * np.sqrt(C_prime1 * C_prime2) * np.sin(np.radians(delta_h_prime) / 2)
            
            # Step 7: Calculate CIEDE2000 components
            L_prime_avg = (L1 + L2) / 2.0
            C_prime_avg = (C_prime1 + C_prime2) / 2.0
            
            h_prime_avg = h_prime1 + h_prime2
            if C_prime1 * C_prime2 != 0:
                if abs(h_prime1 - h_prime2) > 180:
                    if h_prime1 + h_prime2 < 360:
                        h_prime_avg += 360
                    else:
                        h_prime_avg -= 360
                h_prime_avg /= 2.0
            
            T = 1 - 0.17 * np.cos(np.radians(h_prime_avg - 30)) + \
                0.24 * np.cos(np.radians(2 * h_prime_avg)) + \
                0.32 * np.cos(np.radians(3 * h_prime_avg + 6)) - \
                0.20 * np.cos(np.radians(4 * h_prime_avg - 63))
            
            # Step 8: Calculate parameter weights
            S_L = 1 + (0.015 * (L_prime_avg - 50)**2) / np.sqrt(20 + (L_prime_avg - 50)**2)
            S_C = 1 + 0.045 * C_prime_avg
            S_H = 1 + 0.015 * C_prime_avg * T
            
            # Step 9: Calculate rotation term
            delta_theta = 30 * np.exp(-((h_prime_avg - 275) / 25)**2)
            R_C = 2 * np.sqrt(C_prime_avg**7 / (C_prime_avg**7 + 25**7))
            R_T = -R_C * np.sin(np.radians(2 * delta_theta))
            
            # Step 10: Calculate CIEDE2000 color difference
            delta_E = np.sqrt(
                (delta_L_prime / (k_L * S_L))**2 +
                (delta_C_prime / (k_C * S_C))**2 +
                (delta_H_prime / (k_H * S_H))**2 +
                R_T * (delta_C_prime / (k_C * S_C)) * (delta_H_prime / (k_H * S_H))
            )
            
            return delta_E
            
        except Exception as e:
            logger.error(f"CIEDE2000 calculation error: {e}")
            return self.calculate_delta_e_76(lab1, lab2)  # Fallback to CIE76
    
    def calculate_pixels_per_cm(self, depth_in_meters: float = 0.3) -> float:
        """Calculate pixels per cm based on depth (simplified for Basler)"""
        # Default assumption for Basler camera at typical working distance
        # This should be calibrated for specific setup
        if depth_in_meters <= 0:
            depth_in_meters = 0.3  # 30cm default
        
        # Simplified calculation - should be calibrated for actual setup
        base_pixels_per_cm = 30  # Approximate for acA4024-8gc at 30cm
        scale_factor = 0.3 / depth_in_meters
        
        return max(10, base_pixels_per_cm * scale_factor)
    
    def analyze_frame(self, frame: np.ndarray, depth_meters: float = 0.3) -> Optional[Dict[str, Any]]:
        """Analyze frame for color differences"""
        try:
            if frame is None or frame.size == 0:
                return None
            
            height, width = frame.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            # Calculate dynamic sampling area
            self.pixels_per_cm = self.calculate_pixels_per_cm(depth_meters)
            sample_size_pixels = int(self.sample_size_cm * self.pixels_per_cm)
            
            # Sampling area bounds
            half_size = sample_size_pixels // 2
            x1 = max(0, center_x - half_size)
            y1 = max(0, center_y - half_size)
            x2 = min(width, center_x + half_size)
            y2 = min(height, center_y + half_size)
            
            # Convert BGR to LAB
            lab_image = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            
            # Extract ROI
            roi_bgr = frame[y1:y2, x1:x2]
            roi_lab = lab_image[y1:y2, x1:x2]
            
            # Calculate average values
            avg_b, avg_g, avg_r = cv2.mean(roi_bgr)[:3]
            avg_l_opencv, avg_a_opencv, avg_b_lab_opencv = cv2.mean(roi_lab)[:3]
            
            # Convert to standard CIE LAB
            current_lab_standard = self.convert_opencv_lab_to_standard(
                np.array([avg_l_opencv, avg_a_opencv, avg_b_lab_opencv])
            )
            
            # Calculate color differences
            reference = self.calibration_lab if self.is_calibrated else self.reference_lab
            color_diffs = self.calculate_color_differences(reference, current_lab_standard)
            
            # Package result
            result = {
                'bgr': {'b': avg_b, 'g': avg_g, 'r': avg_r},
                'rgb': {'r': avg_r, 'g': avg_g, 'b': avg_b},
                'lab': {
                    'l': round(current_lab_standard[0], gb.COLOR_DIFF_PRECISION),
                    'a': round(current_lab_standard[1], gb.COLOR_DIFF_PRECISION),
                    'b': round(current_lab_standard[2], gb.COLOR_DIFF_PRECISION)
                },
                'color_diffs': color_diffs,
                'sampling_area': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                'sample_size_cm': self.sample_size_cm,
                'pixels_per_cm': self.pixels_per_cm,
                'calibrated': self.is_calibrated,
                'de_method': self.de_method,
                'timestamp': time.time(),
                'depth_meters': depth_meters
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
            return None

# =============================================================================
# Advanced DataManager Class
# =============================================================================

class AdvancedDataManager:
    """Advanced data manager for history persistence and statistics"""
    
    def __init__(self):
        """Initialize advanced data manager"""
        self.history_data = deque(maxlen=gb.HISTORY_SIZE)
        self.start_time = time.time()
        
        # Auto-save settings
        self.save_counter = 0
        self.last_save_time = time.time()
        
        # Statistics
        self.stats_cache = {}
        self.stats_cache_time = 0
        
        logger.info("AdvancedDataManager created")
        
        # Load existing history
        self.load_history()
    
    def add_data_point(self, analysis_result: Dict[str, Any]) -> bool:
        """Add analysis result to history"""
        try:
            if analysis_result is None:
                return False
            
            # Create data point with relative timestamp
            relative_time = analysis_result['timestamp'] - self.start_time
            
            data_point = {
                'time': relative_time,
                'absolute_time': analysis_result['timestamp'],
                'de': analysis_result['color_diffs']['de'],
                'de76': analysis_result['color_diffs']['de76'],
                'de2000': analysis_result['color_diffs']['de2000'],
                'dl': analysis_result['color_diffs']['dl'],
                'da': analysis_result['color_diffs']['da'],
                'db': analysis_result['color_diffs']['db'],
                'dc': analysis_result['color_diffs']['dc'],
                'dh': analysis_result['color_diffs']['dh'],
                'lab': analysis_result['lab'],
                'rgb': analysis_result['rgb'],
                'calibrated': analysis_result['calibrated'],
                'sample_size_cm': analysis_result.get('sample_size_cm', gb.DEFAULT_SAMPLE_SIZE_CM),
                'de_method': analysis_result.get('de_method', gb.DEFAULT_DE_METHOD)
            }
            
            self.history_data.append(data_point)
            
            # Auto-save check
            self.save_counter += 1
            if self.save_counter >= gb.HISTORY_AUTO_SAVE_INTERVAL:
                self.save_history()
                self.save_counter = 0
            
            # Invalidate statistics cache
            self.stats_cache_time = 0
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add data point: {e}")
            return False
    
    def get_recent_data(self, count: int = None, time_window: float = None) -> List[Dict[str, Any]]:
        """Get recent data points"""
        if not self.history_data:
            return []
        
        if time_window is not None:
            # Filter by time window
            current_time = time.time() - self.start_time
            cutoff_time = current_time - time_window
            filtered_data = [dp for dp in self.history_data if dp['time'] >= cutoff_time]
            return filtered_data
        
        if count is None:
            return list(self.history_data)
        else:
            return list(self.history_data)[-count:]
    
    def get_de_values(self, method: str = 'de') -> Tuple[List[float], List[float]]:
        """Get time and DE value arrays for graphing"""
        times = []
        de_values = []
        
        for data_point in self.history_data:
            times.append(data_point['time'])
            de_values.append(data_point.get(method, data_point['de']))
        
        return times, de_values
    
    def get_statistics(self, refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        current_time = time.time()
        
        # Use cache if recent (within 5 seconds)
        if not refresh and self.stats_cache_time > 0 and (current_time - self.stats_cache_time) < 5:
            return self.stats_cache
        
        try:
            if len(self.history_data) == 0:
                return {}
            
            # Extract values for statistics
            de_values = [dp['de'] for dp in self.history_data]
            de76_values = [dp['de76'] for dp in self.history_data]
            de2000_values = [dp['de2000'] for dp in self.history_data]
            dl_values = [dp['dl'] for dp in self.history_data]
            da_values = [dp['da'] for dp in self.history_data]
            db_values = [dp['db'] for dp in self.history_data]
            
            # Calculate statistics
            stats = {
                'count': len(self.history_data),
                'time_span': self.history_data[-1]['time'] - self.history_data[0]['time'] if len(self.history_data) > 1 else 0,
                
                # DE statistics
                'de_min': min(de_values),
                'de_max': max(de_values),
                'de_mean': np.mean(de_values),
                'de_std': np.std(de_values),
                'de_median': np.median(de_values),
                
                # DE76 statistics
                'de76_mean': np.mean(de76_values),
                'de76_std': np.std(de76_values),
                
                # DE2000 statistics  
                'de2000_mean': np.mean(de2000_values),
                'de2000_std': np.std(de2000_values),
                
                # Component statistics
                'dl_mean': np.mean(dl_values),
                'dl_std': np.std(dl_values),
                'da_mean': np.mean(da_values),
                'da_std': np.std(da_values),
                'db_mean': np.mean(db_values),
                'db_std': np.std(db_values),
                
                # Alert counts
                'warning_count': len([de for de in de_values if abs(de) > gb.WARNING_THRESHOLD_DE]),
                'critical_count': len([de for de in de_values if abs(de) > gb.CRITICAL_THRESHOLD_DE]),
                
                # Recent performance (last 100 points)
                'recent_mean': np.mean(de_values[-100:]) if len(de_values) >= 100 else np.mean(de_values),
                'recent_std': np.std(de_values[-100:]) if len(de_values) >= 100 else np.std(de_values),
            }
            
            # Cache results
            self.stats_cache = stats
            self.stats_cache_time = current_time
            
            return stats
            
        except Exception as e:
            logger.error(f"Statistics calculation failed: {e}")
            return {}
    
    def save_history(self) -> bool:
        """Save history to file"""
        try:
            if len(self.history_data) == 0:
                return True
            
            history_dict = {
                'start_time': self.start_time,
                'save_time': time.time(),
                'data': list(self.history_data),
                'version': gb.VERSION,
                'settings': {
                    'history_size': gb.HISTORY_SIZE,
                    'de_method': gb.DEFAULT_DE_METHOD,
                    'warning_threshold': gb.WARNING_THRESHOLD_DE,
                    'critical_threshold': gb.CRITICAL_THRESHOLD_DE
                }
            }
            
            # Save to numpy file
            np.save(gb.HISTORY_FILE, history_dict)
            
            logger.info(f"History saved: {len(self.history_data)} points")
            self.last_save_time = time.time()
            return True
            
        except Exception as e:
            logger.error(f"History save failed: {e}")
            return False
    
    def load_history(self) -> bool:
        """Load history from file"""
        try:
            if not os.path.exists(gb.HISTORY_FILE):
                logger.info("No history file found")
                return False
            
            history_dict = np.load(gb.HISTORY_FILE, allow_pickle=True).item()
            
            if 'data' in history_dict:
                loaded_data = history_dict['data']
                saved_start_time = history_dict.get('start_time', self.start_time)
                
                # Adjust timestamps to current session
                time_offset = self.start_time - saved_start_time
                
                for data_point in loaded_data:
                    adjusted_point = data_point.copy()
                    adjusted_point['time'] -= time_offset
                    self.history_data.append(adjusted_point)
                
                logger.info(f"History loaded: {len(loaded_data)} points")
                return True
            
        except Exception as e:
            logger.error(f"History load failed: {e}")
            return False
        
        return False
    
    def export_csv(self, filename: str) -> bool:
        """Export data to CSV"""
        try:
            import csv
            
            if len(self.history_data) == 0:
                logger.warning("No data to export")
                return False
            
            with open(filename, 'w', newline='', encoding=gb.CSV_ENCODING) as csvfile:
                fieldnames = [
                    'time', 'absolute_time', 'de', 'de76', 'de2000',
                    'dl', 'da', 'db', 'dc', 'dh',
                    'lab_l', 'lab_a', 'lab_b',
                    'rgb_r', 'rgb_g', 'rgb_b',
                    'calibrated', 'sample_size_cm', 'de_method'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, 
                                       delimiter=gb.CSV_DELIMITER)
                
                if gb.CSV_INCLUDE_HEADERS:
                    writer.writeheader()
                
                for data_point in self.history_data:
                    row = {
                        'time': data_point['time'],
                        'absolute_time': data_point.get('absolute_time', ''),
                        'de': data_point['de'],
                        'de76': data_point['de76'],
                        'de2000': data_point['de2000'],
                        'dl': data_point['dl'],
                        'da': data_point['da'],
                        'db': data_point['db'],
                        'dc': data_point['dc'],
                        'dh': data_point['dh'],
                        'lab_l': data_point['lab']['l'],
                        'lab_a': data_point['lab']['a'],
                        'lab_b': data_point['lab']['b'],
                        'rgb_r': data_point['rgb']['r'],
                        'rgb_g': data_point['rgb']['g'],
                        'rgb_b': data_point['rgb']['b'],
                        'calibrated': data_point['calibrated'],
                        'sample_size_cm': data_point.get('sample_size_cm', ''),
                        'de_method': data_point.get('de_method', '')
                    }
                    writer.writerow(row)
            
            logger.info(f"CSV export completed: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def clear_history(self):
        """Clear all history data"""
        self.history_data.clear()
        self.start_time = time.time()
        self.save_counter = 0
        self.stats_cache = {}
        self.stats_cache_time = 0
        logger.info("History cleared")

# =============================================================================
# Module Initialization
# =============================================================================

logger.info(f"lib_basler_cmd_delta_1v.py loaded successfully (version {gb.VERSION})")