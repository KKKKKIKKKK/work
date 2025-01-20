### 필요한 라이브러리 / 함수 임폴트
import os
from dotenv import load_dotenv
from openai import OpenAI
from openai import OpenAIError
import google.generativeai as generativeai

import pandas as pd
import json
import time
import pickle
import random

### .env file 로드
load_dotenv()

### API Key 불러오기
openai_api_key = os.getenv('OPENAI_API_KEY')

### OpenAi 함수 호출
client = OpenAI(api_key=openai_api_key)

# 파일 경로 설정
path= r'C:\Users\asia\Desktop\work\긴소매티셔츠 copy\긴소매_p1_106711935.csv'
print("파일 존재 여부:", os.path.exists(path))

# DataFrame 생성
df = pd.read_csv(path)
# columns = df.columns
# print(f'컬럼 이름 : {columns}')

# 리뷰 텍스트 생성
review_text = df.loc[:, '리뷰내용'].to_list()

### 감성 분석 및 근거가 되는 keyword 추출 함수 정의
def analyze_review(text_input, output_filename="result.json"):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "당신은 이커머스 상품 중 의류에 대한 소비자 리뷰 분석의 전문가입니다."},
                {"role": "user", "content": f"""
                입력된 리뷰의 내용이 긍정적인지 부정적인지 분류하고, 판단의 근거가 되는 키워드들을 추출하여 아래의 JSON 형식으로 결과를 반환하세요. 정확도는 0부터 100 사이의 정수로 표현해주세요.

                {{
                  "감성_분석_결과": "긍정" 또는 "부정",
                  "정확도": 85, // 0부터 100 사이의 정수
                  "판단_근거_키워드": {{
                    "긍정": ["키워드1", "키워드2", ...],
                    "부정": ["키워드1", "키워드2", ...],
                    "중립_또는_기타": ["키워드1", "키워드2", ...]
                  }}
                }}

                리뷰: {text_input}
                """}
            ]
        )

        result_str = response.choices[0].message.content.strip()
        if result_str:
            # print(f'키워드 추출의 결과 : {response.text}')
            
            try:
                json_start = result_str.find('{')
                json_end = result_str.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_output = result_str[json_start:json_end]
                    parsed_json = json.loads(json_output)
                    return parsed_json
                else:
                    print("API 응답에서 JSON 형식을 찾을 수 없습니다.")
                    print(f"API 텍스트 응답: {result_str}")
                    return result_str

            except (ValueError, json.JSONDecodeError) as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"API 텍스트 응답: {result_str}") # 전체 텍스트 응답 출력
                return None

        else:
            print("API 응답에 텍스트가 없습니다.")
            print(f"API 전체 응답: {response}")
            return None
        
    except Exception as e:
        print(f'API 호출 오류 : {e}')
        return None
        # result = json.loads(result_str)

        # with open(output_filename, 'w', encoding='utf-8') as f:
        #     json.dump(result, f, indent=2, ensure_ascii=False)
        # print(f"결과가 {output_filename} 파일에 저장되었습니다.")
        # return result

    ### 전체 텍스트를 처리하는 함수 정의
def process_multiple_texts(text_list):
    results = {}    
    for i, text_input in enumerate(text_list):
        retry_count = 0
        max_retries = 5  # 최대 재시도 횟수
        wait_time = 1  # 초기 대기 시간 (초)

        while retry_count < max_retries:
            print(f"텍스트 {i+1} 처리 시도 {retry_count + 1}...")
            result = analyze_review(text_input)
            if result:
                results[f"텍스트 {i+1}"] = result
                break  # 성공 시 루프 종료
            else:
                retry_count += 1
                wait_time = wait_time * 2 + random.uniform(0, 1) # 지수 백오프 + 약간의 임의 시간 추가
                print(f"API 요청 실패. {wait_time:.2f}초 후 재시도...")
                time.sleep(wait_time)
        else: # 최대 재시도 횟수 초과 시
            results[f"텍스트 {i+1}"] = "감정 키워드 추출 실패 (최대 재시도 횟수 초과)"
    return results
    

# 여러 텍스트 처리
all_results = process_multiple_texts(review_text[:100])

# 최종 결과 출력
# print(all_results)

# 최종 결과를 dict 자료 구조로 변환
with open('review_analysis.pkl', 'wb') as fw:
    pickle.dump(all_results, fw) 

# 저장된 결과를 다시 불러오기
with open('review_analysis.pkl', 'rb') as fr:
    loaded_data = pickle.load(fr) 

print(f'리뷰 데이터 분석의 결과 : \n{loaded_data}')
