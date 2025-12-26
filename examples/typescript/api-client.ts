/**
 * API 클라이언트 예제 (TypeScript)
 *
 * 이 모듈은 REST API와 통신하는 클라이언트 기능을 제공합니다.
 * axios를 사용한 HTTP 통신 예제입니다.
 *
 * 사용법:
 *   npm run api
 *   또는
 *   tsx examples/api-client.ts
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * API 응답 인터페이스
 */
interface APIResponse<T = any> {
  statusCode: number;
  data: T;
  headers: Record<string, string>;
  success: boolean;
}

/**
 * API 오류 클래스
 */
class APIError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
  }
}

/**
 * REST API 클라이언트
 */
class APIClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private maxRetries: number;
  protected client: AxiosInstance;

  /**
   * API 클라이언트 초기화
   *
   * @param baseUrl - API 기본 URL
   * @param apiKey - API 인증 키 (선택)
   * @param timeout - 요청 타임아웃 (밀리초)
   * @param maxRetries - 최대 재시도 횟수
   */
  constructor(
    baseUrl: string,
    apiKey?: string,
    timeout: number = 30000,
    maxRetries: number = 3
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
    this.timeout = timeout;
    this.maxRetries = maxRetries;

    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: this.timeout,
      headers: this.setupHeaders()
    });
  }

  /**
   * 기본 헤더 설정
   */
  private setupHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'User-Agent': 'TypeScript-APIClient/1.0'
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    return headers;
  }

  /**
   * HTTP 요청 실행 (재시도 포함)
   *
   * @param method - HTTP 메서드
   * @param endpoint - API 엔드포인트
   * @param config - axios 설정
   * @returns APIResponse 객체
   */
  private async makeRequest<T = any>(
    method: string,
    endpoint: string,
    config: AxiosRequestConfig = {}
  ): Promise<APIResponse<T>> {
    const url = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    let lastError: Error | null = null;
    let response: AxiosResponse | null = null;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        console.log(`${method} ${this.baseUrl}${url} (시도 ${attempt + 1}/${this.maxRetries})`);

        response = await this.client.request({
          method,
          url,
          ...config
        });

        // 성공 또는 클라이언트 오류는 재시도 안 함
        if (response.status < 500) {
          break;
        }

        // 서버 오류는 재시도
        if (attempt < this.maxRetries - 1) {
          const waitTime = Math.pow(2, attempt) * 1000; // 지수 백오프 (밀리초)
          console.warn(`서버 오류 ${response.status}, ${waitTime / 1000}초 후 재시도`);
          await this.sleep(waitTime);
          continue;
        }
      } catch (error) {
        lastError = error as Error;

        if (axios.isAxiosError(error) && error.response) {
          response = error.response;

          // 클라이언트 오류는 재시도 안 함
          if (error.response.status < 500) {
            break;
          }
        }

        if (attempt < this.maxRetries - 1) {
          const waitTime = Math.pow(2, attempt) * 1000;
          console.warn(`요청 실패: ${error}, ${waitTime / 1000}초 후 재시도`);
          await this.sleep(waitTime);
          continue;
        } else {
          throw new APIError(`최대 재시도 횟수 초과: ${error}`, undefined);
        }
      }
    }

    if (!response) {
      throw new APIError('응답을 받지 못했습니다', undefined);
    }

    // 응답 처리
    const success = response.status >= 200 && response.status < 300;

    const apiResponse: APIResponse<T> = {
      statusCode: response.status,
      data: response.data,
      headers: response.headers as Record<string, string>,
      success
    };

    if (!success) {
      const errorMsg = `API 오류 ${response.status}: ${JSON.stringify(response.data)}`;
      console.error(errorMsg);
      throw new APIError(errorMsg, response.status);
    }

    return apiResponse;
  }

  /**
   * 지정된 시간만큼 대기
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * GET 요청
   *
   * @param endpoint - API 엔드포인트
   * @param params - 쿼리 파라미터
   * @returns APIResponse 객체
   */
  async get<T = any>(endpoint: string, params?: Record<string, any>): Promise<APIResponse<T>> {
    return this.makeRequest<T>('GET', endpoint, { params });
  }

  /**
   * POST 요청
   *
   * @param endpoint - API 엔드포인트
   * @param data - 요청 본문 데이터
   * @returns APIResponse 객체
   */
  async post<T = any>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.makeRequest<T>('POST', endpoint, { data });
  }

  /**
   * PUT 요청
   *
   * @param endpoint - API 엔드포인트
   * @param data - 요청 본문 데이터
   * @returns APIResponse 객체
   */
  async put<T = any>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.makeRequest<T>('PUT', endpoint, { data });
  }

  /**
   * PATCH 요청
   *
   * @param endpoint - API 엔드포인트
   * @param data - 요청 본문 데이터
   * @returns APIResponse 객체
   */
  async patch<T = any>(endpoint: string, data?: any): Promise<APIResponse<T>> {
    return this.makeRequest<T>('PATCH', endpoint, { data });
  }

  /**
   * DELETE 요청
   *
   * @param endpoint - API 엔드포인트
   * @returns APIResponse 객체
   */
  async delete<T = any>(endpoint: string): Promise<APIResponse<T>> {
    return this.makeRequest<T>('DELETE', endpoint);
  }
}

/**
 * 사용자 인터페이스
 */
interface User {
  id: number;
  name: string;
  username: string;
  email: string;
  address?: {
    street: string;
    suite: string;
    city: string;
    zipcode: string;
    geo: {
      lat: string;
      lng: string;
    };
  };
  phone?: string;
  website?: string;
  company?: {
    name: string;
    catchPhrase: string;
    bs: string;
  };
}

/**
 * 게시물 인터페이스
 */
