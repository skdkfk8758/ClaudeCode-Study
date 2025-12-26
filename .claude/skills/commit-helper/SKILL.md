---
name: commit-helper
description: Git diff를 분석하여 명확하고 구조화된 커밋 메시지를 생성합니다. 커밋 메시지 작성, 스테이징된 변경사항 검토, git commit 작업 시 자동으로 사용됩니다.
allowed-tools: Bash, Read, Grep
---

# Commit Helper Skill

이 스킬은 Git 변경사항을 분석하여 컨벤셔널 커밋(Conventional Commits) 형식의 명확한 커밋 메시지를 자동 생성합니다.

## 작업 프로세스

1. **변경사항 확인**
   ```bash
   git diff --staged
   git status
   ```

2. **변경 타입 분석**
   - 새로운 파일 추가 → `feat` (feature)
   - 기존 기능 수정 → `fix` 또는 `refactor`
   - 문서 수정 → `docs`
   - 테스트 추가/수정 → `test`
   - 스타일/포맷 변경 → `style`
   - 성능 개선 → `perf`
   - 빌드/의존성 → `build` 또는 `chore`

3. **컨벤셔널 커밋 메시지 생성**

## 커밋 메시지 형식

### 기본 구조
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type (필수)
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅, 세미콜론 등 (기능 변경 없음)
- `refactor`: 리팩토링 (기능 변경 없음)
- `test`: 테스트 추가/수정
- `chore`: 빌드 설정, 패키지 관리 등
- `perf`: 성능 개선
- `ci`: CI/CD 설정 변경

### Scope (선택)
변경된 모듈이나 컴포넌트명:
```
feat(auth): 소셜 로그인 기능 추가
fix(api): 응답 타임아웃 오류 수정
```

### Subject (필수)
- 50자 이하로 간결하게
- 명령문 형식 사용 ("추가한다" 대신 "추가")
- 마침표 없이 작성
- 무엇을 했는지 명확하게

### Body (선택)
- 72자마다 줄바꿈
- "무엇을" 그리고 "왜" 했는지 설명
- "어떻게"는 코드로 설명되므로 생략 가능

### Footer (선택)
- Breaking Changes: `BREAKING CHANGE: 설명`
- Issue 참조: `Closes #123`, `Fixes #456`

## 예시

### 예시 1: 새 기능 추가
```
feat(user): 비밀번호 재설정 기능 구현

사용자가 이메일을 통해 비밀번호를 재설정할 수 있도록
재설정 링크 생성 및 이메일 발송 기능을 추가했습니다.

- 재설정 토큰 생성 로직 추가
- 이메일 템플릿 작성
- 토큰 검증 및 비밀번호 업데이트 API 구현

Closes #42
```

### 예시 2: 버그 수정
```
fix(api): null 포인터 예외 처리

사용자 정보가 없을 때 발생하던 NullPointerException을
적절한 에러 메시지와 함께 처리하도록 수정했습니다.

Fixes #156
```

### 예시 3: 리팩토링
```
refactor(database): 쿼리 최적화 및 중복 코드 제거

반복되는 데이터베이스 쿼리를 헬퍼 함수로 추출하고
N+1 쿼리 문제를 해결했습니다.
```

### 예시 4: 문서 업데이트
```
docs(readme): API 사용 예시 추가

새로운 개발자가 쉽게 시작할 수 있도록
API 엔드포인트 사용 예시를 추가했습니다.
```

### 예시 5: Breaking Change
```
feat(api)!: 인증 API v2로 업그레이드

BREAKING CHANGE: 기존 v1 인증 엔드포인트가 제거되었습니다.
모든 클라이언트는 /api/v2/auth 엔드포인트를 사용해야 합니다.

마이그레이션 가이드:
- /auth/login → /api/v2/auth/login
- /auth/logout → /api/v2/auth/logout
```

## 한국어 vs 영어

프로젝트 컨벤션에 따라 선택:

### 한국어 예시
```
feat(주문): 주문 취소 기능 추가

고객이 주문 후 30분 이내에 주문을 취소할 수 있도록
취소 버튼과 취소 로직을 구현했습니다.
```

### 영어 예시
```
feat(order): Add order cancellation feature

Implement cancel button and cancellation logic to allow
customers to cancel orders within 30 minutes of placement.
```

## 지침

1. **변경사항 먼저 확인**: 항상 `git diff --staged`로 실제 변경사항을 먼저 확인
2. **단일 책임**: 하나의 커밋은 하나의 목적만 가지도록
3. **명확한 제목**: 제목만 읽어도 변경사항을 이해할 수 있도록
4. **상세한 본문**: 복잡한 변경은 본문에 상세히 설명
5. **Issue 연결**: 관련 이슈가 있으면 footer에 참조
6. **Breaking Change 명시**: API 변경이 있으면 반드시 표시

## 검토 체크리스트

커밋 메시지 작성 전 확인:
- [ ] Type이 적절한가?
- [ ] Subject가 50자 이하인가?
- [ ] Subject가 명령문 형식인가?
- [ ] 변경 이유가 설명되었는가?
- [ ] Breaking change가 있으면 표시했는가?
- [ ] 관련 이슈를 참조했는가?

## 실행 방법

이 스킬은 자동으로 활성화되지만, 명시적으로 요청할 수도 있습니다:

```
커밋 메시지 작성해줘
변경사항에 대한 커밋 메시지 생성
git commit 메시지 도움 필요
```

## 참고 자료

- Conventional Commits: https://www.conventionalcommits.org/
- Angular Commit Guidelines: https://github.com/angular/angular/blob/master/CONTRIBUTING.md
