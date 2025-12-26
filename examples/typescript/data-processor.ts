/**
 * 데이터 처리 예제 (TypeScript)
 *
 * 이 모듈은 CSV/JSON 데이터를 처리하고 분석하는 기능을 제공합니다.
 * 네이티브 TypeScript와 간단한 유틸리티를 사용한 데이터 처리 예제입니다.
 *
 * 사용법:
 *   npm run processor
 *   또는
 *   tsx examples/data-processor.ts
 */

import { readFileSync, writeFileSync, existsSync, unlinkSync } from 'fs';
import { parse } from 'path';

/**
 * 데이터 요약 정보 인터페이스
 */
interface DataSummary {
  rows: number;
  columns: number;
  columnNames: string[];
  dtypes: Record<string, string>;
  missingValues: Record<string, number>;
}

/**
 * 통계 정보 인터페이스
 */
interface Statistics {
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  q25: number;
  q75: number;
}

/**
 * 데이터 처리 클래스
 */
class DataProcessor<T extends Record<string, any> = Record<string, any>> {
  private filePath: string;
  private data: T[] = [];
  private originalData: T[] = [];

  /**
   * 데이터 프로세서 초기화
   *
   * @param filePath - 처리할 데이터 파일 경로
   */
  constructor(filePath: string) {
    this.filePath = filePath;
  }

  /**
   * 파일에서 데이터를 로드합니다.
   *
   * @returns 로드된 데이터 배열
   * @throws Error - 파일이 존재하지 않거나 지원하지 않는 형식일 때
   */
  loadData(): T[] {
    if (!existsSync(this.filePath)) {
      throw new Error(`파일을 찾을 수 없습니다: ${this.filePath}`);
    }

    console.log(`데이터 로딩: ${this.filePath}`);

    try {
      const ext = parse(this.filePath).ext;
      const content = readFileSync(this.filePath, 'utf-8');

      if (ext === '.json') {
        this.data = JSON.parse(content);
      } else if (ext === '.csv') {
        this.data = this.parseCSV(content);
      } else {
        throw new Error(`지원하지 않는 파일 형식: ${ext}`);
      }

      // 원본 데이터 백업
      this.originalData = JSON.parse(JSON.stringify(this.data));
      console.log(`데이터 로드 완료: ${this.data.length}행, ${Object.keys(this.data[0] || {}).length}열`);

      return this.data;
    } catch (error) {
      console.error(`데이터 로드 실패: ${error}`);
      throw error;
    }
  }

  /**
   * CSV 문자열을 파싱합니다.
   */
  private parseCSV(content: string): T[] {
    const lines = content.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim());
    const rows: T[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const row: any = {};

      headers.forEach((header, index) => {
        const value = values[index];
        // 숫자 변환 시도
        const numValue = Number(value);
        row[header] = isNaN(numValue) ? value : numValue;
      });

      rows.push(row);
    }

