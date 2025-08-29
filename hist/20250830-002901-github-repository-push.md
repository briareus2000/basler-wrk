# GitHub 저장소 생성 및 푸시 과정

## 날짜: 2025-08-30

## 요청사항
현재 폴더의 내용들을 basler-wrk 저장소를 새로 만들어서 github.com/briareus2000/basler-wrk.git로 commit하는 과정 설명 및 실행

## 작업 과정

### 1. 초기 상태 확인
```bash
$ ls -la
합계 112
drwxr-xr-x  9 moon moon  4096  8월 29일  22:41 .
drwx------ 47 moon moon 73728  8월 29일  23:02 ..
drwxr-xr-x  2 moon moon  4096  8월 29일  12:19 .claude
drwxr-xr-x  8 moon moon  4096  8월 29일  23:00 .git
-rw-r--r--  1 moon moon    13  8월 29일  22:41 README.md
drwxr-xr-x  2 moon moon  4096  8월 27일  23:21 config
drwxr-xr-x  2 moon moon  4096  8월 28일  15:56 data
drwxr-xr-x  2 moon moon  4096  8월 29일  22:32 hist
drwxr-xr-x  2 moon moon  4096  8월 29일  22:36 imag
drwxr-xr-x  2 moon moon  4096  8월 29일  22:32 sorc
```

### 2. Git Remote 확인
```bash
$ git remote -v
origin	https://github.com/briareus2000/basler-wrk.git (fetch)
origin	https://github.com/briareus2000/basler-wrk.git (push)
```

### 3. Git 상태 확인
```bash
$ git status
현재 브랜치 main
커밋할 사항 없음, 작업 폴더 깨끗함
```

### 4. 기존 커밋 확인
```bash
$ git log --oneline -5
fe71230 init-commtit
775f05b  get-first
```

### 5. GitHub 인증 설정

#### 첫 번째 시도 (실패)
```bash
$ git push -u origin main
fatal: could not read Username for 'https://github.com': 그런 장치 혹은 주소가 없음
```

#### Personal Access Token (PAT) 생성 안내
1. GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 'repo' 권한 체크
4. Token 생성 후 복사

#### 첫 번째 PAT 시도 (권한 오류)
- PAT: github_pat_[REDACTED]
- 결과: 403 Permission denied 오류

#### 두 번째 PAT 생성 및 성공
- 새 PAT: ghp_[REDACTED]
- Remote URL 설정:
```bash
$ git remote set-url origin https://briareus2000:[TOKEN]@github.com/briareus2000/basler-wrk.git
```

### 6. 최종 푸시 성공
```bash
$ git push -u origin main
branch 'main' set up to track 'origin/main'.
To https://github.com/briareus2000/basler-wrk.git
 * [new branch]      main -> main
```

## 완료된 작업
- ✅ GitHub에 `basler-wrk` 저장소 생성
- ✅ PAT 인증 설정
- ✅ 로컬 저장소를 GitHub에 푸시
- ✅ main 브랜치가 origin/main을 추적하도록 설정

## 최종 커밋 내역
```bash
$ git log --oneline -3
fe71230 init-commtit
775f05b  get-first
```

## 결과
2개의 커밋이 성공적으로 GitHub (https://github.com/briareus2000/basler-wrk)에 푸시되었습니다.

## 주요 학습 포인트
1. GitHub CLI 환경에서는 PAT를 사용한 인증이 필요
2. PAT 생성 시 'repo' 전체 권한이 필요
3. Remote URL에 PAT를 포함시켜 인증 가능
4. GitHub에 저장소를 먼저 생성한 후 푸시해야 함