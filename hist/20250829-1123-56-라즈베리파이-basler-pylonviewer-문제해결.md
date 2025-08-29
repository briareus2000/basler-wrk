# Basler acA-4024 GigE 카메라 PylonViewer 문제 해결 가이드

**작성일**: 2025년 8월 29일  
**환경**: Raspberry Pi 4B (Debian 12 bookworm), Basler acA-4024 GigE Vision 카메라  
**해결 문제**: pylonviewer 실행 오류 및 카메라 인식 불가

## 1. 초기 문제 상황

### 1.1 Qt 플랫폼 플러그인 오류
```bash
moon@rasp4b64i12:/opt/pylon/bin $ pylonviewer
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: vkkhrdisplay, minimalegl, xcb, minimal, wayland-egl, wayland, eglfs, linuxfb, vnc, offscreen.

중지됨
```

### 1.2 카메라 연결 상태
- Basler acA-4024 GigE Vision 카메라
- 라즈베리파이와 이더넷 직접 연결
- 어제까지 정상 작동했으나, Windows PC와 연결 후 다시 라즈베리파이와 연결 시 인식 불가

## 2. 문제 해결 과정

### 2.1 Qt 의존성 문제 해결

#### 2.1.1 누락된 패키지 확인
- `libxcb-cursor0` 패키지가 Debian 12에서 기본 제공되지 않음
- Debian 패키지 저장소에서 직접 다운로드 필요

#### 2.1.2 패키지 수동 설치
```bash
# libxcb-cursor0 다운로드 및 설치
wget http://ftp.us.debian.org/debian/pool/main/x/xcb-util-cursor/libxcb-cursor0_0.1.1-4_arm64.deb
sudo dpkg -i libxcb-cursor0_0.1.1-4_arm64.deb
```

#### 2.1.3 Pylon USB 설정
```bash
# Pylon USB 권한 설정 (GigE에도 필요)
yes | sudo /opt/pylon/share/pylon/setup-usb.sh
```

### 2.2 GigE Vision 네트워크 설정

#### 2.2.1 네트워크 인터페이스 확인
```bash
ip addr show
# eth0: 192.168.3.2/24 (기존)
# wlan0: 192.168.0.12/24
```

#### 2.2.2 Link-Local 대역 추가 (Auto IP 지원)
```bash
# 카메라가 Auto IP(169.254.x.x) 대역에 있을 경우를 대비
sudo ip addr add 169.254.1.1/16 dev eth0
```

#### 2.2.3 네트워크 최적화
```bash
# ARP 캐시 초기화
sudo ip neigh flush all

# GigE Vision 포트 방화벽 열기
sudo iptables -I INPUT -p udp --sport 3956 -j ACCEPT
sudo iptables -I OUTPUT -p udp --dport 3956 -j ACCEPT

# 네트워크 버퍼 크기 증가
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.rmem_default=134217728
```

### 2.3 카메라 인식 문제 해결

#### 2.3.1 문제 상황
- pylonviewer는 정상 실행되나 카메라가 "Auto IP(LLA)" 상태로 표시
- "The device is unreachable" 오류 발생
- Windows에서 사용 후 IP 설정이 변경된 것으로 추정

#### 2.3.2 최종 해결 방법
**PylonGigEConfigurator 사용**:
1. `/opt/pylon/bin/PylonGigEConfigurator` 실행
2. **Configure** 버튼 클릭
3. 네트워크 설정이 정상으로 표시되고 카메라 프레임 표시됨

## 3. 해결 방법 요약

### 3.1 Qt 플랫폼 플러그인 오류
```bash
# libxcb-cursor0 패키지 수동 설치
wget http://ftp.us.debian.org/debian/pool/main/x/xcb-util-cursor/libxcb-cursor0_0.1.1-4_arm64.deb
sudo dpkg -i libxcb-cursor0_0.1.1-4_arm64.deb

# Pylon 권한 설정
yes | sudo /opt/pylon/share/pylon/setup-usb.sh
```