    return rows;
  }

  /**
   * 데이터 요약 정보를 반환합니다.
   */
  getSummary(): DataSummary {
    if (this.data.length === 0) {
      throw new Error('데이터가 로드되지 않았습니다.');
    }

    const firstRow = this.data[0];
    const columnNames = Object.keys(firstRow);
    const dtypes: Record<string, string> = {};
    const missingValues: Record<string, number> = {};

    columnNames.forEach(col => {
      // 타입 추정
      const sampleValue = firstRow[col];
      dtypes[col] = typeof sampleValue;

      // 결측치 계산
      missingValues[col] = this.data.filter(
        row => row[col] === null || row[col] === undefined || row[col] === ''
      ).length;
    });

    return {
      rows: this.data.length,
      columns: columnNames.length,
      columnNames,
      dtypes,
      missingValues
    };
  }

  /**
   * 데이터를 정제합니다.
   *
   * @param options - 정제 옵션
   * @returns 정제된 데이터
   */
  cleanData(options: {
    dropDuplicates?: boolean;
    fillNa?: any;
    dropNa?: boolean;
  } = {}): T[] {
    if (this.data.length === 0) {
      throw new Error('데이터가 로드되지 않았습니다.');
    }

    console.log('데이터 정제 시작');
    const originalRows = this.data.length;

    // 중복 제거
    if (options.dropDuplicates) {
      const before = this.data.length;
      this.data = this.removeDuplicates(this.data);
      const removed = before - this.data.length;
      if (removed > 0) {
        console.log(`중복 행 제거: ${removed}개`);
      }
    }

    // 결측치 처리
    if (options.dropNa) {
      const before = this.data.length;
      this.data = this.data.filter(row => {
        return Object.values(row).every(
          val => val !== null && val !== undefined && val !== ''
        );
      });
      const removed = before - this.data.length;
      if (removed > 0) {
        console.log(`결측치가 있는 행 제거: ${removed}개`);
      }
    } else if (options.fillNa !== undefined) {
      this.data = this.data.map(row => {
        const newRow = { ...row };
        Object.keys(newRow).forEach(key => {
          if (newRow[key] === null || newRow[key] === undefined || newRow[key] === '') {
            newRow[key] = options.fillNa;
          }
        });
        return newRow;
      });
      console.log(`결측치를 '${options.fillNa}'로 채움`);
    }

    console.log(`데이터 정제 완료: ${originalRows}행 → ${this.data.length}행`);
    return this.data;
  }

  /**
   * 중복 행 제거
   */
  private removeDuplicates(data: T[]): T[] {
    const seen = new Set<string>();
    return data.filter(row => {
      const key = JSON.stringify(row);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  /**
   * 조건에 따라 데이터를 필터링합니다.
   *
   * @param conditions - 필터 조건
   * @returns 필터링된 데이터
   */
  filterData(conditions: Record<string, any>): T[] {
    if (this.data.length === 0) {
      throw new Error('데이터가 로드되지 않았습니다.');
    }

    let filtered = [...this.data];

    Object.entries(conditions).forEach(([column, condition]) => {
      if (typeof condition === 'object' && !Array.isArray(condition)) {
        // 비교 연산자 조건
        Object.entries(condition).forEach(([operator, value]) => {
          filtered = filtered.filter(row => {
            const cellValue = row[column];
            switch (operator) {
              case '>=': return cellValue >= value;
              case '>': return cellValue > value;
              case '<=': return cellValue <= value;
              case '<': return cellValue < value;
              case '==': return cellValue === value;
              case '!=': return cellValue !== value;
              default: return true;
            }
          });
        });
      } else if (Array.isArray(condition)) {
        // 리스트에 포함된 값 필터
        filtered = filtered.filter(row => condition.includes(row[column]));
      } else {
        // 단일 값 필터
        filtered = filtered.filter(row => row[column] === condition);
      }
    });

    console.log(`필터링 결과: ${this.data.length}행 → ${filtered.length}행`);
    return filtered;
  }

  /**
   * 데이터를 그룹화하고 집계합니다.
   *
   * @param groupBy - 그룹화할 컬럼 배열
   * @param aggregations - 집계 함수 객체
   * @returns 집계된 데이터
   */
  aggregateData(
    groupBy: string[],
    aggregations: Record<string, 'sum' | 'mean' | 'count' | 'min' | 'max'>
  ): Record<string, any>[] {
    if (this.data.length === 0) {
      throw new Error('데이터가 로드되지 않았습니다.');
    }

    console.log(`데이터 집계: ${groupBy.join(', ')} 기준`);

    // 그룹화
    const groups = new Map<string, T[]>();

    this.data.forEach(row => {
      const key = groupBy.map(col => row[col]).join('|');
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(row);
    });

    // 집계
    const result: Record<string, any>[] = [];

    groups.forEach((rows, key) => {
      const aggregated: Record<string, any> = {};

      // 그룹 키 복원
      const keyValues = key.split('|');
      groupBy.forEach((col, i) => {
        aggregated[col] = keyValues[i];
      });

      // 집계 함수 적용
      Object.entries(aggregations).forEach(([col, func]) => {
        const values = rows.map(row => Number(row[col])).filter(v => !isNaN(v));

        switch (func) {
          case 'sum':
            aggregated[col] = values.reduce((a, b) => a + b, 0);
            break;
          case 'mean':
            aggregated[col] = values.reduce((a, b) => a + b, 0) / values.length;
            break;
          case 'count':
            aggregated[col] = values.length;
            break;
          case 'min':
            aggregated[col] = Math.min(...values);
            break;
          case 'max':
            aggregated[col] = Math.max(...values);
            break;
        }
      });

      result.push(aggregated);
    });

    return result;
  }

  /**
   * 처리된 데이터를 저장합니다.
   *
   * @param outputPath - 저장할 파일 경로
   * @param format - 파일 형식
   */
  saveData(outputPath: string, format: 'csv' | 'json' = 'csv'): void {
    if (this.data.length === 0) {
      throw new Error('저장할 데이터가 없습니다.');
    }

    console.log(`데이터 저장: ${outputPath}`);

    try {
      if (format === 'json') {
        writeFileSync(outputPath, JSON.stringify(this.data, null, 2), 'utf-8');
      } else if (format === 'csv') {
        const csv = this.toCSV(this.data);
        writeFileSync(outputPath, csv, 'utf-8');
      } else {
        throw new Error(`지원하지 않는 형식: ${format}`);
      }

      console.log(`저장 완료: ${outputPath}`);
    } catch (error) {
      console.error(`저장 실패: ${error}`);
      throw error;
    }
  }

  /**
   * 데이터를 CSV 문자열로 변환
   */
  private toCSV(data: T[]): string {
    if (data.length === 0) return '';

    const headers = Object.keys(data[0]);
    const rows = data.map(row =>
      headers.map(h => row[h]).join(',')
    );

    return [headers.join(','), ...rows].join('\n');
  }

  /**
   * 현재 데이터 반환
   */
  getData(): T[] {
    return this.data;
  }
}

/**
 * 지정된 컬럼들의 통계를 계산합니다.
 */
function calculateStatistics(
  data: Record<string, any>[],
  columns: string[]
): Record<string, Statistics> {
  const stats: Record<string, Statistics> = {};

  columns.forEach(col => {
    const values = data
      .map(row => Number(row[col]))
      .filter(v => !isNaN(v))
      .sort((a, b) => a - b);

    if (values.length === 0) return;

    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / values.length;

    // 표준편차
    const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
    const std = Math.sqrt(variance);

    // 중앙값 및 사분위수
    const median = values[Math.floor(values.length / 2)];
    const q25 = values[Math.floor(values.length * 0.25)];
    const q75 = values[Math.floor(values.length * 0.75)];

    stats[col] = {
      mean,
      median,
      std,
      min: values[0],
      max: values[values.length - 1],
      q25,
      q75
    };
  });

  return stats;
}

/**
 * 메인 실행 함수
 */
async function main(): Promise<number> {
  console.log('=== 데이터 처리 예제 (TypeScript) ===\n');

  // 예제 데이터 생성
  const sampleData = [
    { name: '김철수', age: 25, city: '서울', sales: 100, quantity: 10 },
    { name: '이영희', age: 30, city: '부산', sales: 200, quantity: 20 },
    { name: '박민수', age: 35, city: '서울', sales: 150, quantity: 15 },
    { name: '김철수', age: 25, city: '서울', sales: 100, quantity: 10 },
    { name: '최지은', age: 28, city: '대전', sales: 180, quantity: 18 }
  ];

  // 임시 파일로 저장
  const tempFile = 'temp_data.json';
  writeFileSync(tempFile, JSON.stringify(sampleData, null, 2));

  try {
    // 데이터 프로세서 사용
    const processor = new DataProcessor(tempFile);
    processor.loadData();

    // 요약 정보
    const summary = processor.getSummary();
    console.log('데이터 요약:');
    console.log(`  행: ${summary.rows}, 열: ${summary.columns}`);
    console.log(`  컬럼: ${summary.columnNames.join(', ')}\n`);

    // 데이터 정제
    processor.cleanData({ dropDuplicates: true });
    console.log(`정제 후 데이터: ${processor.getData().length}행\n`);

    // 데이터 집계
    const aggregated = processor.aggregateData(
      ['city'],
      { sales: 'sum', quantity: 'mean' }
    );
    console.log('도시별 집계:');
    console.table(aggregated);

    // 통계 계산
    const stats = calculateStatistics(processor.getData(), ['age', 'sales']);
    console.log('\n통계 정보:');
    Object.entries(stats).forEach(([col, stat]) => {
      console.log(`  ${col}:`);
      console.log(`    평균: ${stat.mean.toFixed(2)}`);
      console.log(`    중앙값: ${stat.median.toFixed(2)}`);
      console.log(`    범위: ${stat.min.toFixed(2)} ~ ${stat.max.toFixed(2)}\n`);
    });

    // 결과 저장
    const outputFile = 'processed_data.json';
    processor.saveData(outputFile, 'json');
    console.log(`처리된 데이터 저장: ${outputFile}`);

    // 임시 파일 정리
    unlinkSync(tempFile);
    unlinkSync(outputFile);

    console.log('\n처리 완료!');

    return 0;
  } catch (error) {
    if (error instanceof Error) {
      console.error(`처리 중 오류 발생: ${error.message}`);
    }
    return 1;
  }
}

// 스크립트로 직접 실행될 때만 main 함수 실행
if (import.meta.url === `file://${process.argv[1]}`) {
  main().then(code => process.exit(code));
}

export { DataProcessor, calculateStatistics, DataSummary, Statistics };
