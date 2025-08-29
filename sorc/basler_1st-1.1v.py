"""
Basler acA4024-8gc 카메라 Python 간단 예제
필수 설치: pip install pypylon opencv-python numpy
"""

from pypylon import pylon
import cv2
import numpy as np

def main():
    """Basler 카메라 기본 사용 예제"""
    
    # 1. 카메라 검색 및 연결
    print("카메라 검색 중...")
    
    # 연결된 모든 카메라 찾기
    tl_factory = pylon.TlFactory.GetInstance()
    devices = tl_factory.EnumerateDevices()
    
    if len(devices) == 0:
        print("연결된 카메라가 없습니다.")
        return
    
    # 첫 번째 사용 가능한 카메라 선택
    print(f"발견된 카메라 수: {len(devices)}")
    for i, device in enumerate(devices):
        print(f"  {i}: {device.GetModelName()} (S/N: {device.GetSerialNumber()})")
    
    # 카메라 인스턴스 생성
    camera = pylon.InstantCamera(tl_factory.CreateFirstDevice())
    
    try:
        # 2. 카메라 열기
        camera.Open()
        print(f"카메라 연결됨: {camera.GetDeviceInfo().GetModelName()}")
        
        # 3. 기본 설정 (해상도 및 프레임율 최적화)
        # 안전한 설정을 위해 try-except 사용
        try:
            # 해상도 설정 (카메라 최대 해상도 확인 후 설정)
            max_width = camera.Width.GetMax()
            max_height = camera.Height.GetMax()
            print(f"카메라 최대 해상도: {max_width} x {max_height}")
            
            # 적절한 해상도 설정 (최대 해상도의 40% 또는 1600x1200 중 작은 값)
            target_width = min(1600, int(max_width * 0.4))
            target_height = min(1200, int(max_height * 0.4))
            
            # 해상도를 16의 배수로 맞춤 (일부 카메라에서 요구)
            target_width = (target_width // 16) * 16
            target_height = (target_height // 16) * 16
            
            camera.Width.SetValue(target_width)
            camera.Height.SetValue(target_height)
            
            # 중앙 정렬 시도 (속성이 있는 경우에만)
            try:
                if hasattr(camera, 'CenterX'):
                    camera.CenterX.SetValue(True)
                if hasattr(camera, 'CenterY'):
                    camera.CenterY.SetValue(True)
            except:
                # 중앙 정렬이 지원되지 않는 경우 오프셋으로 수동 중앙 정렬
                offset_x = (max_width - target_width) // 2
                offset_y = (max_height - target_height) // 2
                
                # 오프셋을 16의 배수로 맞춤
                offset_x = (offset_x // 16) * 16
                offset_y = (offset_y // 16) * 16
                
                try:
                    camera.OffsetX.SetValue(offset_x)
                    camera.OffsetY.SetValue(offset_y)
                    print(f"수동 중앙 정렬: Offset({offset_x}, {offset_y})")
                except:
                    pass
            
        except Exception as e:
            print(f"해상도 설정 중 오류 (기본값 사용): {e}")
        
        try:
            # 프레임율 설정 시도
            try:
                camera.AcquisitionFrameRateEnable.SetValue(True)
                camera.AcquisitionFrameRate.SetValue(20.0)
                print("프레임율 설정: 20 fps")
            except:
                print("프레임율 설정 실패 - 기본값 사용")
        except Exception as e:
            print(f"프레임율 설정 중 오류: {e}")
        
        try:
            # 픽셀 포맷 설정 - 여러 포맷 시도
            pixel_formats = ["Mono8", "BayerRG8", "BayerGB8", "BayerBG8", "BayerGR8", "RGB8"]
            current_format = None
            
            for fmt in pixel_formats:
                try:
                    camera.PixelFormat.SetValue(fmt)
                    current_format = fmt
                    print(f"픽셀 포맷 설정: {fmt}")
                    break
                except:
                    continue
                    
            if not current_format:
                print("기본 픽셀 포맷 사용")
                
        except Exception as e:
            print(f"픽셀 포맷 설정 중 오류: {e}")
        
        print(f"해상도: {camera.Width.GetValue()} x {camera.Height.GetValue()}")
        
        # 현재 픽셀 포맷 확인
        try:
            current_pixel_format = camera.PixelFormat.GetValue()
            print(f"픽셀 포맷: {current_pixel_format}")
        except:
            current_pixel_format = "Unknown"
            print("픽셀 포맷: 알 수 없음")
        
        # 현재 프레임율 확인
        try:
            if hasattr(camera, 'AcquisitionFrameRate'):
                current_fps = camera.AcquisitionFrameRate.GetValue()
                print(f"프레임율: {current_fps:.1f} fps")
        except:
            print("프레임율: 기본값")
        
        # 4. 영상 획득 시작
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        
        # 이미지 변환기 설정 (픽셀 포맷에 따라 동적 설정)
        converter = pylon.ImageFormatConverter()
        
        # 안전한 변환 포맷 설정
        try:
            # 현재 픽셀 포맷 확인
            current_pixel_format = camera.PixelFormat.GetValue()
            print(f"이미지 변환 설정 - 입력 포맷: {current_pixel_format}")
            
            # 모든 포맷을 BGR8로 통일 변환
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            
        except Exception as e:
            print(f"이미지 변환기 설정 오류: {e}")
            # 기본 설정 사용
            converter = pylon.ImageFormatConverter()
        
        print("영상 획득 시작 (ESC 키로 종료)")
        
        # 5. 실시간 영상 표시
        frame_count = 0
        while camera.IsGrabbing():
            try:
                grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                
                if grab_result.GrabSucceeded():
                    # 이미지 변환
                    image = converter.Convert(grab_result)
                    img = image.GetArray()
                    
                    # Mono 이미지인 경우 컬러로 변환
                    if len(img.shape) == 2:  # Grayscale
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    
                    # 화면 크기 조정 (너무 큰 경우)
                    height, width = img.shape[:2]
                    if width > 1280 or height > 720:
                        scale = min(1280/width, 720/height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        img = cv2.resize(img, (new_width, new_height))
                    
                    # 프레임 정보 추가
                    frame_count += 1
                    cv2.putText(img, f"Frame: {frame_count}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # OpenCV로 표시
                    cv2.imshow('Basler Camera', img)
                    
                    # 프레임 정보 출력 (100프레임마다)
                    if frame_count % 100 == 0:
                        print(f"Frame: {frame_count}")
                    
                grab_result.Release()
                
            except Exception as e:
                print(f"프레임 처리 중 오류: {e}")
                break
                
            # ESC 키로 종료
            if cv2.waitKey(1) & 0xFF == 27:  # ESC 키
                break
                
    except Exception as e:
        print(f"오류 발생: {e}")
        
    finally:
        # 6. 정리 작업
        camera.StopGrabbing()
        camera.Close()
        cv2.destroyAllWindows()
        print("카메라 연결 해제됨")

if __name__ == "__main__":
    main()
    