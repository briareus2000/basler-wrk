"""
Basler acA4024-8gc 카메라 Python 간단 예제 (오류 수정판)
필수 설치: pip install pypylon opencv-python numpy

이 버전은 최대한 안전하게 작성되어 다양한 오류 상황에서도 동작합니다.
"""

from pypylon import pylon
import cv2
import numpy as np
import sys

def safe_camera_setup(camera):
    """안전한 카메라 설정 함수"""
    settings_applied = []
    
    try:
        # 1. 해상도 설정 시도
        max_w = camera.Width.GetMax()
        max_h = camera.Height.GetMax()
        print(f"카메라 최대 해상도: {max_w} x {max_h}")
        
        # 안전한 해상도 계산 (16의 배수로 맞춤)
        safe_width = min(1600, (max_w // 3 // 16) * 16)
        safe_height = min(1200, (max_h // 3 // 16) * 16)
        
        camera.Width.SetValue(safe_width)
        camera.Height.SetValue(safe_height)
        settings_applied.append(f"해상도: {safe_width} x {safe_height}")
        
        # 2. 오프셋 설정 (중앙 정렬)
        offset_x = ((max_w - safe_width) // 2 // 16) * 16
        offset_y = ((max_h - safe_height) // 2 // 16) * 16
        
        if offset_x >= 0:
            camera.OffsetX.SetValue(offset_x)
        if offset_y >= 0:    
            camera.OffsetY.SetValue(offset_y)
        settings_applied.append(f"오프셋: ({offset_x}, {offset_y})")
        
    except Exception as e:
        print(f"해상도 설정 실패: {e}")
    
    try:
        # 3. 프레임율 설정 시도  
        camera.AcquisitionFrameRateEnable.SetValue(True)
        camera.AcquisitionFrameRate.SetValue(15.0)  # 보수적인 15fps
        settings_applied.append("프레임율: 15 fps")
    except Exception as e:
        print(f"프레임율 설정 실패: {e}")
    
    try:
        # 4. 픽셀 포맷 설정 시도 (여러 포맷 순차 시도)
        formats_to_try = ["Mono8", "BayerRG8", "BayerGB8", "RGB8Packed"]
        for fmt in formats_to_try:
            try:
                camera.PixelFormat.SetValue(fmt)
                settings_applied.append(f"픽셀 포맷: {fmt}")
                break
            except:
                continue
    except Exception as e:
        print(f"픽셀 포맷 설정 실패: {e}")
    
    # 설정 완료 메시지
    print("적용된 설정:")
    for setting in settings_applied:
        print(f"  - {setting}")
    
    return len(settings_applied) > 0

def main():
    """메인 함수"""
    camera = None
    
    try:
        print("=" * 50)
        print("Basler 카메라 Python 예제 (안정화 버전)")
        print("=" * 50)
        
        # 1. 카메라 검색
        print("\n1. 카메라 검색 중...")
        tl_factory = pylon.TlFactory.GetInstance()
        devices = tl_factory.EnumerateDevices()
        
        if len(devices) == 0:
            print("❌ 연결된 카메라가 없습니다.")
            print("\n확인사항:")
            print("  - 카메라 전원 확인")
            print("  - USB/이더넷 케이블 연결 확인")
            print("  - 드라이버 설치 확인")
            return False
        
        # 발견된 카메라 정보 출력
        print(f"✅ 발견된 카메라: {len(devices)}개")
        for i, device in enumerate(devices):
            try:
                model = device.GetModelName()
                serial = device.GetSerialNumber()
                print(f"   [{i}] {model} (S/N: {serial})")
            except:
                print(f"   [{i}] 카메라 (정보 읽기 실패)")
        
        # 2. 첫 번째 카메라 연결
        print(f"\n2. 첫 번째 카메라 연결 중...")
        camera = pylon.InstantCamera(tl_factory.CreateFirstDevice())
        camera.Open()
        
        # 카메라 정보 출력
        try:
            info = camera.GetDeviceInfo()
            print(f"✅ 연결 성공: {info.GetModelName()}")
            print(f"   시리얼: {info.GetSerialNumber()}")
        except:
            print("✅ 카메라 연결 성공 (정보 읽기 실패)")
        
        # 3. 카메라 설정
        print(f"\n3. 카메라 설정 중...")
        if not safe_camera_setup(camera):
            print("⚠️ 설정 적용에 실패했지만 기본 설정으로 계속 진행합니다.")
        
        # 4. 영상 획득 시작
        print(f"\n4. 영상 획득 시작...")
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        
        # 이미지 변환기 설정
        converter = pylon.ImageFormatConverter()
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        
        print("✅ 영상 표시 시작")
        print("\n조작법:")
        print("  - ESC: 종료")
        print("  - SPACE: 현재 프레임 정보 출력")
        
        # 5. 메인 루프
        frame_count = 0
        error_count = 0
        
        while camera.IsGrabbing():
            try:
                # 프레임 획득 (타임아웃 1초)
                grab_result = camera.RetrieveResult(1000, pylon.TimeoutHandling_Return)
                
                if grab_result.GrabSucceeded():
                    # 이미지 변환
                    image = converter.Convert(grab_result)
                    img = image.GetArray()
                    
                    frame_count += 1
                    error_count = 0  # 성공 시 에러 카운트 리셋
                    
                    # 이미지가 grayscale인 경우 BGR로 변환
                    if len(img.shape) == 2:
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    
                    # 화면 크기 조정 (화면에 맞게)
                    h, w = img.shape[:2]
                    if w > 1200 or h > 800:
                        scale = min(1200/w, 800/h)
                        new_w, new_h = int(w * scale), int(h * scale)
                        img = cv2.resize(img, (new_w, new_h))
                    
                    # 상태 정보 표시
                    cv2.putText(img, f"Frame: {frame_count}", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(img, "ESC: Exit, SPACE: Info", (10, img.shape[0]-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # 화면 출력
                    cv2.imshow('Basler Camera Live View', img)
                    
                else:
                    error_count += 1
                    if error_count % 10 == 1:  # 10번에 한 번만 출력
                        print(f"⚠️ 프레임 획득 실패 (연속 {error_count}회)")
                
                grab_result.Release()
                
            except Exception as e:
                error_count += 1
                if error_count % 20 == 1:  # 20번에 한 번만 출력  
                    print(f"❌ 프레임 처리 오류: {e}")
                if error_count > 100:  # 너무 많은 연속 오류 시 종료
                    print("❌ 너무 많은 오류로 인해 프로그램을 종료합니다.")
                    break
            
            # 키 입력 처리
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("\n사용자 종료 요청")
                break
            elif key == 32:  # SPACE
                try:
                    w = camera.Width.GetValue()
                    h = camera.Height.GetValue()
                    fmt = camera.PixelFormat.GetValue()
                    print(f"\n현재 상태: {w}x{h}, {fmt}, Frame: {frame_count}")
                except:
                    print(f"\n현재 Frame: {frame_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 심각한 오류 발생: {e}")
        return False
        
    finally:
        # 정리 작업
        print(f"\n5. 정리 중...")
        try:
            if camera and camera.IsOpen():
                camera.StopGrabbing()
                camera.Close()
                print("✅ 카메라 연결 해제 완료")
        except Exception as e:
            print(f"⚠️ 카메라 해제 중 오류: {e}")
        
        cv2.destroyAllWindows()
        print("✅ 프로그램 종료")

if __name__ == "__main__":
    print("Basler 카메라 제어 프로그램을 시작합니다...")
    

    # 프로그램 실행
    success = main()
    
    if success:
        print("\n프로그램이 정상적으로 완료되었습니다.")
    else:
        print("\n프로그램 실행 중 문제가 발생했습니다.")
        print("문제 해결 방법:")
        print("1. 카메라 연결 상태 확인")
        print("2. Basler Pylon Viewer로 카메라 동작 확인")
        print("3. 드라이버 재설치")

