### 필요한 함수 임폴트
import os
import json
import pandas
import pickle
from dotenv import load_dotenv
import google.generativeai as generativeai
import pandas as pd
import random
import time
import json

# ### .env file 로드
load_dotenv()

### gemini key 불러오기기
gemini_api_key='AIzaSyCQwUC7057qWwXKkRRDefL-b7Xh0sPESOQ'
# gemini_api_key = os.getenv('GEMINI_API_KEY')
generativeai.configure(api_key=gemini_api_key)


# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel("gemini-1.5-flash")


### 리뷰 텍스트 전처리

# 파일 경로 설정
path="/Users/jihoyeom/Desktop/projects/zigzag/done/긴소매티셔츠/긴소매_p1_106711935.csv"


# DataFrame 생성
df = pd.read_csv(path)
columns = df.columns
print(f'컬럼 이름 : {columns}')

# 리뷰 텍스트 생성 (옵션1, 옵션2 포함)
review_text = df.loc[:, ['옵션1', '옵션2', '리뷰내용']].to_dict(orient="records")


### 감성 분석 및 근거가 되는 keyword 추출 함수 정의
def analyze_review(record):
    # 옵션1, 옵션2, 리뷰내용 추출
    option1 = record.get("옵션1", "")
    option2 = record.get("옵션2", "")
    review = record.get("리뷰내용", "")
# Prompt 생성
    prompt = f"""
    다음은 의류에 관한 소비자 리뷰입니다. 리뷰에서 중요한 키워드만 추출하여 아래 카테고리에 맞게 분류해주세요. 

    리뷰: "{review}"
    옵션1: "{option1}"
    옵션2: "{option2}"

    1. 재질 키워드:
       - 재질 관련: 탄성, 두께감, 부드러움 등과 관련된 키워드.
    2. 핏 키워드:
       - 통 관련: 타이트, 오버핏, 목끼임 등과 관련된 키워드.
       - 길이 관련: 소매 길이, 기장, 어깨 길이 등과 관련된 키워드.
    3. 가격 키워드:
       - 가격 대비 만족도와 관련된 키워드.
    4. 활용도 키워드:
       - 이너, 내복, 아우터와 관련된 키워드.
    5. 스타일링 키워드:
       - 후줄근, 여리여리 등과 관련된 키워드.
    6. 추천 키워드:
       - 추천 여부와 관련된 키워드.

    출력 형식:
    {{
    "리뷰" : {review},
    "옵션1/2" : {option1} / {option2},
    "재질_키워드": ["키워드1", "키워드2", ...],
    "핏_키워드": {{
    "통": ["키워드1", "키워드2", ...],
    "길이": ["키워드1", "키워드2", ...]
    }},
    "가격_키워드": ["키워드1", "키워드2", ...],
    "활용도_키워드": ["키워드1", "키워드2", ...],
    "스타일링_키워드": ["키워드1", "키워드2", ...],
    "추천_키워드": ["키워드1", "키워드2", ...]
    }}
    """

                    
    try:
        # 텍스트 분석 결과 생성
        model = generativeai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(contents=[prompt])
        
        if response:
            text_response = response.text
            try:
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
            except (ValueError, json.JSONDecodeError) as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"Gemini API 텍스트 응답: {text_response}")  # 전체 텍스트 응답 출력
                return None
        else:
            print("Gemini API 응답에 텍스트가 없습니다.")
            print(f"Gemini API 전체 응답: {response}")
            return None
    except Exception as e:
        print(f"Gemini API 호출 오류: {e}")
        return None

### 전체 텍스트를 처리하는 함수 정의
def process_multiple_texts(text_records):
    results = {}
    for i, record in enumerate(text_records):
        retry_count = 0
        max_retries = 5  # 최대 재시도 횟수
        wait_time = 1  # 초기 대기 시간 (초)

        while retry_count < max_retries:
            print(f"텍스트 {i+1} 처리 시도 {retry_count + 1}...")
            result = analyze_review(record)
            if result:
                results[f"텍스트 {i+1}"] = result
                break  # 성공 시 루프 종료
            else:
                retry_count += 1
                wait_time = wait_time * 2 + random.uniform(0, 1)  # 지수 백오프 + 약간의 임의 시간 추가
                print(f"API 요청 실패. {wait_time:.2f}초 후 재시도...")
                time.sleep(wait_time)
        else:  # 최대 재시도 횟수 초과 시
            results[f"텍스트 {i+1}"] = "감정 키워드 추출 실패 (최대 재시도 횟수 초과)"
    return results

# 여러 텍스트 처리
all_results = process_multiple_texts(review_text[:10])

# JSON 파일로 저장
with open('/Users/jihoyeom/Desktop/projects/zigzag/done/review_analysis.json', 'w', encoding='utf-8-sig') as fw:
    json.dump(all_results, fw, ensure_ascii=False, indent=4)

print("결과가 JSON 형식으로 저장되었습니다.")

# 저장된 결과를 다시 불러오기
with open('/Users/jihoyeom/Desktop/projects/zigzag/done/review_analysis.json', 'r', encoding='utf-8-sig') as fr:
    loaded_data = json.load(fr)

print(f'리뷰 데이터 분석의 결과 : \n{loaded_data}')