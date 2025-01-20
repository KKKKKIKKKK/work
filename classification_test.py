### 필요한 함수 임폴트
import os
import json
import pandas as pd
from dotenv import load_dotenv
from collections import OrderedDict

import google.generativeai as generativeai
import random
import time

# ### .env file 로드
load_dotenv()

### gemini key 불러오기
gemini_api_key = os.getenv('GEMINI_API_KEY')
generativeai.configure(api_key=gemini_api_key)

### 리뷰 텍스트 전처리

# 파일 경로 설정
path = r'C:\Users\asia\Downloads\전체 파일 압축_win\긴소매티셔츠\긴소매_p1_106711935.csv'
print("파일 존재 여부:", os.path.exists(path))

# DataFrame 생성
df = pd.read_csv(path)
columns = df.columns
print(f'컬럼 이름 : {columns}')

# 리뷰 텍스트 생성
review_data = df[['옵션1', '옵션2', '리뷰내용']].dropna()

### 감성 분석 및 근거가 되는 keyword 추출 함수 정의
def analyze_review(option1_value, option2_value, review_value):   
    # prompt 생성
    prompt = f"""
    {review_value}    
    당신은 텍스트 감정분석 전문가입니다. 다음 질문에 정확하게 답변해야 합니다. 질문 : 다음 텍스트는 의류에 관한 소비자 리뷰입니다. 해당 리뷰의 내용이 긍정인지 부정인지를 분류를 하고, 판단의 근거가 되는 키워드들을 추출하여 JSON 파일로 저장해 주세요.

    리뷰내용: {review_value}
    옵션1: {option1_value}
    옵션2: {option2_value}

    출력 형식 예시:
    {{
      "리뷰내용": "{review_value}",
      "옵션1": "{option1_value}",
      "옵션2": "{option2_value}",
      "감성_분석_결과": "긍정" 또는 "부정",
      "정확도": 85,
      "판단_근거_키워드": {{
        "긍정": ["키워드1", "키워드2", ...],
        "부정": ["키워드1", "키워드2", ...],
        "중립_또는_기타": ["키워드1", "키워드2", ...]
      }}
    }}
    """
    try:
        # 텍스트 분석 결과 생성
        model = generativeai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(contents=[prompt])
        if response:
            # 결과 JSON 파싱
            text_response = response.text
            json_start = text_response.find('{')
            json_end = text_response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_output = text_response[json_start:json_end]
                parsed_json = json.loads(json_output)
                return parsed_json
            else:
                print("Gemini API 응답에서 JSON 형식을 찾을 수 없습니다.")
                print(f"Gemini API 텍스트 응답: {text_response}")
                return None
        else:
            print("Gemini API 응답에 텍스트가 없습니다.")
            return None
    except Exception as e:
        print(f'Gemini API 호출 오류 : {e}')
        return None

### 전체 텍스트를 처리하는 함수 정의
def process_multiple_texts(dataframe):
    results = {}
    for i, row in dataframe.iterrows():
        option1_value = row['옵션1']
        option2_value = row['옵션2']
        review_value = row['리뷰내용']
        retry_count = 0
        max_retries = 5  # 최대 재시도 횟수
        wait_time = 1  # 초기 대기 시간 (초)

        while retry_count < max_retries:
            print(f"텍스트 {i + 1} 처리 시도 {retry_count + 1}...")
            result = analyze_review(option1_value, option2_value, review_value)
            if result:
                results[f"텍스트 {i + 1}"] = result
                break  # 성공 시 루프 종료
            else:
                retry_count += 1
                wait_time = wait_time * 2 + random.uniform(0, 1)  # 지수 백오프 + 약간의 임의 시간 추가
                print(f"API 요청 실패. {wait_time:.2f}초 후 재시도...")
                time.sleep(wait_time)
        else:  # 최대 재시도 횟수 초과 시
            results[f"텍스트 {i + 1}"] = "감정 키워드 추출 실패 (최대 재시도 횟수 초과)"
    return results

# 여러 텍스트 처리
all_results = process_multiple_texts(review_data[:10])

# 최종 결과 출력
print("결과 저장 중...")

# 결과를 JSON 파일로 저장
output_json_path = 'review.json'
with open(output_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(all_results, json_file, ensure_ascii=False, indent=4)

# 저장된 JSON 파일 경로 출력
print(f"리뷰 데이터 분석 결과가 JSON 파일로 저장되었습니다: {output_json_path}")