interface Post {
  id: number;
  userId: number;
  title: string;
  body: string;
}

/**
 * 사용자 API 클라이언트 (예제)
 */
class UserAPIClient extends APIClient {
  /**
   * 사용자 정보 조회
   *
   * @param userId - 사용자 ID
   * @returns 사용자 정보
   */
  async getUser(userId: number): Promise<User> {
    const response = await this.get<User>(`/users/${userId}`);
    return response.data;
  }

  /**
   * 사용자 생성
   *
   * @param userData - 사용자 데이터
   * @returns 생성된 사용자 정보
   */
  async createUser(userData: Partial<User>): Promise<User> {
    const response = await this.post<User>('/users', userData);
    return response.data;
  }

  /**
   * 사용자 정보 수정
   *
   * @param userId - 사용자 ID
   * @param userData - 수정할 데이터
   * @returns 수정된 사용자 정보
   */
  async updateUser(userId: number, userData: Partial<User>): Promise<User> {
    const response = await this.put<User>(`/users/${userId}`, userData);
    return response.data;
  }

  /**
   * 사용자 삭제
   *
   * @param userId - 사용자 ID
   * @returns 삭제 성공 여부
   */
  async deleteUser(userId: number): Promise<boolean> {
    const response = await this.delete(`/users/${userId}`);
    return response.success;
  }

  /**
   * 사용자 목록 조회
   *
   * @param page - 페이지 번호
   * @param perPage - 페이지당 항목 수
   * @returns 사용자 목록
   */
  async listUsers(page: number = 1, perPage: number = 10): Promise<User[]> {
    const params = { _page: page, _limit: perPage };
    const response = await this.get<User[]>('/users', params);
    return response.data;
  }
}

/**
 * Rate limiting 데코레이터
 */
function rateLimited(minIntervalMs: number = 1000) {
  let lastCallTime = 0;

  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const currentTime = Date.now();
      const timeSinceLastCall = currentTime - lastCallTime;

      if (timeSinceLastCall < minIntervalMs) {
        const sleepTime = minIntervalMs - timeSinceLastCall;
        console.debug(`Rate limit: ${sleepTime / 1000}초 대기`);
        await new Promise(resolve => setTimeout(resolve, sleepTime));
      }

      const result = await originalMethod.apply(this, args);
      lastCallTime = Date.now();
      return result;
    };

    return descriptor;
  };
}

/**
 * 메인 실행 함수
 */
async function main(): Promise<number> {
  console.log('=== API 클라이언트 예제 (TypeScript) ===\n');

  // JSONPlaceholder API 사용 (무료 테스트 API)
  const baseUrl = 'https://jsonplaceholder.typicode.com';

  try {
    // 일반 API 클라이언트
    const client = new APIClient(baseUrl);

    // GET 요청 예제
    console.log('1. GET 요청 - 사용자 조회');
    const userResponse = await client.get<User>('/users/1');
    if (userResponse.success) {
      const user = userResponse.data;
      console.log(`   이름: ${user.name}`);
      console.log(`   이메일: ${user.email}`);
      console.log(`   도시: ${user.address?.city}\n`);
    }

    // GET 요청 with 파라미터
    console.log('2. GET 요청 with 파라미터 - 게시물 목록');
    const postsResponse = await client.get<Post[]>('/posts', { userId: 1 });
    if (postsResponse.success) {
      const posts = postsResponse.data;
      console.log(`   사용자 1의 게시물: ${posts.length}개`);
      console.log(`   첫 번째 게시물: ${posts[0].title}\n`);
    }

    // POST 요청 예제
    console.log('3. POST 요청 - 새 게시물 생성');
    const newPost: Partial<Post> = {
      title: '테스트 게시물',
      body: '이것은 테스트 게시물입니다.',
      userId: 1
    };
    const createResponse = await client.post<Post>('/posts', newPost);
    if (createResponse.success) {
      const createdPost = createResponse.data;
      console.log(`   생성된 게시물 ID: ${createdPost.id}`);
      console.log(`   제목: ${createdPost.title}\n`);
    }

    // PUT 요청 예제
    console.log('4. PUT 요청 - 게시물 수정');
    const updatedPost: Post = {
      id: 1,
      title: '수정된 게시물',
      body: '내용이 수정되었습니다.',
      userId: 1
    };
    const updateResponse = await client.put<Post>('/posts/1', updatedPost);
    if (updateResponse.success) {
      console.log(`   수정 완료: ${updateResponse.data.title}\n`);
    }

    // DELETE 요청 예제
    console.log('5. DELETE 요청 - 게시물 삭제');
    const deleteResponse = await client.delete('/posts/1');
    if (deleteResponse.success) {
      console.log(`   삭제 완료 (상태 코드: ${deleteResponse.statusCode})\n`);
    }

    // 사용자 API 클라이언트 예제
    console.log('6. 전용 클라이언트 사용');
    const userClient = new UserAPIClient(baseUrl);

    const users = await userClient.listUsers(1, 3);
    console.log(`   사용자 목록: ${users.length}명`);
    users.forEach(user => {
      console.log(`   - ${user.name} (${user.email})`);
    });

    console.log('\nAPI 통신 완료!');

    return 0;
  } catch (error) {
    if (error instanceof APIError) {
      console.error(`API 오류: ${error.message}`);
      if (error.statusCode) {
        console.error(`상태 코드: ${error.statusCode}`);
      }
    } else if (error instanceof Error) {
      console.error(`예기치 않은 오류: ${error.message}`);
    }
    return 1;
  }
}

// 스크립트로 직접 실행될 때만 main 함수 실행
if (import.meta.url === `file://${process.argv[1]}`) {
  main().then(code => process.exit(code));
}

export { APIClient, UserAPIClient, APIError, APIResponse, User, Post };
