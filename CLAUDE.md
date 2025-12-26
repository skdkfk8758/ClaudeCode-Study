# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

이 프로젝트는 **Claude Code의 서브에이전트(Subagents)와 스킬(Skills) 기능에 대한 이해도를 높이기 위한 MVP 프로젝트**입니다.

- **기본 언어**: 한국어
- **개발 언어**: Python
- **목적**: Claude Code의 확장 기능(서브에이전트, 스킬)을 실습하고 이해하기 위한 예제 제공

## 프로젝트 구조

```
sub_agent_skills/
├── .claude/
│   ├── agents/          # 커스텀 서브에이전트 정의
│   │   ├── code-reviewer.md
│   │   ├── test-runner.md
│   │   └── data-analyzer.md
│   └── skills/          # 커스텀 스킬 정의
│       ├── commit-helper/
│       │   └── SKILL.md
│       └── test-generator/
│           └── SKILL.md
├── examples/            # 실습 예제 코드
│   ├── web_scraper.py
│   ├── data_processor.py
│   └── api_client.py
└── CLAUDE.md           # 이 파일
```

## 커스텀 명령어

### 서브에이전트 관련

```bash
# 코드 리뷰 서브에이전트 실행
> Use the code-reviewer subagent to review my recent changes

# 테스트 실행 서브에이전트 실행
> Use the test-runner subagent to run all tests

# 데이터 분석 서브에이전트 실행
> Use the data-analyzer subagent to analyze the dataset
```

### 스킬 관련

스킬은 자동으로 발견되어 사용됩니다:

```bash
# 커밋 헬퍼 스킬 (자동 활성화)
> Help me create a commit message for my changes

# 테스트 생성 스킬 (자동 활성화)
> Generate tests for this function
```

### 관리 명령어

```bash
# 사용 가능한 서브에이전트 확인 및 관리
/agents

# 사용 가능한 스킬 확인
> What Skills are available?
```

## 서브에이전트 아키텍처

### 1. code-reviewer (코드 리뷰어)

**목적**: 코드 품질, 보안, 베스트 프랙티스 검토

**도구**: Read, Grep, Glob, Bash

**사용 시점**:
- 코드 작성 또는 수정 후
- PR 생성 전
- 리팩토링 후

**검토 항목**:
- 코드 가독성 및 명확성
- 보안 취약점 (SQL injection, XSS, 인증 문제 등)
- 에러 처리
- 테스트 커버리지
- 성능 고려사항

### 2. test-runner (테스트 실행자)

**목적**: 자동화된 테스트 실행 및 결과 분석

**도구**: Bash, Read, Grep

**사용 시점**:
- 코드 변경 후 테스트 실행
- CI/CD 파이프라인 로컬 검증
- 특정 테스트 케이스 디버깅

**주요 기능**:
- pytest 실행
- 테스트 실패 원인 분석
- 커버리지 리포트 생성

### 3. data-analyzer (데이터 분석가)

**목적**: 데이터 분석, 시각화, 통계 계산

**도구**: Bash, Read, Write

**사용 시점**:
- CSV/JSON 데이터 분석
- 통계 계산
- 데이터 변환 및 정제

**주요 기능**:
- pandas를 이용한 데이터 처리
- 기초 통계 분석
- 데이터 시각화 (matplotlib, seaborn)

## 스킬 아키텍처

### 1. commit-helper (커밋 헬퍼)

**자동 활성화 조건**: "커밋 메시지", "commit message", "스테이징된 변경사항"

**기능**:
- git diff --staged 분석
- 컨벤셔널 커밋 형식으로 메시지 생성
- 한국어/영어 커밋 메시지 지원

**커밋 메시지 형식**:
```
<type>: <subject>

<body>

<footer>
```

### 2. test-generator (테스트 생성기)

**자동 활성화 조건**: "테스트 생성", "generate tests", "unit test"

**기능**:
- 함수/클래스 분석
- pytest 기반 단위 테스트 생성
- 엣지 케이스 고려
- Mock 객체 자동 생성

## Python 개발 가이드

### 필수 패키지

```bash
pip install pytest pytest-cov pandas requests beautifulsoup4
```

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_example.py

