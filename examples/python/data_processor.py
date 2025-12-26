"""
데이터 처리 예제

이 모듈은 CSV/JSON 데이터를 처리하고 분석하는 기능을 제공합니다.
pandas를 사용한 데이터 처리 예제입니다.

사용법:
    python examples/data_processor.py
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """데이터 처리 클래스"""

    def __init__(self, file_path: str):
        """
        데이터 프로세서 초기화

        Args:
            file_path: 처리할 데이터 파일 경로
        """
        self.file_path = Path(file_path)
        self.df: Optional[pd.DataFrame] = None
        self.original_df: Optional[pd.DataFrame] = None

    def load_data(self) -> pd.DataFrame:
        """
        파일에서 데이터를 로드합니다.

        Returns:
            로드된 DataFrame

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 지원하지 않는 파일 형식일 때
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.file_path}")

        logger.info(f"데이터 로딩: {self.file_path}")

        try:
            if self.file_path.suffix == '.csv':
                self.df = pd.read_csv(self.file_path)
            elif self.file_path.suffix == '.json':
                self.df = pd.read_json(self.file_path)
            elif self.file_path.suffix in ['.xlsx', '.xls']:
                self.df = pd.read_excel(self.file_path)
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {self.file_path.suffix}")

            # 원본 데이터 백업
            self.original_df = self.df.copy()
            logger.info(f"데이터 로드 완료: {self.df.shape[0]}행, {self.df.shape[1]}열")
            return self.df

        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            raise

    def get_summary(self) -> Dict[str, Any]:
        """
        데이터 요약 정보를 반환합니다.

        Returns:
            요약 정보 딕셔너리
        """
        if self.df is None:
            raise ValueError("데이터가 로드되지 않았습니다.")

        summary = {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'column_names': self.df.columns.tolist(),
            'dtypes': self.df.dtypes.astype(str).to_dict(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'memory_usage': f"{self.df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        }

        return summary

    def clean_data(self,
                   drop_duplicates: bool = True,
                   fill_na: Optional[Any] = None,
                   drop_na: bool = False) -> pd.DataFrame:
        """
        데이터를 정제합니다.

        Args:
            drop_duplicates: 중복 행 제거 여부
            fill_na: 결측치를 채울 값 (None이면 채우지 않음)
            drop_na: 결측치가 있는 행 제거 여부

        Returns:
            정제된 DataFrame
        """
        if self.df is None:
            raise ValueError("데이터가 로드되지 않았습니다.")

        logger.info("데이터 정제 시작")
        original_rows = len(self.df)

        # 중복 제거
        if drop_duplicates:
            before = len(self.df)
            self.df = self.df.drop_duplicates()
            removed = before - len(self.df)
            if removed > 0:
                logger.info(f"중복 행 제거: {removed}개")

        # 결측치 처리
        if drop_na:
            before = len(self.df)
            self.df = self.df.dropna()
            removed = before - len(self.df)
            if removed > 0:
                logger.info(f"결측치가 있는 행 제거: {removed}개")
        elif fill_na is not None:
            self.df = self.df.fillna(fill_na)
            logger.info(f"결측치를 '{fill_na}'로 채움")

        logger.info(f"데이터 정제 완료: {original_rows}행 → {len(self.df)}행")
        return self.df

    def filter_data(self, conditions: Dict[str, Any]) -> pd.DataFrame:
        """
        조건에 따라 데이터를 필터링합니다.

        Args:
            conditions: 필터 조건 딕셔너리
                예: {'age': {'>=': 18, '<': 65}, 'city': ['서울', '부산']}

        Returns:
            필터링된 DataFrame
        """
        if self.df is None:
            raise ValueError("데이터가 로드되지 않았습니다.")

        filtered_df = self.df.copy()

        for column, condition in conditions.items():
            if column not in filtered_df.columns:
                logger.warning(f"컬럼이 존재하지 않음: {column}")
                continue

            if isinstance(condition, dict):
                # 비교 연산자 조건
                for operator, value in condition.items():
                    if operator == '>=':
                        filtered_df = filtered_df[filtered_df[column] >= value]
                    elif operator == '>':
                        filtered_df = filtered_df[filtered_df[column] > value]
                    elif operator == '<=':
                        filtered_df = filtered_df[filtered_df[column] <= value]
                    elif operator == '<':
                        filtered_df = filtered_df[filtered_df[column] < value]
                    elif operator == '==':
                        filtered_df = filtered_df[filtered_df[column] == value]
                    elif operator == '!=':
                        filtered_df = filtered_df[filtered_df[column] != value]
            elif isinstance(condition, list):
                # 리스트에 포함된 값 필터
                filtered_df = filtered_df[filtered_df[column].isin(condition)]
            else:
                # 단일 값 필터
                filtered_df = filtered_df[filtered_df[column] == condition]

        logger.info(f"필터링 결과: {len(self.df)}행 → {len(filtered_df)}행")
        return filtered_df

    def aggregate_data(self,
                      group_by: List[str],
                      aggregations: Dict[str, str]) -> pd.DataFrame:
        """
        데이터를 그룹화하고 집계합니다.

        Args:
            group_by: 그룹화할 컬럼 리스트
            aggregations: 집계 함수 딕셔너리
                예: {'sales': 'sum', 'quantity': 'mean'}

        Returns:
            집계된 DataFrame
        """
        if self.df is None:
            raise ValueError("데이터가 로드되지 않았습니다.")

        logger.info(f"데이터 집계: {group_by} 기준")
        result = self.df.groupby(group_by).agg(aggregations).reset_index()
        return result

    def add_calculated_column(self,
                            column_name: str,
                            calculation: str) -> pd.DataFrame:
        """
        계산된 컬럼을 추가합니다.

        Args:
            column_name: 새로운 컬럼 이름
            calculation: 계산 표현식 (예: 'price * quantity')

        Returns:
            컬럼이 추가된 DataFrame
        """
        if self.df is None:
            raise ValueError("데이터가 로드되지 않았습니다.")

        try:
            self.df[column_name] = self.df.eval(calculation)
            logger.info(f"계산 컬럼 추가: {column_name} = {calculation}")
            return self.df
        except Exception as e:
            logger.error(f"컬럼 계산 실패: {e}")
            raise

    def save_data(self, output_path: str, file_format: str = 'csv'):
        """
        처리된 데이터를 저장합니다.

        Args:
            output_path: 저장할 파일 경로
            file_format: 파일 형식 ('csv', 'json', 'excel')
        """
        if self.df is None:
            raise ValueError("저장할 데이터가 없습니다.")

        output_path = Path(output_path)
        logger.info(f"데이터 저장: {output_path}")

        try:
            if file_format == 'csv':
                self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif file_format == 'json':
                self.df.to_json(output_path, orient='records', force_ascii=False, indent=2)
            elif file_format == 'excel':
                self.df.to_excel(output_path, index=False)
            else:
                raise ValueError(f"지원하지 않는 형식: {file_format}")

            logger.info(f"저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"저장 실패: {e}")
            raise


def calculate_statistics(df: pd.DataFrame, columns: List[str]) -> Dict[str, Dict]:
    """
    지정된 컬럼들의 통계를 계산합니다.

    Args:
        df: DataFrame
        columns: 통계를 계산할 컬럼 리스트

    Returns:
        컬럼별 통계 딕셔너리
    """
    stats = {}

    for col in columns:
        if col not in df.columns:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            stats[col] = {
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'q25': float(df[col].quantile(0.25)),
                'q75': float(df[col].quantile(0.75)),
            }

    return stats


def main():
    """메인 실행 함수"""
    print("=== 데이터 처리 예제 ===\n")

    # 예제 데이터 생성
    sample_data = pd.DataFrame({
        'name': ['김철수', '이영희', '박민수', '김철수', '최지은'],
        'age': [25, 30, 35, 25, 28],
        'city': ['서울', '부산', '서울', '서울', '대전'],
        'sales': [100, 200, 150, 100, 180],
        'quantity': [10, 20, 15, 10, 18]
    })

    # 임시 파일로 저장
    temp_file = Path('temp_data.csv')
    sample_data.to_csv(temp_file, index=False)

    try:
        # 데이터 프로세서 사용
        processor = DataProcessor(temp_file)
        processor.load_data()

        # 요약 정보
        summary = processor.get_summary()
        print("데이터 요약:")
        print(f"  행: {summary['rows']}, 열: {summary['columns']}")
        print(f"  컬럼: {', '.join(summary['column_names'])}")
        print(f"  메모리: {summary['memory_usage']}\n")

        # 데이터 정제
        processor.clean_data(drop_duplicates=True)
        print(f"정제 후 데이터: {len(processor.df)}행\n")

        # 계산 컬럼 추가
        processor.add_calculated_column('total', 'sales * quantity')
        print("계산 컬럼 추가: total = sales * quantity\n")

        # 데이터 집계
        aggregated = processor.aggregate_data(
            group_by=['city'],
            aggregations={'sales': 'sum', 'quantity': 'mean'}
        )
        print("도시별 집계:")
        print(aggregated.to_string(index=False))
        print()

        # 통계 계산
        stats = calculate_statistics(processor.df, ['age', 'sales'])
        print("통계 정보:")
        for col, stat in stats.items():
            print(f"  {col}:")
            print(f"    평균: {stat['mean']:.2f}")
            print(f"    중앙값: {stat['median']:.2f}")
            print(f"    범위: {stat['min']:.2f} ~ {stat['max']:.2f}\n")

        # 결과 저장
        output_file = Path('processed_data.csv')
        processor.save_data(output_file, file_format='csv')
        print(f"처리된 데이터 저장: {output_file}")

        # 임시 파일 정리
        temp_file.unlink()
        output_file.unlink()

        print("\n처리 완료!")

    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
