import os
import json
import pandas as pd
import random
import time
from dotenv import load_dotenv
import google.generativeai as generativeai

# .env 파일 로드
load_dotenv()

# Gemini API 키 설정
gemini_api_key = os.getenv('GEMINI_API_KEY')
generativeai.configure(api_key=gemini_api_key)

# 파일 경로 설정
path = r'C:\Users\asia\Desktop\work\긴소매티셔츠 copy\긴소매_p1_106711935.csv'
print("파일 존재 여부:", os.path.exists(path))

# DataFrame 생성
df = pd.read_csv(path)
columns = df.columns
print(f'컬럼 이름 : {columns}')

# 리뷰 텍스트 생성 (옵션1, 옵션2 포함)
review_text = df.loc[:, ['옵션1', '옵션2', '리뷰내용']].to_dict(orient="records")

# 감성 분석 및 근거가 되는 keyword 추출 함수 정의
def analyze_review(record):
    # 옵션1, 옵션2, 리뷰내용 추출
    option1 = record.get("옵션1", "")
    option2 = record.get("옵션2", "")
    review = record.get("리뷰내용", "")

    # 상품 이름(사이즈) 리스트
    product_names = [
        "피치기모_반팔 ver.",
        "피치기모_긴팔 ver.",
        "20수_기본ver.-F(44~66)",
        "20수_세미크롭 ver.-F(44~66)",
        "모달 ver.-F(44~66)",
        "쫀 ver.-F(44~66)"
    ]

    # 프롬프트 생성
    prompt = f"""
    당신은 텍스트 감정분석 전문가입니다. 
    아래는 의류에 관한 소비자 리뷰 데이터입니다. 
    각 리뷰에서 길이 분석과 관련된 모든 정보를 상세히 추출하고, 상품 이름을 기준으로 중요한 키워드를 분류하세요.

    리뷰: "{review}"
    옵션1: "{option1}"
    옵션2: "{option2}"
    상품 이름(사이즈): {product_names}

    ### 길이 관련 정보 추출 가이드

    길이 분석: 
    - 소매 길이: 리뷰에서 "길다", "짧다"와 같은 표현과 관련된 문장과 키워드.
    - 기장: "엉덩이를 덮음", "허리선에 맞음"과 같은 표현과 관련된 문장과 키워드.
    - 어깨 길이: "어깨가 크다", "어깨가 좁다"와 같은 표현과 관련된 문장과 키워드.
    - 리뷰에서 상품 이름과 연결된  소매길이, 기장, 어깨길이와 관련된 각 속성에 대한 키워드드와 근거 문장을 반드시 포함하세요.
    - 팔뚝부각과 같은 신체적 체형과 관련된 부분은 제거해주세요.
    - "이너, 레이어드와 같은 키워드는 소매 길이, 기장에 포함하지 마세요."
    


    출력 형식:
    {{
        "리뷰": "{review}",
        "옵션1/2": "{option1} / {option2}",
        "상품 이름": "{product_names}",
        "소매 길이": [
            {{
                "평가": "길다" 또는 "짧다",
                "근거 문장": "리뷰에서 해당 문장",
                "키워드": ["키워드1", "키워드2"]
            }}
        ],
        "기장": [
            {{
                "평가": "엉덩이 덮음" 또는 "허리선" 또는 "길다",
                "근거 문장": "리뷰에서 해당 문장",
                "키워드": ["키워드1", "키워드2"]
            }}
        ],
        "어깨 길이": [
            {{
                "평가": "길다" 또는 "짧다"" ,
                "근거 문장": "리뷰에서 해당 문장",
                "키워드": ["키워드1", "키워드2"]
            }}
        ]
    }}

    - 소매 길이는 "길다", "짧다"와 관련된 문장을 리뷰에서 상세히 추출하세요.
    - 기장은 "엉덩이 덮음", "허리선", "길다"와 같은 문장을 리뷰에서 상세히 추출하세요.
    - 어깨 길이는 "넓다", "좁다"와 관련된 문장을 리뷰에서 상세히 추출하세요.
    - 길이 관련 문장이 없으면 빈 배열([])을 반환하세요.
    ### 예시 출력:
    {{
        "리뷰": "소매가 너무 짧고, 기장은 엉덩이를 덮어 좋았습니다.",
        "옵션1/2": "스카이블루 / F(44~66)",
        "소매 길이": [
            {{
                "평가": "짧다",
                "근거 문장": "소매가 너무 짧고"
            }}
        ],
        "기장": [
            {{
                "평가": "엉덩이 덮음",
                "근거 문장": "기장은 엉덩이를 덮어 좋았습니다."
            }}
        ],
         "어깨 길이": [
            {{
                "평가": "좁다",
                "근거 문장": "어깨가 좀 좁게 나온 것 같긴 해요"
            }}
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
                print(f"Gemini API 텍스트 응답: {text_response}")
                return None
        else:
            print("Gemini API 응답에 텍스트가 없습니다.")
            return None
    except Exception as e:
        print(f"Gemini API 호출 오류: {e}")
        return None

# 전체 리뷰 데이터를 처리하는 함수 정의
def process_multiple_texts(text_records):
    results = {}
    for i, record in enumerate(text_records):
        retry_count = 0
        max_retries = 5
        wait_time = 1

        while retry_count < max_retries:
            print(f"텍스트 {i+1} 처리 시도 {retry_count + 1}...")
            result = analyze_review(record)
            if result:
                results[f"텍스트 {i+1}"] = result
                break
            else:
                retry_count += 1
                wait_time = wait_time * 2 + random.uniform(0, 1)
                print(f"API 요청 실패. {wait_time:.2f}초 후 재시도...")
                time.sleep(wait_time)
        else:
            results[f"텍스트 {i+1}"] = "감정 키워드 추출 실패 (최대 재시도 횟수 초과)"
    return results

# 리뷰 데이터 처리
all_results = process_multiple_texts(review_text[:1000])

# 결과 저장
output_json_path = 'review1000_analysis_results.json'
with open(output_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(all_results, json_file, ensure_ascii=False, indent=4)

print(f"리뷰 데이터 분석 결과가 JSON 파일로 저장되었습니다: {output_json_path}")
