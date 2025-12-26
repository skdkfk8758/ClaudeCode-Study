---
name: test-generator
description: Python 함수와 클래스에 대한 포괄적인 pytest 단위 테스트를 자동 생성합니다. 테스트 작성, unit test 생성, pytest 작업 시 자동으로 사용됩니다.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Test Generator Skill

이 스킬은 Python 코드를 분석하여 pytest 기반의 포괄적인 단위 테스트를 자동으로 생성합니다.

## 작업 프로세스

1. **대상 코드 분석**: 함수/클래스의 시그니처, 매개변수, 반환값 파악
2. **테스트 케이스 설계**: 정상 케이스, 엣지 케이스, 에러 케이스 식별
3. **테스트 코드 생성**: pytest 형식으로 테스트 작성
4. **Mock 생성**: 외부 의존성에 대한 Mock 객체 생성
5. **검증**: 생성된 테스트가 실행 가능한지 확인

## 테스트 생성 원칙

### 1. AAA 패턴 (Arrange-Act-Assert)
```python
def test_function():
    # Arrange: 테스트 준비
    input_data = "test"
    expected = "TEST"

    # Act: 함수 실행
    result = function(input_data)

    # Assert: 결과 검증
    assert result == expected
```

### 2. Given-When-Then
```python
def test_user_registration():
    # Given: 유효한 사용자 데이터가 주어졌을 때
    user_data = {"email": "test@example.com", "password": "secure123"}

    # When: 사용자 등록을 시도하면
    result = register_user(user_data)

    # Then: 등록이 성공해야 한다
    assert result.success is True
    assert result.user_id is not None
```

### 3. 테스트 케이스 종류

**정상 케이스 (Happy Path)**
- 기대되는 정상 입력
- 일반적인 사용 시나리오

**엣지 케이스 (Edge Cases)**
- 경계값 (0, 1, -1, 최댓값, 최솟값)
- 빈 문자열, 빈 리스트
- None 값
- 특수 문자

**에러 케이스 (Error Cases)**
- 잘못된 타입
- 범위를 벗어난 값
- 예외 발생 시나리오

## 테스트 템플릿

### 단순 함수 테스트
```python
import pytest
from module import function_name


def test_function_name_with_valid_input():
    """정상적인 입력에 대한 테스트"""
    # Arrange
    input_value = "test_input"
    expected_output = "expected_result"

    # Act
    result = function_name(input_value)

    # Assert
    assert result == expected_output


def test_function_name_with_empty_input():
    """빈 입력에 대한 테스트"""
    result = function_name("")
    assert result == ""


def test_function_name_with_none():
    """None 입력에 대한 테스트"""
    with pytest.raises(ValueError):
        function_name(None)
```

### 클래스 테스트
```python
import pytest
from module import MyClass


class TestMyClass:
    """MyClass에 대한 테스트"""

    @pytest.fixture
    def instance(self):
        """테스트용 인스턴스 생성"""
        return MyClass(param="test")

    def test_initialization(self, instance):
        """초기화 테스트"""
        assert instance.param == "test"
        assert instance.state is not None

    def test_method_with_valid_input(self, instance):
        """메서드 정상 동작 테스트"""
        result = instance.method("input")
        assert result is not None

    def test_method_with_invalid_input(self, instance):
        """메서드 에러 처리 테스트"""
        with pytest.raises(ValueError):
            instance.method(None)
```

### 비동기 함수 테스트
```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """비동기 함수 테스트"""
    result = await async_function("input")
    assert result == "expected"
```

## Mock 사용

### 외부 API 호출 Mock
```python
from unittest.mock import Mock, patch
import pytest


@patch('module.requests.get')
def test_api_call(mock_get):
    """API 호출 Mock 테스트"""
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_get.return_value = mock_response

    # Act
    result = fetch_data_from_api("endpoint")

    # Assert
    assert result["data"] == "test"
    mock_get.assert_called_once_with("endpoint")
```

### 파일 시스템 Mock
```python
from unittest.mock import mock_open, patch


@patch('builtins.open', new_callable=mock_open, read_data='test content')
def test_read_file(mock_file):
    """파일 읽기 Mock 테스트"""
    result = read_file("test.txt")
    assert result == "test content"
    mock_file.assert_called_once_with("test.txt", 'r')
```