# 커버리지와 함께 실행
pytest --cov=. --cov-report=html
```

### 코드 스타일

- PEP 8 준수
- Type hints 사용 권장
- Docstring은 Google 스타일 사용

### 예제 실행

```bash
# 웹 스크레이퍼 예제
python examples/web_scraper.py

# 데이터 처리 예제
python examples/data_processor.py

# API 클라이언트 예제
python examples/api_client.py
```

## 서브에이전트와 스킬 개발 가이드

### 새로운 서브에이전트 추가

1. `/agents` 명령어 실행
2. "Create New Agent" 선택
3. 프로젝트 수준 선택 (`.claude/agents/`)
4. 이름, 설명, 도구 권한 설정
5. 상세한 시스템 프롬프트 작성

**템플릿**:
```markdown
---
name: your-agent-name
description: 명확한 사용 시점 설명. Use proactively when [조건].
tools: Read, Bash, Grep
model: sonnet
---

당신은 [역할]입니다.

작업 프로세스:
1. [단계 1]
2. [단계 2]
3. [단계 3]

핵심 가이드라인:
- [가이드라인 1]
- [가이드라인 2]
```

### 새로운 스킬 추가

1. `.claude/skills/your-skill-name/` 디렉토리 생성
2. `SKILL.md` 파일 작성
3. 필요시 지원 스크립트 추가

**템플릿**:
```yaml
---
name: your-skill-name
description: 스킬 기능 설명. [트리거 키워드] 작업 시 사용.
allowed-tools: Read, Bash  # 선택사항
---

# Your Skill Name

## 지침

1. [단계별 지침]

## 예시

[구체적인 사용 예시]
```

## 핵심 개념 이해

### 서브에이전트 vs 스킬

| 측면 | 서브에이전트 | 스킬 |
|------|------------|------|
| **목적** | 복잡한 멀티스텝 작업 처리 | 특정 워크플로우 가이드 제공 |
| **컨텍스트** | 독립적인 컨텍스트 윈도우 | 메인 컨텍스트 공유 |
| **도구 접근** | 제한 가능 | 제한 가능 |
| **활성화** | 명시적 또는 자동 위임 | 자동 발견 (문맥 기반) |
| **파일 형식** | `.md` (YAML 프론트매터) | `SKILL.md` (디렉토리) |

### 언제 무엇을 사용할까?

**서브에이전트 사용**:
- 독립적인 작업 실행 필요
- 메인 컨텍스트 보존 중요
- 도구 권한 제한 필요
- 복잡한 멀티스텝 워크플로우

**스킬 사용**:
- 반복적인 프롬프트 패턴
- 간단한 가이드라인 제공
- 자동 발견 선호
- 지원 파일(스크립트, 템플릿) 포함

## 실습 시나리오

### 시나리오 1: 코드 리뷰 자동화

```python
# 1. 코드 작성
# 2. 서브에이전트 호출
> Use the code-reviewer subagent to review my code

# 3. 피드백 받고 수정
# 4. 재검토
```

### 시나리오 2: 테스트 주도 개발

```python
# 1. 함수 작성
# 2. 스킬 자동 활성화
> Generate comprehensive tests for this function

# 3. 테스트 실행 서브에이전트
> Use the test-runner subagent to verify all tests pass
```

### 시나리오 3: 데이터 분석 파이프라인

```python
# 1. 데이터 수집
# 2. 분석 서브에이전트 호출
> Use the data-analyzer subagent to analyze this CSV file

# 3. 결과 시각화 요청
# 4. 리포트 생성
```

## 문제 해결

### 서브에이전트가 활성화되지 않을 때

1. `description` 필드가 명확한지 확인
2. "Use the [agent-name] subagent" 명시적 호출 시도
3. `/agents` 명령어로 등록 확인

### 스킬이 발견되지 않을 때

1. `SKILL.md` 파일 위치 확인 (`.claude/skills/skill-name/SKILL.md`)
2. YAML 프론트매터 구문 오류 확인
3. `description`에 트리거 키워드 추가

### 도구 권한 오류

1. 서브에이전트/스킬의 `tools` 또는 `allowed-tools` 확인
2. 필요한 도구를 목록에 추가
3. 모든 도구 허용하려면 필드 제거
