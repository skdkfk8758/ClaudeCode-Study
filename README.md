# Claude Code 서브에이전트 & 스킬 학습 프로젝트

Claude Code의 서브에이전트(Subagents)와 스킬(Skills) 기능을 실습하고 이해하기 위한 MVP 프로젝트입니다.

## 프로젝트 개요

- **목적**: Claude Code의 확장 기능 실습 및 이해
- **언어**: 한국어 (기본), Python (개발)
- **주요 기능**: 커스텀 서브에이전트와 스킬 예제 제공

## 설치 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 프로젝트 구조 확인

```
sub_agent_skills/
├── .claude/
│   ├── agents/              # 커스텀 서브에이전트
│   │   ├── code-reviewer.md
│   │   ├── test-runner.md
│   │   └── data-analyzer.md
│   └── skills/              # 커스텀 스킬
│       ├── commit-helper/
│       └── test-generator/
├── examples/                # Python 예제 코드
│   ├── web_scraper.py
│   ├── data_processor.py
│   └── api_client.py
├── CLAUDE.md               # Claude Code 가이드
├── requirements.txt
└── README.md
```

## 서브에이전트

### 1. code-reviewer (코드 리뷰어)

코드 품질, 보안, 베스트 프랙티스를 자동으로 검토합니다.

**사용 방법:**
```
> Use the code-reviewer subagent to review my recent changes
```

**검토 항목:**
- 코드 가독성 및 구조
- 보안 취약점 (SQL Injection, XSS 등)
- 에러 처리
- 테스트 커버리지
- 성능 고려사항

### 2. test-runner (테스트 실행자)

자동화된 테스트 실행 및 결과 분석을 수행합니다.

**사용 방법:**
```
> Use the test-runner subagent to run all tests
```

**주요 기능:**
- pytest 실행
- 테스트 실패 원인 분석
- 커버리지 리포트 생성
- 테스트 모범 사례 검증

### 3. data-analyzer (데이터 분석가)

데이터 분석, 시각화, 통계 계산을 수행합니다.

**사용 방법:**
```
> Use the data-analyzer subagent to analyze this CSV file
```

**주요 기능:**
- CSV/JSON/Excel 데이터 로드
- 기초 통계 분석
- 데이터 시각화
- 인사이트 도출

## 스킬

### 1. commit-helper (커밋 헬퍼)

Git 변경사항을 분석하여 컨벤셔널 커밋 형식의 메시지를 생성합니다.

**자동 활성화 조건:**
- "커밋 메시지"
- "commit message"
- "스테이징된 변경사항"

**커밋 형식:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 2. test-generator (테스트 생성기)

Python 함수/클래스에 대한 포괄적인 pytest 테스트를 자동 생성합니다.

**자동 활성화 조건:**
- "테스트 생성"
- "generate tests"
- "unit test"

**생성 내용:**
- 정상 케이스 테스트
- 엣지 케이스 테스트
- 에러 케이스 테스트
- Mock 객체

## 예제 실행

### 웹 스크레이퍼
```bash
python examples/web_scraper.py
```

HTML에서 데이터를 추출하는 BeautifulSoup 예제입니다.

### 데이터 처리
```bash
python examples/data_processor.py
```

pandas를 사용한 데이터 처리 및 분석 예제입니다.

### API 클라이언트
```bash
python examples/api_client.py
```

REST API와 통신하는 클라이언트 예제입니다.

## 실습 시나리오

### 시나리오 1: 코드 리뷰 자동화

1. Python 코드 작성
2. 서브에이전트 호출
   ```
   > Use the code-reviewer subagent to review my code
   ```
3. 피드백 받고 수정
4. 재검토 수행

### 시나리오 2: 테스트 주도 개발

1. 함수 작성
2. 테스트 생성 요청
   ```
   > Generate comprehensive tests for this function
   ```
3. 테스트 실행
   ```
   > Use the test-runner subagent to verify all tests pass
   ```

### 시나리오 3: 데이터 분석 파이프라인

1. 데이터 수집
2. 분석 요청
   ```
   > Use the data-analyzer subagent to analyze this CSV file
   ```
3. 결과 시각화 및 리포트 생성

## 개발 가이드

### 새로운 서브에이전트 추가

1. `/agents` 명령어 실행
2. "Create New Agent" 선택
3. 이름, 설명, 도구 권한 설정
4. 상세한 시스템 프롬프트 작성

### 새로운 스킬 추가

1. `.claude/skills/your-skill-name/` 디렉토리 생성
2. `SKILL.md` 파일 작성
3. 필요시 지원 스크립트 추가

자세한 내용은 [CLAUDE.md](CLAUDE.md)를 참조하세요.

## 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_example.py

# 커버리지와 함께 실행
pytest --cov=. --cov-report=html
```

## 문제 해결

### 서브에이전트가 활성화되지 않을 때

1. `description` 필드가 명확한지 확인
2. "Use the [agent-name] subagent" 명시적 호출
3. `/agents` 명령어로 등록 확인

### 스킬이 발견되지 않을 때

1. `SKILL.md` 파일 위치 확인
2. YAML 프론트매터 구문 확인
3. `description`에 트리거 키워드 추가

## 참고 자료

- [Claude Code 공식 문서](https://code.claude.com)
- [서브에이전트 문서](https://code.claude.com/docs/en/sub-agents.md)
- [스킬 문서](https://code.claude.com/docs/en/skills.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pytest 문서](https://docs.pytest.org/)

## 라이선스

이 프로젝트는 학습 목적으로 제공됩니다.
