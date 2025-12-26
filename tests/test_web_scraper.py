"""
웹 스크레이퍼 테스트 모듈

코드 리뷰에서 발견된 주요 이슈에 대한 테스트:
1. HTML 파싱 오류 (잘못된 형식의 HTML)
2. URL 검증 누락 (SSRF 취약점)
3. SSL 검증 누락
"""

import pytest
import requests
import socket
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.web_scraper import (
    WebScraper,
    Article,
    extract_links,
    extract_images
)


class TestHTMLParsingErrors:
    """HTML 파싱 오류 테스트 클래스"""

    def test_parse_malformed_html_with_random_text(self):
        """
        테스트: 잘못된 형식의 HTML (임의의 텍스트 포함) 파싱

        시나리오: 라인 226의 "sdsdsd"와 같은 잘못된 텍스트가 HTML에 포함된 경우
        예상 결과: 파서가 에러 없이 처리하고 유효한 데이터만 추출
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        malformed_html = """
        <html>
            <body>
                sdsdsd
                <article class="post">
                    <h2 class="title">Valid Article</h2>
                    <a href="/article/1">Link</a>
                    <p class="summary">Valid summary</p>
                </article>
                random text here
                <article class="post">
                    <h2 class="title">Another Article</h2>
                    random inline text
                    <a href="/article/2">Link 2</a>
                </article>
            </body>
        </html>
        """

        # Act (실행)
        articles = scraper.parse_articles(malformed_html)

        # Assert (검증)
        assert len(articles) == 2, "잘못된 텍스트가 있어도 유효한 기사는 파싱되어야 함"
        assert articles[0].title == "Valid Article"
        assert articles[1].title == "Another Article"

    def test_parse_completely_broken_html(self):
        """
        테스트: 완전히 깨진 HTML 파싱

        시나리오: 닫히지 않은 태그, 잘못된 중첩 구조
        예상 결과: BeautifulSoup이 최선을 다해 파싱하고 에러 없이 처리
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        broken_html = """
        <html>
            <body>
                <article class="post">
                    <h2 class="title">Unclosed Article
                    <a href="/test">Link
                    <p class="summary">Unclosed paragraph
                <article class="post">
                    </h2><a href="/broken"></a><h2 class="title">Broken Nesting</h2>
                </article>
            </body>
        """

        # Act (실행)
        # 에러가 발생하지 않고 정상적으로 파싱되어야 함
        articles = scraper.parse_articles(broken_html)

        # Assert (검증)
        assert isinstance(articles, list), "깨진 HTML도 리스트를 반환해야 함"
        # BeautifulSoup은 깨진 HTML을 복구하므로 일부 article을 찾을 수 있음

    def test_parse_html_with_missing_required_elements(self):
        """
        테스트: 필수 요소가 없는 HTML 파싱

        시나리오: title이나 link가 없는 article 태그
        예상 결과: 해당 article은 건너뛰고 유효한 article만 반환
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        incomplete_html = """
        <html>
            <body>
                <article class="post">
                    <h2 class="title">Only Title</h2>
                </article>
                <article class="post">
                    <a href="/only-link">Only Link</a>
                </article>
                <article class="post">
                    <h2 class="title">Complete Article</h2>
                    <a href="/complete">Link</a>
                </article>
            </body>
        </html>
        """

        # Act (실행)
        articles = scraper.parse_articles(incomplete_html)

        # Assert (검증)
        assert len(articles) == 1, "필수 요소가 모두 있는 article만 반환되어야 함"
        assert articles[0].title == "Complete Article"

    def test_parse_empty_html(self):
        """
        테스트: 빈 HTML 파싱

        시나리오: 비어있거나 article이 없는 HTML
        예상 결과: 빈 리스트 반환
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        assert scraper.parse_articles("") == []
        assert scraper.parse_articles("<html></html>") == []
        assert scraper.parse_articles("<html><body></body></html>") == []

    def test_parse_html_with_special_characters(self):
        """
        테스트: 특수 문자가 포함된 HTML 파싱

        시나리오: HTML 엔티티, 유니코드, 특수 기호
        예상 결과: 특수 문자가 올바르게 파싱됨
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        special_html = """
        <html>
            <body>
                <article class="post">
                    <h2 class="title">&lt;Script&gt; &amp; "Quotes" &#39;Apostrophe&#39;</h2>
                    <a href="/article/1">Link</a>
                    <p class="summary">한글 テスト 中文 🚀 Emoji</p>
                </article>
            </body>
        </html>
        """

        # Act (실행)
        articles = scraper.parse_articles(special_html)

        # Assert (검증)
        assert len(articles) == 1
        assert "&lt;" in articles[0].title or "<" in articles[0].title
        assert "한글" in articles[0].summary


class TestURLValidationSSRF:
    """URL 검증 및 SSRF 취약점 테스트 클래스"""

    def test_reject_localhost_url(self):
        """
        테스트: localhost URL 거부

        시나리오: SSRF 공격을 통해 localhost에 접근 시도
        예상 결과: ValueError 발생하여 localhost 접근 차단
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        # URL 검증이 구현되어 localhost 접근이 차단됨
        with pytest.raises(ValueError, match="내부 호스트 접근 금지"):
            scraper.fetch_page("http://localhost/admin")

    def test_reject_internal_ip_addresses(self):
        """
        테스트: 내부 IP 주소 거부

        시나리오: SSRF 공격을 통해 내부 네트워크 IP에 접근 시도
        예상 결과: 192.168.x.x, 10.x.x.x, 127.x.x.x 등 내부 IP 거부
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        dangerous_urls = [
            ("http://127.0.0.1/admin", "루프백 IP 접근 금지"),
            ("http://192.168.1.1/config", "내부 IP 접근 금지"),
            ("http://10.0.0.1/internal", "내부 IP 접근 금지"),
            ("http://172.16.0.1/secret", "내부 IP 접근 금지"),
            # 169.254.169.254는 is_private로 먼저 걸림 (link-local은 private의 일종)
            ("http://169.254.169.254/metadata", "내부 IP 접근 금지"),
        ]

        # Act & Assert (실행 및 검증)
        for url, expected_error in dangerous_urls:
            # URL 검증이 구현되어 내부 IP 접근이 차단됨
            with pytest.raises(ValueError, match=expected_error):
                scraper.fetch_page(url)

    def test_reject_file_protocol(self):
        """
        테스트: file:// 프로토콜 거부

        시나리오: file:// 프로토콜을 통한 로컬 파일 접근 시도
        예상 결과: file:// 프로토콜 거부 (ValueError 발생)
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        # URL 검증이 구현되어 file:// 프로토콜이 차단됨
        with pytest.raises(ValueError, match="허용되지 않는 프로토콜"):
            scraper.fetch_page("file:///etc/passwd")

    def test_reject_redirect_to_internal_network(self):
        """
        테스트: 내부 네트워크로의 리다이렉트 거부

        시나리오: 외부 URL이 내부 IP로 리다이렉트되는 경우
        예상 결과: 리다이렉트 후 최종 URL도 검증되어야 하며 ValueError 발생
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            # 리다이렉트 시뮬레이션 - response.url을 문자열로 설정
            final_response = Mock()
            final_response.status_code = 200
            final_response.text = "<html>Internal</html>"
            final_response.url = "http://192.168.1.1/internal"  # 문자열로 설정
            final_response.raise_for_status = Mock()

            mock_get.return_value = final_response

            # 리다이렉트 후 URL 검증이 구현되어 내부 IP로의 리다이렉트가 차단됨
            with pytest.raises(ValueError, match="내부 IP 접근 금지"):
                scraper.fetch_page("https://example.com/redirect")

    def test_allow_valid_external_urls(self):
        """
        테스트: 유효한 외부 URL 허용

        시나리오: 정상적인 외부 웹사이트 URL
        예상 결과: https://example.com 등 정상 URL은 허용
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        valid_urls = [
            "https://example.com/page",
            "https://www.google.com",
            "https://github.com/user/repo",
        ]

        # Act & Assert (실행 및 검증)
        for url in valid_urls:
            with patch.object(scraper.session, 'get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.text = "<html>Valid Content</html>"
                mock_response.url = url  # response.url을 문자열로 설정
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                result = scraper.fetch_page(url)
                assert result is not None, f"{url}은 허용되어야 함"

    def test_allow_redirect_to_valid_external_url(self):
        """
        테스트: 유효한 외부 URL로의 리다이렉트 허용

        시나리오: 정상적인 외부 URL로 리다이렉트
        예상 결과: 정상적으로 처리되고 최종 URL도 검증됨
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            # 리다이렉트 시뮬레이션
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html>Redirected Content</html>"
            mock_response.url = "https://www.example.org/newpage"  # 다른 유효한 외부 URL
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = scraper.fetch_page("https://example.com/redirect")
            assert result is not None, "유효한 외부 URL로의 리다이렉트는 허용되어야 함"


class TestSSLVerification:
    """SSL 검증 테스트 클래스"""

    def test_ssl_verification_enabled_by_default(self):
        """
        테스트: SSL 검증이 기본적으로 활성화되어 있는지 확인

        시나리오: HTTPS URL 요청 시 SSL 인증서 검증
        예상 결과: verify=True로 요청이 전송됨
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html></html>"
            mock_response.url = "https://secure-site.com"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            scraper.fetch_page("https://secure-site.com")

            # requests.get 호출 시 verify 파라미터 확인
            call_args = mock_get.call_args

            # verify=True가 명시적으로 설정되었는지 확인
            assert call_args.kwargs.get('verify') is True, "SSL 검증이 명시적으로 활성화되어야 함"

    def test_reject_invalid_ssl_certificate(self):
        """
        테스트: 잘못된 SSL 인증서 거부

        시나리오: SSL 인증서가 유효하지 않은 사이트 접근
        예상 결과: SSLError 발생
        """
        # Arrange (준비)
        scraper = WebScraper("https://expired.badssl.com")

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.SSLError(
                "SSL certificate verify failed"
            )

            with pytest.raises(requests.exceptions.SSLError):
                scraper.fetch_page("https://expired.badssl.com")

    def test_ssl_verification_not_disabled(self):
        """
        테스트: SSL 검증이 의도적으로 비활성화되지 않았는지 확인

        시나리오: 코드에 verify=False가 없는지 확인
        예상 결과: verify=True로 명시적 설정
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html></html>"
            mock_response.url = "https://example.com"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            scraper.fetch_page("https://example.com")

            # verify=True가 명시적으로 설정되었는지 확인
            call_kwargs = mock_get.call_args.kwargs if mock_get.call_args.kwargs else {}
            assert call_kwargs.get('verify') is True, \
                "SSL 검증이 명시적으로 활성화되어야 함"

    def test_ssl_with_custom_ca_bundle(self):
        """
        테스트: 커스텀 CA 번들 사용 지원

        시나리오: 자체 서명된 인증서를 사용하는 경우
        예상 결과: verify 파라미터에 CA 번들 경로 전달 가능
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        ca_bundle_path = "/path/to/ca-bundle.crt"

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_get.return_value = Mock(status_code=200, text="<html></html>")

            # 현재 구현에서는 지원하지 않지만, 향후 개선 가능
            # scraper.fetch_page("https://example.com", verify=ca_bundle_path)

            # TODO: verify 파라미터 옵션 추가 고려


class TestWebScraperInitialization:
    """WebScraper 초기화 전용 테스트 클래스"""

    def test_initialization_succeeds_without_errors(self):
        """
        테스트: 초기화가 에러 없이 성공하는지 확인

        시나리오: WebScraper 객체 생성 시 ZeroDivisionError나 다른 예외가 발생하지 않음
        예상 결과: 객체가 정상적으로 생성됨 (이전 버그: line 51의 1/0)
        """
        # Arrange & Act (준비 및 실행)
        base_url = "https://example.com"
        timeout = 10

        # 초기화 중 예외가 발생하지 않아야 함
        scraper = WebScraper(base_url, timeout)

        # Assert (검증)
        assert scraper is not None

    def test_initialization_with_custom_timeout(self):
        """
        테스트: 커스텀 타임아웃으로 초기화

        시나리오: 사용자 정의 타임아웃 값으로 WebScraper 생성
        예상 결과: timeout이 올바르게 설정됨
        """
        # Arrange (준비)
        base_url = "https://example.com"
        custom_timeout = 15

        # Act (실행)
        scraper = WebScraper(base_url, custom_timeout)

        # Assert (검증)
        assert scraper.timeout == custom_timeout

    def test_initialization_with_default_timeout(self):
        """
        테스트: 기본 타임아웃으로 초기화

        시나리오: timeout 파라미터 없이 WebScraper 생성
        예상 결과: 기본값 10초로 설정됨
        """
        # Arrange (준비)
        base_url = "https://example.com"

        # Act (실행)
        scraper = WebScraper(base_url)

        # Assert (검증)
        assert scraper.timeout == 10

    def test_all_instance_variables_properly_set(self):
        """
        테스트: 모든 인스턴스 변수가 올바르게 설정되는지 확인

        시나리오: 초기화 후 base_url, timeout, session 모두 확인
        예상 결과: 모든 속성이 올바른 값과 타입으로 설정됨
        """
        # Arrange & Act (준비 및 실행)
        base_url = "https://example.com"
        timeout = 15
        scraper = WebScraper(base_url, timeout)

        # Assert (검증)
        assert scraper.base_url == base_url
        assert scraper.timeout == timeout
        assert scraper.session is not None
        assert isinstance(scraper.session, requests.Session)

    def test_session_has_user_agent_header(self):
        """
        테스트: 세션에 User-Agent 헤더가 설정되는지 확인

        시나리오: 초기화 후 session.headers에 User-Agent 포함
        예상 결과: User-Agent 헤더가 존재하고 적절한 값을 가짐
        """
        # Arrange & Act (준비 및 실행)
        scraper = WebScraper("https://example.com")

        # Assert (검증)
        assert 'User-Agent' in scraper.session.headers
        assert 'Mozilla' in scraper.session.headers['User-Agent']

    def test_session_max_redirects_is_set(self):
        """
        테스트: 세션의 max_redirects가 설정되는지 확인

        시나리오: 초기화 후 session.max_redirects 값 확인
        예상 결과: MAX_REDIRECTS 상수 값(5)으로 설정됨
        """
        # Arrange & Act (준비 및 실행)
        scraper = WebScraper("https://example.com")

        # Assert (검증)
        assert scraper.session.max_redirects == WebScraper.MAX_REDIRECTS
        assert scraper.session.max_redirects == 5

    def test_context_manager_enter(self):
        """
        테스트: Context manager의 __enter__ 메서드

        시나리오: with 문으로 WebScraper 사용 시작
        예상 결과: __enter__가 self를 반환하고 정상 작동
        """
        # Arrange (준비)
        base_url = "https://example.com"

        # Act (실행)
        with WebScraper(base_url) as scraper:
            # Assert (검증)
            assert scraper is not None
            assert scraper.base_url == base_url
            assert scraper.session is not None

    def test_context_manager_exit_closes_session(self):
        """
        테스트: Context manager의 __exit__ 메서드가 세션을 닫는지 확인

        시나리오: with 블록 종료 시 session.close() 호출
        예상 결과: 세션이 정상적으로 종료됨
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act (실행)
        with patch.object(scraper.session, 'close') as mock_close:
            scraper.__exit__(None, None, None)

            # Assert (검증)
            mock_close.assert_called_once()

    def test_context_manager_full_lifecycle(self):
        """
        테스트: Context manager의 전체 생명주기

        시나리오: with 문으로 전체 사용 과정 테스트
        예상 결과: 진입, 사용, 종료가 모두 정상 작동
        """
        # Arrange (준비)
        base_url = "https://example.com"

        # Act & Assert (실행 및 검증)
        with WebScraper(base_url) as scraper:
            # 진입 후: 정상적으로 사용 가능
            assert scraper.base_url == base_url
            assert scraper.session is not None

            # 세션 close 감시
            with patch.object(scraper.session, 'close') as mock_close:
                pass
        # with 블록 종료 후: close가 호출되었는지는 블록 내부에서 확인 불가
        # 하지만 예외 없이 정상 종료되어야 함

    def test_multiple_instances_independent(self):
        """
        테스트: 여러 WebScraper 인스턴스가 독립적인지 확인

        시나리오: 두 개의 WebScraper 인스턴스를 생성
        예상 결과: 각 인스턴스가 독립적인 session과 속성을 가짐
        """
        # Arrange & Act (준비 및 실행)
        scraper1 = WebScraper("https://example1.com", timeout=10)
        scraper2 = WebScraper("https://example2.com", timeout=20)

        # Assert (검증)
        assert scraper1.base_url != scraper2.base_url
        assert scraper1.timeout != scraper2.timeout
        assert scraper1.session is not scraper2.session

    def test_initialization_does_not_make_network_requests(self):
        """
        테스트: 초기화 시 네트워크 요청이 발생하지 않는지 확인

        시나리오: WebScraper 생성만으로는 HTTP 요청이 발생하지 않음
        예상 결과: 초기화 중 requests.get()이 호출되지 않음
        """
        # Arrange & Act (준비 및 실행)
        with patch('requests.Session.get') as mock_get:
            scraper = WebScraper("https://example.com")

            # Assert (검증)
            mock_get.assert_not_called()
            assert scraper is not None


class TestNormalFunctionality:
    """정상 기능 테스트 클래스"""

    def test_webscraper_initialization(self):
        """
        테스트: WebScraper 초기화

        시나리오: 정상적인 WebScraper 객체 생성
        예상 결과: base_url, timeout, session이 올바르게 설정됨
        """
        # Arrange & Act (준비 및 실행)
        base_url = "https://example.com"
        timeout = 15
        scraper = WebScraper(base_url, timeout)

        # Assert (검증)
        assert scraper.base_url == base_url
        assert scraper.timeout == timeout
        assert scraper.session is not None
        assert 'User-Agent' in scraper.session.headers

    def test_fetch_page_success(self):
        """
        테스트: 페이지 가져오기 성공

        시나리오: 정상적인 HTTP 200 응답
        예상 결과: HTML 텍스트 반환
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        expected_html = "<html><body>Test</body></html>"

        # Act (실행)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = expected_html
            mock_response.url = "https://example.com/test"  # response.url을 문자열로 설정
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = scraper.fetch_page("https://example.com/test")

        # Assert (검증)
        assert result == expected_html
        mock_get.assert_called_once()

    def test_fetch_page_timeout(self):
        """
        테스트: 페이지 가져오기 타임아웃

        시나리오: 요청이 timeout 시간을 초과
        예상 결과: Timeout 예외 발생
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com", timeout=1)

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            with pytest.raises(requests.exceptions.Timeout):
                scraper.fetch_page("https://slow-site.com")

    def test_fetch_page_404_error(self):
        """
        테스트: 404 에러 처리

        시나리오: 존재하지 않는 페이지 요청
        예상 결과: HTTPError 예외 발생
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.url = "https://example.com/notfound"  # response.url을 문자열로 설정
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_get.return_value = mock_response

            with pytest.raises(requests.exceptions.HTTPError):
                scraper.fetch_page("https://example.com/notfound")

    def test_parse_articles_success(self):
        """
        테스트: 기사 파싱 성공

        시나리오: 유효한 HTML에서 기사 정보 추출
        예상 결과: Article 객체 리스트 반환
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        html = """
        <html>
            <body>
                <article class="post">
                    <h2 class="title">Test Article</h2>
                    <a href="/article/1">Read More</a>
                    <p class="summary">This is a test summary.</p>
                    <time datetime="2024-01-01">January 1, 2024</time>
                </article>
            </body>
        </html>
        """

        # Act (실행)
        articles = scraper.parse_articles(html)

        # Assert (검증)
        assert len(articles) == 1
        assert articles[0].title == "Test Article"
        assert articles[0].link == "/article/1"
        assert articles[0].summary == "This is a test summary."
        assert articles[0].published_date == "2024-01-01"

    def test_scrape_multiple_pages(self):
        """
        테스트: 여러 페이지 스크래핑

        시나리오: page_count=3으로 여러 페이지 수집
        예상 결과: 모든 페이지의 기사가 합쳐진 리스트 반환
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        def mock_fetch(url):
            return """
            <html>
                <body>
                    <article class="post">
                        <h2 class="title">Article</h2>
                        <a href="/test">Link</a>
                    </article>
                </body>
            </html>
            """

        # Act (실행)
        with patch.object(scraper, 'fetch_page', side_effect=mock_fetch):
            articles = scraper.scrape(page_count=3)

        # Assert (검증)
        assert len(articles) == 3, "3개 페이지에서 각 1개씩 총 3개 기사"

    def test_extract_links_function(self):
        """
        테스트: 링크 추출 함수

        시나리오: HTML에서 모든 링크 추출
        예상 결과: href 속성을 가진 모든 a 태그의 링크 반환
        """
        # Arrange (준비)
        html = """
        <html>
            <body>
                <a href="/relative">Relative Link</a>
                <a href="https://external.com">External Link</a>
                <a href="/another">Another Link</a>
            </body>
        </html>
        """
        base_url = "https://example.com"

        # Act (실행)
        links = extract_links(html, base_url)

        # Assert (검증)
        assert len(links) == 3
        assert "https://example.com/relative" in links
        assert "https://external.com" in links
        assert "https://example.com/another" in links

    def test_extract_images_function(self):
        """
        테스트: 이미지 추출 함수

        시나리오: HTML에서 모든 이미지 정보 추출
        예상 결과: src와 alt 속성을 포함한 딕셔너리 리스트 반환
        """
        # Arrange (준비)
        html = """
        <html>
            <body>
                <img src="/image1.jpg" alt="Image 1">
                <img src="https://cdn.com/image2.png" alt="Image 2">
                <img src="/image3.gif">
            </body>
        </html>
        """
        base_url = "https://example.com"

        # Act (실행)
        images = extract_images(html, base_url)

        # Assert (검증)
        assert len(images) == 3
        assert images[0]['src'] == "https://example.com/image1.jpg"
        assert images[0]['alt'] == "Image 1"
        assert images[1]['src'] == "https://cdn.com/image2.png"
        assert images[2]['alt'] == ""

    def test_session_close(self):
        """
        테스트: 세션 종료

        시나리오: scraper.close() 호출
        예상 결과: session.close()가 호출됨
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Act (실행)
        with patch.object(scraper.session, 'close') as mock_close:
            scraper.close()

        # Assert (검증)
        mock_close.assert_called_once()

    def test_article_dataclass(self):
        """
        테스트: Article 데이터클래스

        시나리오: Article 객체 생성 및 속성 확인
        예상 결과: 모든 필드가 올바르게 설정됨
        """
        # Arrange & Act (준비 및 실행)
        article = Article(
            title="Test Title",
            link="https://example.com/article",
            summary="Test Summary",
            published_date="2024-01-01"
        )

        # Assert (검증)
        assert article.title == "Test Title"
        assert article.link == "https://example.com/article"
        assert article.summary == "Test Summary"
        assert article.published_date == "2024-01-01"

    def test_article_optional_fields(self):
        """
        테스트: Article의 선택적 필드

        시나리오: summary와 published_date 없이 Article 생성
        예상 결과: 선택적 필드는 None으로 설정됨
        """
        # Arrange & Act (준비 및 실행)
        article = Article(
            title="Minimal Article",
            link="/article"
        )

        # Assert (검증)
        assert article.title == "Minimal Article"
        assert article.link == "/article"
        assert article.summary is None
        assert article.published_date is None


class TestEdgeCases:
    """엣지 케이스 테스트 클래스"""

    def test_scrape_with_partial_page_failure(self):
        """
        테스트: 일부 페이지 실패 시 처리

        시나리오: 여러 페이지 중 일부만 성공
        예상 결과: 성공한 페이지의 기사만 반환
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        def mock_fetch(url):
            if "page=2" in url:
                raise requests.exceptions.HTTPError("Page not found")
            return """
            <html>
                <body>
                    <article class="post">
                        <h2 class="title">Article</h2>
                        <a href="/test">Link</a>
                    </article>
                </body>
            </html>
            """

        # Act (실행)
        with patch.object(scraper, 'fetch_page', side_effect=mock_fetch):
            articles = scraper.scrape(page_count=3)

        # Assert (검증)
        # 3개 페이지 중 1개 실패, 2개 성공
        assert len(articles) == 2

    def test_parse_articles_with_unicode_and_whitespace(self):
        """
        테스트: 유니코드 및 공백 처리

        시나리오: 제목과 요약에 여러 공백과 유니코드 문자
        예상 결과: strip()으로 공백이 제거되고 유니코드가 보존됨
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")
        html = """
        <html>
            <body>
                <article class="post">
                    <h2 class="title">

                        한글 Title   with   spaces

                    </h2>
                    <a href="/test">Link</a>
                    <p class="summary">  Summary  with  spaces  日本語  </p>
                </article>
            </body>
        </html>
        """

        # Act (실행)
        articles = scraper.parse_articles(html)

        # Assert (검증)
        assert len(articles) == 1
        assert articles[0].title == "한글 Title   with   spaces"
        assert "日本語" in articles[0].summary
        assert not articles[0].summary.startswith(" ")
        assert not articles[0].summary.endswith(" ")

    def test_very_large_html_parsing(self):
        """
        테스트: 매우 큰 HTML 파싱

        시나리오: 수백 개의 기사가 있는 큰 HTML
        예상 결과: 모든 기사가 올바르게 파싱됨
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # 100개의 기사 생성
        articles_html = ""
        for i in range(100):
            articles_html += f"""
                <article class="post">
                    <h2 class="title">Article {i}</h2>
                    <a href="/article/{i}">Link {i}</a>
                </article>
            """

        html = f"<html><body>{articles_html}</body></html>"

        # Act (실행)
        articles = scraper.parse_articles(html)

        # Assert (검증)
        assert len(articles) == 100
        assert articles[0].title == "Article 0"
        assert articles[99].title == "Article 99"

    @patch('socket.getaddrinfo')
    def test_network_connection_error(self, mock_getaddrinfo):
        """
        테스트: 네트워크 연결 오류

        시나리오: 네트워크 연결 실패
        예상 결과: ConnectionError 발생
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Mock DNS resolution to return an external IP (to bypass DNS Rebinding protection)
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('93.184.216.34', 0))  # example.com의 실제 IP
        ]

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()

            with pytest.raises(requests.exceptions.ConnectionError):
                scraper.fetch_page("https://unreachable.com")


class TestDNSRebindingProtection:
    """DNS Rebinding 보호 테스트"""

    @patch('socket.getaddrinfo')
    def test_dns_rebinding_to_private_ip(self, mock_getaddrinfo):
        """
        테스트: DNS Rebinding - 도메인이 내부 IP로 해석되는 경우

        시나리오: 외부 도메인 이름이 DNS에서 내부 IP로 해석됨
        예상 결과: ValueError 발생 (DNS Rebinding 감지)
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Mock DNS resolution to return a private IP
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('192.168.1.100', 0))
        ]

        # Act & Assert (실행 및 검증)
        with pytest.raises(ValueError, match="DNS Rebinding 감지.*내부 IP"):
            scraper.fetch_page("https://malicious-domain.com")

    @patch('socket.getaddrinfo')
    def test_dns_rebinding_to_loopback(self, mock_getaddrinfo):
        """
        테스트: DNS Rebinding - 도메인이 루프백 주소로 해석되는 경우

        시나리오: 외부 도메인 이름이 127.0.0.1로 해석됨
        예상 결과: ValueError 발생 (DNS Rebinding 감지)
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Mock DNS resolution to return loopback address
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('127.0.0.1', 0))
        ]

        # Act & Assert (실행 및 검증)
        with pytest.raises(ValueError, match="DNS Rebinding 감지.*루프백"):
            scraper.fetch_page("https://evil.example.com")

    @patch('socket.getaddrinfo')
    def test_dns_rebinding_to_link_local(self, mock_getaddrinfo):
        """
        테스트: DNS Rebinding - 도메인이 링크 로컬 주소로 해석되는 경우

        시나리오: 외부 도메인 이름이 169.254.x.x로 해석됨
        예상 결과: ValueError 발생 (DNS Rebinding 감지)
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Mock DNS resolution to return link-local address
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('169.254.1.1', 0))
        ]

        # Act & Assert (실행 및 검증)
        with pytest.raises(ValueError, match="DNS Rebinding 감지.*링크 로컬"):
            scraper.fetch_page("https://linklocal-attack.com")

    @patch('socket.getaddrinfo')
    def test_dns_rebinding_to_aws_metadata(self, mock_getaddrinfo):
        """
        테스트: DNS Rebinding - 도메인이 AWS 메타데이터 엔드포인트로 해석되는 경우

        시나리오: 외부 도메인 이름이 169.254.169.254로 해석됨
        예상 결과: ValueError 발생 (클라우드 메타데이터 엔드포인트 접근 금지)
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Mock DNS resolution to return AWS metadata endpoint
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('169.254.169.254', 0))
        ]

        # Act & Assert (실행 및 검증)
        with pytest.raises(ValueError, match="DNS Rebinding 감지.*메타데이터"):
            scraper.fetch_page("https://aws-metadata-attack.com")

    @patch('socket.getaddrinfo')
    def test_dns_rebinding_allows_valid_external_ip(self, mock_getaddrinfo):
        """
        테스트: DNS Rebinding 보호가 정상적인 외부 IP는 허용하는지 검증

        시나리오: 외부 도메인 이름이 정상적인 외부 IP로 해석됨
        예상 결과: 정상적으로 페이지 가져오기 진행
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Mock DNS resolution to return a valid external IP
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('93.184.216.34', 0))  # example.com의 실제 IP
        ]

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html>Valid Content</html>"
            mock_response.url = "https://example.com"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = scraper.fetch_page("https://example.com")
            assert result == "<html>Valid Content</html>"

    @patch('socket.getaddrinfo')
    def test_dns_resolution_failure_allows_request(self, mock_getaddrinfo):
        """
        테스트: DNS 해석 실패 시에도 요청이 진행되는지 검증

        시나리오: DNS 해석이 실패하는 경우 (오프라인 환경 등)
        예상 결과: DNS 검증을 건너뛰고 요청 진행 (실제 네트워크 오류는 나중에 발생)
        """
        # Arrange (준비)
        scraper = WebScraper("https://example.com")

        # Mock DNS resolution to fail
        mock_getaddrinfo.side_effect = socket.gaierror("Name or service not known")

        # Act & Assert (실행 및 검증)
        with patch.object(scraper.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html>Content</html>"
            mock_response.url = "https://example.com"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # DNS 실패는 무시되고 요청이 진행됨
            result = scraper.fetch_page("https://example.com")
            assert result == "<html>Content</html>"
