# 2025-08-25
# Basler acA4024-8gc Color Difference Analysis Package

"""
Basler acA4024-8gc 카메라를 이용한 색차값 측정 패키지

이 패키지는 RealSense D435 카메라용 색차값 측정 프로그램을 
Basler acA4024-8gc 카메라용으로 포팅한 것입니다.

주요 모듈:
- glob_basler: 전역 설정
- lib_basler: 핵심 라이브러리 (카메라, 색차분석, 데이터관리)
- gui_basler: PyQt5 기반 GUI
- test_basler_color: 통합 테스트 프로그램

사용 예제:
    # 간단한 사용법
    from sorc import lib_basler as lb
    
    camera = lb.BaslerCamera()
    analyzer = lb.ColorAnalyzer()
    
    if camera.connect() and camera.start_grabbing():
        frame = camera.grab_frame()
        result = analyzer.analyze_frame(frame)
        print(f"DE value: {result['color_diffs']['de']}")
    
    # GUI 실행
    python test_basler_color.py
"""

from . import glob_basler
from . import lib_basler
from . import gui_basler

__version__ = glob_basler.VERSION
__author__ = glob_basler.AUTHOR
__build_date__ = glob_basler.BUILD_DATE

__all__ = [
    'glob_basler',
    'lib_basler', 
    'gui_basler'
]