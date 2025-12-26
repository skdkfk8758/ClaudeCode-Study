/**
 * 웹 스크레이퍼 예제 (TypeScript)
 *
 * 이 모듈은 웹사이트에서 데이터를 수집하는 기능을 제공합니다.
 * Cheerio를 사용한 HTML 파싱 예제입니다.
 *
 * 사용법:
 *   npm run scraper
 *   또는
 *   tsx examples/web-scraper.ts
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import * as cheerio from 'cheerio';
import { URL } from 'url';
import { isIP } from 'net';
import { lookup } from 'dns/promises';

/**
 * 뉴스 기사 데이터 인터페이스
 */
interface Article {
  title: string;
  link: string;
  summary?: string;
  publishedDate?: string;
}

/**
 * 웹 스크레이퍼 클래스
 */
class WebScraper {
  private baseUrl: string;
  private timeout: number;
  private client: AxiosInstance;
  private readonly MAX_REDIRECTS = 5;

  /**
   * 웹 스크레이퍼 초기화
   *
   * @param baseUrl - 스크래핑할 기본 URL
   * @param timeout - 요청 타임아웃 (밀리초)
   */
  constructor(baseUrl: string, timeout: number = 10000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
    this.client = axios.create({
      timeout,
      maxRedirects: this.MAX_REDIRECTS,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
      },
      validateStatus: (status) => status >= 200 && status < 300
    });
  }

  /**
   * URL이 안전한지 검증합니다 (SSRF 방지).
   *
   * @param urlString - 검증할 URL
   * @throws Error - URL이 안전하지 않을 때
   */
  private async validateUrl(urlString: string): Promise<void> {
    let parsedUrl: URL;

    try {
      parsedUrl = new URL(urlString);
    } catch (error) {
      throw new Error(`유효하지 않은 URL: ${urlString}`);
    }

    // 1. 프로토콜 검증 (http, https만 허용)
    if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
      throw new Error(`허용되지 않는 프로토콜: ${parsedUrl.protocol}`);
    }

    // 2. 호스트명 검증
    const hostname = parsedUrl.hostname;
    if (!hostname) {
      throw new Error('유효하지 않은 URL: 호스트명 없음');
    }

    // 3. localhost 차단
    const localhostNames = ['localhost', 'localhost.localdomain'];
    if (localhostNames.includes(hostname.toLowerCase())) {
      throw new Error(`내부 호스트 접근 금지: ${hostname}`);
    }

    // 4. IP 주소 검증
    const ipType = isIP(hostname);
    if (ipType !== 0) {
      this.validateIpAddress(hostname);
    }

    // 5. DNS Rebinding 방어 - 도메인 이름의 DNS 해석 결과 검증
    try {
      const addresses = await lookup(hostname, { all: true });

      for (const addr of addresses) {
        this.validateIpAddress(addr.address);
      }
    } catch (error) {
      // DNS 해석 실패는 허용 (오프라인 테스트 등)
      console.debug(`DNS 해석 실패: ${hostname} (계속 진행)`);
    }
  }

  /**
   * IP 주소가 안전한지 검증합니다.
   *
   * @param ip - 검증할 IP 주소
   * @throws Error - IP가 안전하지 않을 때
   */
  private validateIpAddress(ip: string): void {
    // AWS 메타데이터 엔드포인트 명시적 차단
    if (ip === '169.254.169.254') {
      throw new Error('클라우드 메타데이터 엔드포인트 접근 금지');
    }

    // 루프백 주소 (127.0.0.0/8, ::1)
    if (this.isLoopback(ip)) {
      throw new Error(`루프백 IP 접근 금지: ${ip}`);
    }

    // 링크 로컬 (169.254.0.0/16, fe80::/10)
    if (this.isLinkLocal(ip)) {
      throw new Error(`링크 로컬 IP 접근 금지: ${ip}`);
    }

    // 내부 네트워크 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    if (this.isPrivate(ip)) {
      throw new Error(`내부 IP 접근 금지: ${ip}`);
    }
  }

  /**
   * IP가 루프백 주소인지 확인
   */
  private isLoopback(ip: string): boolean {
    if (ip.includes(':')) {
      // IPv6
      return ip === '::1';
    }
    // IPv4 - 127.0.0.0/8
    const parts = ip.split('.').map(Number);
    return parts[0] === 127;
  }

  /**
   * IP가 링크 로컬 주소인지 확인
   */
  private isLinkLocal(ip: string): boolean {
    if (ip.includes(':')) {
      // IPv6 - fe80::/10
      return ip.toLowerCase().startsWith('fe80:');
    }
    // IPv4 - 169.254.0.0/16
    const parts = ip.split('.').map(Number);
    return parts[0] === 169 && parts[1] === 254;
  }

  /**
   * IP가 사설 주소인지 확인
   */
  private isPrivate(ip: string): boolean {
    if (ip.includes(':')) {
      // IPv6 - fc00::/7 (Unique Local Addresses)
      const firstByte = parseInt(ip.substring(0, 2), 16);
      return (firstByte & 0xfe) === 0xfc;
    }

    // IPv4
    const parts = ip.split('.').map(Number);

    // 10.0.0.0/8
    if (parts[0] === 10) return true;

    // 172.16.0.0/12
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;

    // 192.168.0.0/16
    if (parts[0] === 192 && parts[1] === 168) return true;

    return false;
  }

  /**
   * URL에서 HTML 페이지를 가져옵니다.
   *
   * @param url - 가져올 페이지 URL
   * @returns HTML 문자열
   * @throws Error - URL 검증 실패 또는 네트워크 오류
   */
  async fetchPage(url: string): Promise<string> {
    // URL 보안 검증 (SSRF 방지)
    await this.validateUrl(url);

    try {
      console.log(`Fetching page: ${url}`);

      const response = await this.client.get(url, {
        // SSL 검증 명시적 활성화
        httpsAgent: undefined, // axios 기본값 사용 (검증 활성화)
      });

      // 리다이렉트 발생 시 최종 URL도 검증
      if (response.request.res.responseUrl && response.request.res.responseUrl !== url) {
        const finalUrl = response.request.res.responseUrl;
        console.log(`리다이렉트 발생: ${url} → ${finalUrl}`);
        await this.validateUrl(finalUrl);
      }

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`Failed to fetch ${url}: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * HTML에서 기사 정보를 파싱합니다.
   *
   * @param html - 파싱할 HTML 문자열
   * @returns Article 객체 배열
   */
  parseArticles(html: string): Article[] {
    const $ = cheerio.load(html);
    const articles: Article[] = [];

    // 예시: 기사 항목 찾기 (실제 사이트 구조에 맞게 수정 필요)
    $('article.post').each((_, element) => {
      try {
        const $element = $(element);
        const title = $element.find('h2.title').text().trim();
        const link = $element.find('a').attr('href') || '';
        const summary = $element.find('p.summary').text().trim() || undefined;
        const publishedDate = $element.find('time').attr('datetime') || undefined;

        if (title && link) {
          articles.push({
            title,
            link,
            summary,
            publishedDate
          });
        }
      } catch (error) {
        console.warn(`Failed to parse article: ${error}`);
      }
    });

    console.log(`Parsed ${articles.length} articles`);
    return articles;
  }

  /**
   * 여러 페이지에서 기사를 스크래핑합니다.
   *
   * @param pageCount - 스크래핑할 페이지 수
   * @param delay - 요청 간 지연 시간 (밀리초) - Rate limiting
   * @returns 모든 기사의 배열
   */
  async scrape(pageCount: number = 1, delay: number = 1000): Promise<Article[]> {
    const allArticles: Article[] = [];

    for (let pageNum = 1; pageNum <= pageCount; pageNum++) {
      const url = `${this.baseUrl}?page=${pageNum}`;

      try {
        const html = await this.fetchPage(url);
        const articles = this.parseArticles(html);
        allArticles.push(...articles);

        // Rate limiting: 마지막 페이지가 아니면 딜레이 추가
        if (pageNum < pageCount && delay > 0) {
          console.debug(`Rate limiting: ${delay}ms 대기`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      } catch (error) {
        console.error(`Failed to scrape page ${pageNum}: ${error}`);
        continue;
      }
    }

    return allArticles;
  }
}

/**
 * HTML에서 모든 링크를 추출합니다.
 *
 * @param html - HTML 문자열
 * @param baseUrl - 상대 경로를 절대 경로로 변환할 기본 URL
 * @returns 링크 배열
 */
function extractLinks(html: string, baseUrl: string = ''): string[] {
  const $ = cheerio.load(html);
  const links: string[] = [];

  $('a[href]').each((_, element) => {
    let href = $(element).attr('href') || '';

    // 상대 경로를 절대 경로로 변환
    if (href.startsWith('/') && baseUrl) {
      href = baseUrl.replace(/\/$/, '') + href;
    }

    links.push(href);
  });

  return links;
}

/**
 * HTML에서 모든 이미지 정보를 추출합니다.
 *
 * @param html - HTML 문자열
 * @param baseUrl - 상대 경로를 절대 경로로 변환할 기본 URL
 * @returns 이미지 정보 객체 배열 (src, alt)
 */
function extractImages(html: string, baseUrl: string = ''): Array<{ src: string; alt: string }> {
  const $ = cheerio.load(html);
  const images: Array<{ src: string; alt: string }> = [];

  $('img[src]').each((_, element) => {
    let src = $(element).attr('src') || '';

    // 상대 경로를 절대 경로로 변환
    if (src.startsWith('/') && baseUrl) {
      src = baseUrl.replace(/\/$/, '') + src;
    }

    images.push({
      src,
      alt: $(element).attr('alt') || ''
    });
  });

  return images;
}

/**
 * 메인 실행 함수
 */
async function main(): Promise<number> {
  // 예제 사용법
  console.log('=== 웹 스크레이퍼 예제 (TypeScript) ===\n');

  // 주의: 실제 사용 시에는 robots.txt를 확인하고 적절한 딜레이를 추가하세요
  const baseUrl = 'https://example.com/news';

  try {
    const scraper = new WebScraper(baseUrl);
    console.log(`스크래핑 시작: ${baseUrl}\n`);

    // 페이지 스크래핑 (실제로는 동작하지 않음 - 예제 URL)
    // const articles = await scraper.scrape(3, 1000);

    // 예제 HTML로 파싱 테스트
    const exampleHtml = `
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
    `;

    const articles = scraper.parseArticles(exampleHtml);

    console.log(`수집된 기사: ${articles.length}개\n`);
    articles.forEach((article, i) => {
      console.log(`${i + 1}. ${article.title}`);
      console.log(`   링크: ${article.link}`);
      console.log(`   요약: ${article.summary}`);
      console.log(`   날짜: ${article.publishedDate}\n`);
    });

    // 링크 추출 예제
    const links = extractLinks(exampleHtml, baseUrl);
    console.log(`\n추출된 링크: ${links.length}개`);
    links.forEach(link => {
      console.log(`  - ${link}`);
    });

    console.log('\n스크래핑 완료!');

    return 0;
  } catch (error) {
    if (error instanceof Error) {
      console.error(`오류: ${error.message}`);
    }
    return 1;
  }
}

// 스크립트로 직접 실행될 때만 main 함수 실행
if (import.meta.url === `file://${process.argv[1]}`) {
  main().then(code => process.exit(code));
}

export { WebScraper, Article, extractLinks, extractImages };
