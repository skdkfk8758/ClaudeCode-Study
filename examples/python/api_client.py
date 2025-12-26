"""
API 클라이언트 예제

이 모듈은 REST API와 통신하는 클라이언트 기능을 제공합니다.
requests를 사용한 HTTP 통신 예제입니다.

사용법:
    python examples/api_client.py
"""

import requests
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
import logging
import time
from urllib.parse import urljoin

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """API 응답 데이터 클래스"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    success: bool

    @property
    def is_success(self) -> bool:
        """성공 여부 반환"""
        return self.success and 200 <= self.status_code < 300


class APIError(Exception):
    """API 관련 예외"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    """REST API 클라이언트"""

    def __init__(self,
                 base_url: str,
                 api_key: Optional[str] = None,
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        API 클라이언트 초기화

        Args:
            base_url: API 기본 URL
            api_key: API 인증 키 (선택)
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        """기본 헤더 설정"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Python-APIClient/1.0'
        }

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        self.session.headers.update(headers)

    def _build_url(self, endpoint: str) -> str:
        """
        전체 URL 구성

        Args:
            endpoint: API 엔드포인트

        Returns:
            전체 URL
        """
        return urljoin(self.base_url + '/', endpoint.lstrip('/'))

    def _make_request(self,
                     method: str,
                     endpoint: str,
                     **kwargs) -> APIResponse:
        """
        HTTP 요청 실행 (재시도 포함)

        Args:
            method: HTTP 메서드 (GET, POST, PUT, DELETE 등)
            endpoint: API 엔드포인트
            **kwargs: requests 라이브러리에 전달할 추가 인자

        Returns:
            APIResponse 객체

        Raises:
            APIError: API 요청 실패 시
        """
        url = self._build_url(endpoint)
        kwargs.setdefault('timeout', self.timeout)

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"{method} {url} (시도 {attempt + 1}/{self.max_retries})")

                response = self.session.request(method, url, **kwargs)

                # 성공 또는 클라이언트 오류는 재시도 안 함
                if response.status_code < 500:
                    break

                # 서버 오류는 재시도
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 지수 백오프
                    logger.warning(f"서버 오류 {response.status_code}, {wait_time}초 후 재시도")
                    time.sleep(wait_time)
                    continue

            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"요청 실패: {e}, {wait_time}초 후 재시도")
                    time.sleep(wait_time)
                    continue
                else:
                    raise APIError(f"최대 재시도 횟수 초과: {e}") from e

        # 응답 처리
        success = 200 <= response.status_code < 300

        try:
            data = response.json()
        except ValueError:
            data = response.text

        api_response = APIResponse(
            status_code=response.status_code,
            data=data,
            headers=dict(response.headers),
            success=success
        )

        if not success:
            error_msg = f"API 오류 {response.status_code}: {data}"
            logger.error(error_msg)
            raise APIError(error_msg, response.status_code)

        return api_response

    def get(self, endpoint: str, params: Optional[Dict] = None) -> APIResponse:
        """
        GET 요청

        Args:
            endpoint: API 엔드포인트
            params: 쿼리 파라미터

        Returns:
            APIResponse 객체
        """
        return self._make_request('GET', endpoint, params=params)

    def post(self, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        """
        POST 요청

        Args:
            endpoint: API 엔드포인트
            data: 요청 본문 데이터

        Returns:
            APIResponse 객체
        """
        return self._make_request('POST', endpoint, json=data)

    def put(self, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        """
        PUT 요청

        Args:
            endpoint: API 엔드포인트
            data: 요청 본문 데이터

        Returns:
            APIResponse 객체
        """
        return self._make_request('PUT', endpoint, json=data)

    def patch(self, endpoint: str, data: Optional[Dict] = None) -> APIResponse:
        """
        PATCH 요청

        Args:
            endpoint: API 엔드포인트
            data: 요청 본문 데이터

        Returns:
            APIResponse 객체
        """
        return self._make_request('PATCH', endpoint, json=data)

    def delete(self, endpoint: str) -> APIResponse:
        """
        DELETE 요청

        Args:
            endpoint: API 엔드포인트

        Returns:
            APIResponse 객체
        """
        return self._make_request('DELETE', endpoint)

    def close(self):
        """세션 종료"""
        self.session.close()
        logger.info("API 클라이언트 세션 종료")


class UserAPIClient(APIClient):
    """사용자 API 클라이언트 (예제)"""

    def get_user(self, user_id: int) -> Dict:
        """
        사용자 정보 조회

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 정보 딕셔너리
        """
        response = self.get(f'/users/{user_id}')
        return response.data

    def create_user(self, user_data: Dict) -> Dict:
        """
        사용자 생성

        Args:
            user_data: 사용자 데이터

        Returns:
            생성된 사용자 정보
        """
        response = self.post('/users', data=user_data)
        return response.data

    def update_user(self, user_id: int, user_data: Dict) -> Dict:
        """
        사용자 정보 수정

        Args:
            user_id: 사용자 ID
            user_data: 수정할 데이터

        Returns:
            수정된 사용자 정보
        """
        response = self.put(f'/users/{user_id}', data=user_data)
        return response.data

    def delete_user(self, user_id: int) -> bool:
        """
        사용자 삭제

        Args:
            user_id: 사용자 ID

        Returns:
            삭제 성공 여부
        """
        response = self.delete(f'/users/{user_id}')
        return response.is_success

    def list_users(self, page: int = 1, per_page: int = 10) -> List[Dict]:
        """
        사용자 목록 조회

        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수

        Returns:
            사용자 목록
        """
        params = {'page': page, 'per_page': per_page}
        response = self.get('/users', params=params)
        return response.data


def rate_limited_request(func):
    """
    Rate limiting 데코레이터

    초당 최대 요청 수를 제한합니다.
    """
    last_call_time = [0]
    min_interval = 1.0  # 초

    def wrapper(*args, **kwargs):
        current_time = time.time()
        time_since_last_call = current_time - last_call_time[0]

        if time_since_last_call < min_interval:
            sleep_time = min_interval - time_since_last_call
            logger.debug(f"Rate limit: {sleep_time:.2f}초 대기")
            time.sleep(sleep_time)

        result = func(*args, **kwargs)
        last_call_time[0] = time.time()
        return result

    return wrapper


def main():
    """메인 실행 함수"""
    print("=== API 클라이언트 예제 ===\n")

    # JSONPlaceholder API 사용 (무료 테스트 API)
    base_url = "https://jsonplaceholder.typicode.com"

    try:
        # 일반 API 클라이언트
        client = APIClient(base_url)

        # GET 요청 예제
        print("1. GET 요청 - 사용자 조회")
        response = client.get('/users/1')
        if response.is_success:
            user = response.data
            print(f"   이름: {user.get('name')}")
            print(f"   이메일: {user.get('email')}")
            print(f"   도시: {user.get('address', {}).get('city')}\n")

        # GET 요청 with 파라미터
        print("2. GET 요청 with 파라미터 - 게시물 목록")
        response = client.get('/posts', params={'userId': 1})
        if response.is_success:
            posts = response.data
            print(f"   사용자 1의 게시물: {len(posts)}개")
            print(f"   첫 번째 게시물: {posts[0].get('title')}\n")

        # POST 요청 예제
        print("3. POST 요청 - 새 게시물 생성")
        new_post = {
            'title': '테스트 게시물',
            'body': '이것은 테스트 게시물입니다.',
            'userId': 1
        }
        response = client.post('/posts', data=new_post)
        if response.is_success:
            created_post = response.data
            print(f"   생성된 게시물 ID: {created_post.get('id')}")
            print(f"   제목: {created_post.get('title')}\n")

        # PUT 요청 예제
        print("4. PUT 요청 - 게시물 수정")
        updated_post = {
            'id': 1,
            'title': '수정된 게시물',
            'body': '내용이 수정되었습니다.',
            'userId': 1
        }
        response = client.put('/posts/1', data=updated_post)
        if response.is_success:
            print(f"   수정 완료: {response.data.get('title')}\n")

        # DELETE 요청 예제
        print("5. DELETE 요청 - 게시물 삭제")
        response = client.delete('/posts/1')
        if response.is_success:
            print(f"   삭제 완료 (상태 코드: {response.status_code})\n")

        # 사용자 API 클라이언트 예제
        print("6. 전용 클라이언트 사용")
        user_client = UserAPIClient(base_url)

        users = user_client.list_users(page=1, per_page=3)
        print(f"   사용자 목록: {len(users)}명")
        for user in users:
            print(f"   - {user.get('name')} ({user.get('email')})")

        client.close()
        user_client.close()

        print("\nAPI 통신 완료!")

    except APIError as e:
        logger.error(f"API 오류: {e}")
        if e.status_code:
            logger.error(f"상태 코드: {e.status_code}")
        return 1
    except Exception as e:
        logger.error(f"예기치 않은 오류: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
