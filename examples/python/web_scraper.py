"""
웹 스크레이퍼 예제

이 모듈은 웹사이트에서 데이터를 수집하는 기능을 제공합니다.
BeautifulSoup을 사용한 HTML 파싱 예제입니다.

사용법:
    python examples/web_scraper.py
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
import time
import ipaddress
import socket
from urllib.parse import urlparse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Article:
    """뉴스 기사 데이터 클래스"""
    title: str
    link: str
    summary: Optional[str] = None
    published_date: Optional[str] = None


class WebScraper:
    """웹 스크레이퍼 클래스"""

    # 최대 리다이렉트 횟수
    MAX_REDIRECTS = 5

    def __init__(self, base_url: str, timeout: int = 10):
        """
        웹 스크레이퍼 초기화

        Args:
            base_url: 스크래핑할 기본 URL
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.max_redirects = self.MAX_REDIRECTS
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def _validate_url(self, url: str) -> bool:
        """
        URL이 안전한지 검증합니다 (SSRF 방지).

        Args:
            url: 검증할 URL

        Returns:
            검증 성공 시 True

        Raises:
            ValueError: URL이 안전하지 않을 때
        """
        parsed = urlparse(url)

        # 1. 프로토콜 검증 (http, https만 허용)
        if parsed.scheme not in ['http', 'https']:
            raise ValueError(f"허용되지 않는 프로토콜: {parsed.scheme}")

        # 2. 호스트명 검증
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("유효하지 않은 URL: 호스트명 없음")

        # 3. localhost 차단
        localhost_names = ['localhost', 'localhost.localdomain']
        if hostname.lower() in localhost_names:
            raise ValueError(f"내부 호스트 접근 금지: {hostname}")

        # 4. IP 주소 검증
        try:
            ip = ipaddress.ip_address(hostname)

            # 루프백 주소 (127.0.0.0/8, ::1)
            if ip.is_loopback:
                raise ValueError(f"루프백 IP 접근 금지: {hostname}")

            # 내부 네트워크 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
            if ip.is_private:
                raise ValueError(f"내부 IP 접근 금지: {hostname}")

            # 링크 로컬 (169.254.0.0/16, fe80::/10)
            if ip.is_link_local:
                raise ValueError(f"링크 로컬 IP 접근 금지: {hostname}")

            # 예약된 주소
            if ip.is_reserved:
                raise ValueError(f"예약된 IP 접근 금지: {hostname}")

            # AWS 메타데이터 엔드포인트 명시적 차단
            if str(ip) == "169.254.169.254":
                raise ValueError("클라우드 메타데이터 엔드포인트 접근 금지")

        except ValueError as e:
            # hostname이 IP가 아닌 도메인인 경우
            # "does not appear to be" 에러는 정상 (도메인명)
            if "does not appear to be" not in str(e):
                raise

        # 5. DNS Rebinding 방어 - 도메인 이름의 DNS 해석 결과 검증
        try:
            # 도메인 이름을 IP로 해석
            resolved_ips = socket.getaddrinfo(hostname, None)
            for result in resolved_ips:
                ip_str = result[4][0]
                try:
                    resolved_ip = ipaddress.ip_address(ip_str)

                    # 해석된 IP가 내부 주소인지 검증 (우선순위 순서대로)
                    # AWS 메타데이터 엔드포인트 먼저 체크 (가장 구체적)
                    if str(resolved_ip) == "169.254.169.254":
                        raise ValueError(f"DNS Rebinding 감지: {hostname} → 클라우드 메타데이터 엔드포인트")

                    # 루프백 주소
                    if resolved_ip.is_loopback:
                        raise ValueError(f"DNS Rebinding 감지: {hostname} → {ip_str} (루프백)")

                    # 링크 로컬 (is_private보다 먼저 체크)
                    if resolved_ip.is_link_local:
                        raise ValueError(f"DNS Rebinding 감지: {hostname} → {ip_str} (링크 로컬)")

                    # 내부 네트워크
                    if resolved_ip.is_private:
                        raise ValueError(f"DNS Rebinding 감지: {hostname} → {ip_str} (내부 IP)")

                    # 예약된 주소
                    if resolved_ip.is_reserved:
                        raise ValueError(f"DNS Rebinding 감지: {hostname} → {ip_str} (예약됨)")

                except ValueError as ve:
                    # IP 파싱 실패는 무시하고 다음 결과로
                    if "does not appear to be" not in str(ve):
                        raise

        except socket.gaierror:
            # DNS 해석 실패는 허용 (오프라인 테스트 등)
            logger.debug(f"DNS 해석 실패: {hostname} (계속 진행)")

        return True

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()
        return False

    def fetch_page(self, url: str) -> Optional[str]:
        """
        URL에서 HTML 페이지를 가져옵니다.

        Args:
            url: 가져올 페이지 URL

        Returns:
            HTML 문자열 또는 실패 시 None

        Raises:
            ValueError: URL 검증 실패 시
            requests.RequestException: 네트워크 오류 발생 시
        """
        # URL 보안 검증 (SSRF 방지)
        self._validate_url(url)

        try:
            logger.info(f"Fetching page: {url}")
            # SSL 검증 명시, 타임아웃 세분화 (connect, read)
            response = self.session.get(
                url,
                timeout=(3.05, self.timeout),
                verify=True,
                allow_redirects=True
            )

            # 리다이렉트 발생 시 최종 URL도 검증
            if response.url != url:
                logger.info(f"리다이렉트 발생: {url} → {response.url}")
                self._validate_url(response.url)

            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise

    def parse_articles(self, html: str) -> List[Article]:
        """
        HTML에서 기사 정보를 파싱합니다.

        Args:
            html: 파싱할 HTML 문자열

        Returns:
            Article 객체 리스트
        """
        soup = BeautifulSoup(html, 'lxml')
        articles = []

        # 예시: 기사 항목 찾기 (실제 사이트 구조에 맞게 수정 필요)
        article_elements = soup.find_all('article', class_='post')

        for element in article_elements:
            try:
                title_elem = element.find('h2', class_='title')
                link_elem = element.find('a')
                summary_elem = element.find('p', class_='summary')
                date_elem = element.find('time')

                if title_elem and link_elem:
                    article = Article(
                        title=title_elem.get_text(strip=True),
                        link=link_elem.get('href', ''),
                        summary=summary_elem.get_text(strip=True) if summary_elem else None,
                        published_date=date_elem.get('datetime') if date_elem else None
                    )
                    articles.append(article)
            except (AttributeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse article: {e}")
                continue

        logger.info(f"Parsed {len(articles)} articles")
        return articles

    def scrape(self, page_count: int = 1, delay: float = 1.0) -> List[Article]:
        """
        여러 페이지에서 기사를 스크래핑합니다.

        Args:
            page_count: 스크래핑할 페이지 수
            delay: 요청 간 지연 시간 (초) - Rate limiting

        Returns:
            모든 기사의 리스트
        """
        all_articles = []

        for page_num in range(1, page_count + 1):
            url = f"{self.base_url}?page={page_num}"
            try:
                html = self.fetch_page(url)
                if html:
                    articles = self.parse_articles(html)
                    all_articles.extend(articles)

                # Rate limiting: 마지막 페이지가 아니면 딜레이 추가
                if page_num < page_count and delay > 0:
                    logger.debug(f"Rate limiting: {delay}초 대기")
                    time.sleep(delay)

            except (ValueError, requests.RequestException) as e:
                logger.error(f"Failed to scrape page {page_num}: {e}")
                continue

        return all_articles

    def close(self):
        """세션을 닫습니다."""
        self.session.close()


def extract_links(html: str, base_url: str = "") -> List[str]:
    """
    HTML에서 모든 링크를 추출합니다.

    Args:
        html: HTML 문자열
        base_url: 상대 경로를 절대 경로로 변환할 기본 URL

    Returns:
        링크 리스트
    """
    soup = BeautifulSoup(html, 'lxml')
    links = []

    for link in soup.find_all('a', href=True):
        href = link['href']
        # 상대 경로를 절대 경로로 변환
        if href.startswith('/') and base_url:
            href = base_url.rstrip('/') + href
        links.append(href)

    return links


def extract_images(html: str, base_url: str = "") -> List[Dict[str, str]]:
    """
    HTML에서 모든 이미지 정보를 추출합니다.

    Args:
        html: HTML 문자열
        base_url: 상대 경로를 절대 경로로 변환할 기본 URL

    Returns:
        이미지 정보 딕셔너리 리스트 (src, alt)
    """
    soup = BeautifulSoup(html, 'lxml')
    images = []

    for img in soup.find_all('img', src=True):
        src = img['src']
        # 상대 경로를 절대 경로로 변환
        if src.startswith('/') and base_url:
            src = base_url.rstrip('/') + src

        images.append({
            'src': src,
            'alt': img.get('alt', ''),
        })

    return images


def main() -> int:
    """메인 실행 함수"""
    # 예제 사용법
    print("=== 웹 스크레이퍼 예제 ===\n")

    # 주의: 실제 사용 시에는 robots.txt를 확인하고 적절한 딜레이를 추가하세요
    base_url = "https://example.com/news"

    try:
        # Context manager 사용으로 자동 세션 종료
        with WebScraper(base_url) as scraper:
            print(f"스크래핑 시작: {base_url}\n")

            # 페이지 스크래핑 (실제로는 동작하지 않음 - 예제 URL)
            # articles = scraper.scrape(page_count=3, delay=1.0)

            # 예제 HTML로 파싱 테스트
            example_html = """
            <html>
                <body>
                    <article class="post">
                        <h2 class="title">첫 번째 기사</h2>
                        <a href="/article/1">자세히 보기</a>
                        <p class="summary">이것은 첫 번째 기사의 요약입니다.</p>
                        <time datetime="2024-01-01">2024년 1월 1일</time>
                    </article>
                    <article class="post">
                        <h2 class="title">두 번째 기사</h2>
                        <a href="/article/2">자세히 보기</a>
                        <p class="summary">이것은 두 번째 기사의 요약입니다.</p>
                        <time datetime="2024-01-02">2024년 1월 2일</time>
                    </article>
                    <article class="post">
                        <h2 class="title">세 번째 기사</h2>
                        <a href="/article/3">자세히 보기</a>
                        <p class="summary">이것은 세 번째 기사의 요약입니다.</p>
                        <time datetime="2024-01-03">2024년 1월 3일</time>
                    </article>
                </body>
            </html>
            """

            articles = scraper.parse_articles(example_html)

            print(f"수집된 기사: {len(articles)}개\n")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article.title}")
                print(f"   링크: {article.link}")
                print(f"   요약: {article.summary}")
                print(f"   날짜: {article.published_date}\n")

            # 링크 추출 예제
            links = extract_links(example_html, base_url)
            print(f"\n추출된 링크: {len(links)}개")
            for link in links:
                print(f"  - {link}")

            print("\n스크래핑 완료!")

    except ValueError as e:
        logger.error(f"URL 검증 실패: {e}")
        return 1
    except requests.RequestException as e:
        logger.error(f"네트워크 오류: {e}")
        return 1
    except Exception as e:
        logger.error(f"예기치 않은 오류: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
