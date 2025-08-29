#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025-08-25
Basler acA4024-8gc 카메라 색차값 측정 통합 테스트 프로그램

이 프로그램은 RealSense D435 색차값 프로그램의 기능을 
Basler acA4024-8gc 카메라로 구현한 것입니다.

실행 방법:
    python test_basler_color.py

필수 라이브러리:
    pip install pypylon opencv-python numpy PyQt5 pyqtgraph PyOpenGL

키보드 단축키:
    C: 캘리브레이션
    V: 그래프 뷰 모드 토글
    S: 데이터 저장
    L: 데이터 로드
    R: 히스토리 리셋
    SPACE: 정보 표시 토글
    ESC: 종료
"""

import sys
import os
import time
import traceback
from typing import Optional

# 경로 설정 (같은 디렉토리의 모듈들을 import하기 위함)
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    import numpy as np
    import cv2
    from pypylon import pylon
    from PyQt5.QtWidgets import QApplication, QMessageBox
    import pyqtgraph as pg
    
    print("✅ 필수 라이브러리 import 성공")
    
except ImportError as e:
    print(f"❌ 필수 라이브러리 import 실패: {e}")
    print("\n필수 라이브러리 설치:")
    print("pip install pypylon opencv-python numpy PyQt5 pyqtgraph PyOpenGL")
    sys.exit(1)

# 로컬 모듈 import
try:
    import glob_basler as gb
    import lib_basler as lb
    import gui_basler as gui
    
    print("✅ 로컬 모듈 import 성공")
    
except ImportError as e:
    print(f"❌ 로컬 모듈 import 실패: {e}")
    print(f"현재 디렉토리: {os.getcwd()}")
    print(f"스크립트 디렉토리: {script_dir}")
    print("\n파일 구조를 확인하세요:")
    print("- glob_basler.py")
    print("- lib_basler.py") 
    print("- gui_basler.py")
    sys.exit(1)

# =============================================================================
# 시스템 검증 함수들
# =============================================================================

def check_camera_availability() -> bool:
    """카메라 연결 상태 확인"""
    print("\n🔍 카메라 연결 상태 확인...")
    
    try:
        camera = lb.BaslerCamera()
        cameras = camera.find_cameras()
        
        if len(cameras) == 0:
            print("❌ 연결된 Basler 카메라가 없습니다.")
            print("\n확인사항:")
            print("  - 카메라 전원 확인")
            print("  - USB/이더넷 케이블 연결 확인")
            print("  - 카메라 드라이버 설치 확인")
            return False
        
        print(f"✅ 발견된 카메라: {len(cameras)}개")
        for camera_info in cameras:
            print(f"  - {camera_info['model']} (S/N: {camera_info['serial']})")
        
        return True
        
    except Exception as e:
        print(f"❌ 카메라 검색 실패: {e}")
        return False

def test_camera_connection() -> bool:
    """카메라 연결 및 기본 기능 테스트"""
    print("\n🔍 카메라 연결 테스트...")
    
    try:
        camera = lb.BaslerCamera()
        
        # 카메라 연결
        if not camera.connect():
            print("❌ 카메라 연결 실패")
            return False
        
        print("✅ 카메라 연결 성공")
        
        # 프레임 획득 시작
        if not camera.start_grabbing():
            print("❌ 프레임 획득 시작 실패")
            camera.disconnect()
            return False
        
        print("✅ 프레임 획득 시작 성공")
        
        # 몇 프레임 테스트
        success_count = 0
        for i in range(10):
            frame = camera.grab_frame(timeout_ms=1000)
            if frame is not None:
                success_count += 1
            time.sleep(0.1)
        
        print(f"✅ 프레임 테스트: {success_count}/10 성공")
        
        # 카메라 정보 출력
        info = camera.get_camera_info()
        print(f"  - 해상도: {info['width']} x {info['height']}")
        print(f"  - 프레임율: {info['frame_rate']} fps")
        print(f"  - 픽셀 포맷: {info['pixel_format']}")
        
        # 정리
        camera.disconnect()
        print("✅ 카메라 연결 해제 완료")
        
        return success_count >= 5
        
    except Exception as e:
        print(f"❌ 카메라 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_color_analysis() -> bool:
    """색차값 분석 기능 테스트"""
    print("\n🔍 색차값 분석 기능 테스트...")
    
    try:
        # 테스트용 이미지 생성 (백색)
        test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # ColorAnalyzer 초기화
        analyzer = lb.ColorAnalyzer()
        
        # 분석 수행
        result = analyzer.analyze_frame(test_image)
        
        if result is None:
            print("❌ 색차값 분석 실패")
            return False
        
        print("✅ 색차값 분석 성공")
        print(f"  - BGR: R={result['bgr']['r']:.1f}, G={result['bgr']['g']:.1f}, B={result['bgr']['b']:.1f}")
        print(f"  - LAB: L={result['lab']['l']:.1f}, a={result['lab']['a']:.1f}, b={result['lab']['b']:.1f}")
        print(f"  - 색차값: DE={result['color_diffs']['de']:.1f}")
        
        # 캘리브레이션 테스트
        lab_values = np.array([result['lab']['l'], result['lab']['a'], result['lab']['b']])
        if analyzer.calibrate(lab_values):
            print("✅ 캘리브레이션 기능 정상")
        else:
            print("❌ 캘리브레이션 기능 오류")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 색차값 분석 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_data_management() -> bool:
    """데이터 관리 기능 테스트"""
    print("\n🔍 데이터 관리 기능 테스트...")
    
    try:
        data_manager = lb.DataManager()
        
        # 테스트 데이터 생성
        test_analysis = {
            'timestamp': time.time(),
            'color_diffs': {
                'de': 1.5, 'dl': 0.5, 'da': 0.3, 
                'db': 0.2, 'dc': 0.1, 'dh': 0.1
            },
            'lab': {'l': 95.0, 'a': -0.5, 'b': 2.0},
            'calibrated': False
        }
        
        # 데이터 추가
        if not data_manager.add_data_point(test_analysis):
            print("❌ 데이터 포인트 추가 실패")
            return False
        
        print("✅ 데이터 포인트 추가 성공")
        
        # 데이터 검색
        recent_data = data_manager.get_recent_data(count=1)
        if len(recent_data) != 1:
            print("❌ 데이터 검색 실패")
            return False
        
        print("✅ 데이터 검색 성공")
        
        # 통계 계산
        stats = data_manager.get_statistics()
        if not stats or stats['count'] != 1:
            print("❌ 통계 계산 실패")
            return False
        
        print("✅ 통계 계산 성공")
        print(f"  - 데이터 개수: {stats['count']}")
        print(f"  - DE 평균: {stats['de_mean']:.2f}")
        
        # 저장/로드 테스트
        if not data_manager.save_history():
            print("❌ 데이터 저장 실패")
            return False
        
        print("✅ 데이터 저장 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 관리 테스트 실패: {e}")
        traceback.print_exc()
        return False

def run_simple_test() -> bool:
    """간단한 콘솔 테스트 실행"""
    print("\n🚀 간단한 콘솔 테스트 시작...")
    
    try:
        # 카메라 초기화
        camera = lb.BaslerCamera()
        analyzer = lb.ColorAnalyzer()
        
        if not camera.connect():
            print("❌ 카메라 연결 실패")
            return False
        
        if not camera.start_grabbing():
            print("❌ 프레임 획득 시작 실패")
            camera.disconnect()
            return False
        
        print("✅ 카메라 초기화 완료")
        print("\n색차값 측정 테스트 (10초간)...")
        print("Ctrl+C로 중단 가능")
        
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 10:
            try:
                # 프레임 획득
                frame = camera.grab_frame()
                if frame is None:
                    continue
                
                frame_count += 1
                
                # 색차값 분석 (1초마다)
                if frame_count % 10 == 0:
                    result = analyzer.analyze_frame(frame)
                    if result:
                        de_value = result['color_diffs']['de']
                        lab = result['lab']
                        print(f"Frame {frame_count}: DE={de_value:.1f}, "
                             f"LAB=({lab['l']:.1f}, {lab['a']:.1f}, {lab['b']:.1f})")
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n사용자 중단 요청")
                break
            except Exception as e:
                print(f"처리 오류: {e}")
                continue
        
        # 정리
        camera.disconnect()
        print(f"\n✅ 테스트 완료: {frame_count}개 프레임 처리")
        
        return True
        
    except Exception as e:
        print(f"❌ 간단 테스트 실패: {e}")
        traceback.print_exc()
        return False

# =============================================================================
# GUI 테스트
# =============================================================================

def run_gui_test():
    """GUI 애플리케이션 테스트 실행"""
    print("\n🚀 GUI 애플리케이션 시작...")
    
    try:
        app = QApplication(sys.argv)
        
        # PyQt5 그래프 설정
        pg.setConfigOptions(antialias=True, useOpenGL=True)
        
        # 메인 윈도우 생성
        window = gui.MainWindow()
        window.show()
        
        print("✅ GUI 애플리케이션 시작됨")
        print("\n사용법:")
        print("  C: 캘리브레이션")
        print("  V: 그래프 뷰 토글")
        print("  S: 데이터 저장")
        print("  L: 데이터 로드")
        print("  R: 히스토리 리셋")
        print("  SPACE: 정보 표시 토글")
        print("  ESC: 종료")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ GUI 실행 실패: {e}")
        traceback.print_exc()
        
        # 에러 다이얼로그 표시 시도
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "Error", 
                               f"GUI 실행 실패:\n{str(e)}\n\n"
                               f"필수 라이브러리가 설치되어 있는지 확인하세요:\n"
                               f"pip install pypylon opencv-python numpy PyQt5 pyqtgraph PyOpenGL")
        except:
            pass
        
        sys.exit(1)

# =============================================================================
# 메인 함수
# =============================================================================

def print_header():
    """프로그램 헤더 출력"""
    print("=" * 70)
    print("🎯 Basler acA4024-8gc Color Difference Analysis Test")
    print("=" * 70)
    print(f"버전: {gb.VERSION}")
    print(f"빌드 날짜: {gb.BUILD_DATE}")
    print(f"작성자: {gb.AUTHOR}")
    print("=" * 70)

def print_system_info():
    """시스템 정보 출력"""
    print("\n📋 시스템 정보:")
    print(f"  - Python: {sys.version}")
    print(f"  - 운영체제: {os.name}")
    print(f"  - 현재 디렉토리: {os.getcwd()}")
    print(f"  - 스크립트 경로: {script_dir}")

def run_system_checks() -> bool:
    """시스템 검증 수행"""
    print("\n🔧 시스템 검증 중...")
    
    checks = [
        ("카메라 가용성 확인", check_camera_availability),
        ("카메라 연결 테스트", test_camera_connection),
        ("색차값 분석 테스트", test_color_analysis),
        ("데이터 관리 테스트", test_data_management)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"⚠️ {name} 실패")
        except Exception as e:
            print(f"❌ {name} 오류: {e}")
    
    print(f"\n📊 검증 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("✅ 모든 시스템 검증 통과!")
        return True
    elif passed >= total * 0.5:
        print("⚠️ 부분적 통과 - 일부 기능에 문제가 있을 수 있습니다.")
        return True
    else:
        print("❌ 시스템 검증 실패 - 주요 문제가 있습니다.")
        return False

def main():
    """메인 함수"""
    print_header()
    print_system_info()
    
    # 인수 처리
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "gui"  # 기본값
    
    if mode == "check":
        # 시스템 검증만 수행
        if run_system_checks():
            print("\n✅ 시스템 검증 완료")
            sys.exit(0)
        else:
            print("\n❌ 시스템 검증 실패")
            sys.exit(1)
            
    elif mode == "console":
        # 콘솔 모드 실행
        if run_system_checks():
            if run_simple_test():
                print("\n✅ 콘솔 테스트 완료")
                sys.exit(0)
            else:
                print("\n❌ 콘솔 테스트 실패")
                sys.exit(1)
        else:
            print("\n❌ 시스템 검증 실패로 인해 테스트 중단")
            sys.exit(1)
            
    elif mode == "gui":
        # GUI 모드 실행 (기본)
        if not run_system_checks():
            response = input("\n⚠️ 시스템 검증에 문제가 있습니다. 계속 진행하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("사용자 취소")
                sys.exit(1)
        
        run_gui_test()
        
    else:
        print(f"\n❌ 알 수 없는 모드: {mode}")
        print("\n사용법:")
        print("  python test_basler_color.py [mode]")
        print("    mode:")
        print("      gui     - GUI 모드 (기본값)")
        print("      console - 콘솔 테스트 모드")
        print("      check   - 시스템 검증만 수행")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n사용자 중단 (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        traceback.print_exc()
        sys.exit(1)