### 데이터베이스 Mock
```python
from unittest.mock import MagicMock


def test_database_query():
    """데이터베이스 쿼리 Mock 테스트"""
    # Arrange
    mock_db = MagicMock()
    mock_db.query.return_value = [{"id": 1, "name": "test"}]

    # Act
    result = get_users(mock_db)

    # Assert
    assert len(result) == 1
    assert result[0]["name"] == "test"
    mock_db.query.assert_called_once()
```

## Pytest Fixtures

### 기본 Fixture
```python
import pytest


@pytest.fixture
def sample_data():
    """테스트용 샘플 데이터"""
    return {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com"
    }


def test_with_fixture(sample_data):
    """Fixture 사용 예시"""
    assert sample_data["id"] == 1
```

### Setup/Teardown Fixture
```python
import pytest


@pytest.fixture
def database_connection():
    """데이터베이스 연결 fixture"""
    # Setup
    conn = create_connection()
    yield conn
    # Teardown
    conn.close()


def test_database_operation(database_connection):
    """데이터베이스 작업 테스트"""
    result = database_connection.execute("SELECT 1")
    assert result is not None
```

## 매개변수화 테스트

```python
import pytest


@pytest.mark.parametrize("input_value,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
    ("123", "123"),
])
def test_uppercase_multiple_cases(input_value, expected):
    """여러 케이스를 한 번에 테스트"""
    result = to_uppercase(input_value)
    assert result == expected


@pytest.mark.parametrize("invalid_input", [
    None,
    123,
    [],
    {},
])
def test_with_invalid_types(invalid_input):
    """잘못된 타입 테스트"""
    with pytest.raises(TypeError):
        process_string(invalid_input)
```

## 테스트 케이스 생성 체크리스트

함수/클래스를 분석할 때 다음을 확인:

- [ ] 함수 시그니처 (매개변수, 반환값)
- [ ] 타입 힌트
- [ ] Docstring
- [ ] 가능한 예외
- [ ] 외부 의존성 (API, DB, 파일 등)
- [ ] 상태 변경 여부
- [ ] 부작용 (side effects)

각 함수/메서드에 대해 생성:

- [ ] 정상 동작 테스트 (최소 1개)
- [ ] 엣지 케이스 테스트 (경계값)
- [ ] 에러 처리 테스트 (예외 발생)
- [ ] Mock이 필요한 외부 호출 테스트
- [ ] 매개변수화 테스트 (여러 케이스)

## 테스트 파일 구조

```python
"""
tests/test_module_name.py

모듈에 대한 단위 테스트
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from module_name import function1, function2, MyClass


# Fixtures
@pytest.fixture
def sample_fixture():
    """테스트용 fixture"""
    return "test_data"


# 함수 테스트
class TestFunction1:
    """function1에 대한 테스트"""

    def test_with_valid_input(self):
        """정상 입력 테스트"""
        pass

    def test_with_invalid_input(self):
        """비정상 입력 테스트"""
        pass


class TestFunction2:
    """function2에 대한 테스트"""

    def test_edge_case(self):
        """엣지 케이스 테스트"""
        pass


# 클래스 테스트
class TestMyClass:
    """MyClass에 대한 테스트"""

    @pytest.fixture
    def instance(self):
        """테스트 인스턴스"""
        return MyClass()

    def test_initialization(self, instance):
        """초기화 테스트"""
        pass

    def test_method(self, instance):
        """메서드 테스트"""
        pass
```

## 실행 방법

이 스킬은 자동으로 활성화되지만, 명시적으로 요청할 수도 있습니다:

```
이 함수에 대한 테스트 생성해줘
pytest 테스트 작성
unit test 만들어줘
test coverage 높이기 위한 테스트 추가
```

## 생성 후 작업

테스트 생성 후 다음을 수행:

1. **테스트 실행**
   ```bash
   pytest tests/test_module.py -v
   ```

2. **커버리지 확인**
   ```bash
   pytest --cov=module --cov-report=html
   ```

3. **필요시 수정**: 생성된 테스트를 프로젝트 상황에 맞게 조정

## 주의사항

- 생성된 테스트는 기본 템플릿이므로 프로젝트 특성에 맞게 수정 필요
- 비즈니스 로직에 대한 도메인 지식은 개발자가 추가해야 함
- Mock 객체는 실제 동작과 다를 수 있으므로 통합 테스트도 필요
- 테스트 커버리지 100%가 목표가 아니라 중요한 로직 검증이 목표

## 참고 자료

- Pytest 공식 문서: https://docs.pytest.org/
- unittest.mock 문서: https://docs.python.org/3/library/unittest.mock.html
- Test-Driven Development (TDD) 가이드