### 3.2 GigE Vision 카메라 인식 불가
```bash
# Link-Local 대역 IP 추가 (Auto IP 지원)
sudo ip addr add 169.254.1.1/16 dev eth0

# 네트워크 최적화
sudo ip neigh flush all
sudo iptables -I INPUT -p udp --sport 3956 -j ACCEPT
sudo iptables -I OUTPUT -p udp --dport 3956 -j ACCEPT
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.rmem_default=134217728

# 최종 해결: PylonGigEConfigurator 실행 후 Configure 버튼 클릭
/opt/pylon/bin/PylonGigEConfigurator
```

## 4. 문제 발생 원인 분석

### 4.1 Qt 플랫폼 플러그인 오류
- Debian 12 (bookworm)에서 `libxcb-cursor0` 패키지가 기본 제공되지 않음
- Pylon 설치 시 해당 의존성이 자동으로 해결되지 않음

### 4.2 GigE Vision 카메라 인식 문제
- Windows PC에서 사용 시 카메라의 네트워크 설정이 변경됨
- GigE Vision 필터 드라이버나 네트워크 인터페이스 설정이 초기화됨
- **PylonGigEConfigurator의 Configure 버튼**이 다음 작업을 수행:
  - GigE Vision 필터 드라이버 활성화
  - 네트워크 인터페이스 최적화 설정 적용
  - 패킷 수신 필터 재설정

## 5. 예방 및 유지보수 방법

### 5.1 정기 점검 사항
```bash
# 네트워크 인터페이스 상태 확인
ip addr show eth0

# GigE Vision 드라이버 상태 확인
/opt/pylon/bin/PylonGigEConfigurator
```

### 5.2 문제 재발 시 대처 방법
1. **카메라 하드웨어 재시작**: 전원 케이블 분리 후 10초 대기, 재연결
2. **PylonGigEConfigurator 실행**: Configure 버튼 클릭
3. **pylonviewer에서 강제 IP 할당**: 
   - unreachable 카메라 우클릭
   - "Assign IP Configuration" 선택
   - Static IP 설정 (예: 192.168.3.100/24)

### 5.3 시스템 재시작 시 설정 유지
```bash
# /etc/rc.local 또는 systemd 서비스로 네트워크 설정 자동화
echo "ip addr add 169.254.1.1/16 dev eth0" | sudo tee -a /etc/rc.local
echo "sysctl -w net.core.rmem_max=134217728" | sudo tee -a /etc/rc.local
echo "sysctl -w net.core.rmem_default=134217728" | sudo tee -a /etc/rc.local
```

## 6. 주요 학습사항

1. **Debian 패키지 의존성**: 최신 Debian에서 일부 Qt 의존성이 기본 제공되지 않을 수 있음
2. **GigE Vision 카메라 특성**: Windows/Linux 간 전환 시 네트워크 설정이 변경될 수 있음
3. **PylonGigEConfigurator의 중요성**: 단순한 Configure 버튼 클릭으로 복잡한 네트워크 문제 해결 가능
4. **Auto IP 지원**: Link-Local 대역(169.254.x.x) 설정으로 카메라 호환성 향상

## 7. 참고 명령어

### 7.1 진단 명령어
```bash
# 네트워크 인터페이스 확인
ip addr show

# ARP 테이블 확인
arp -a

# Pylon 도구 목록
ls /opt/pylon/bin/

# 프로세스 확인
pgrep -fl pylon
```

### 7.2 설정 명령어
```bash
# pylonviewer 실행
/opt/pylon/bin/pylonviewer

# PylonGigEConfigurator 실행
/opt/pylon/bin/PylonGigEConfigurator

# IP Configurator 실행
/opt/pylon/bin/ipconfigurator
```

---
**작성자**: Claude Code AI Assistant  
**문서 버전**: 1.0  
**최종 수정일**: 2025-08-29