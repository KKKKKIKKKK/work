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

# ### .env file 로드
load_dotenv()

# 변수에 담으면 노출 위험도가 작음. 
### gemini key 불러오기기
# configure 환경설정에 api_key를 넣어주고 사용자 인식 
gemini_api_key = os.getenv('GEMINI_API_KEY')
generativeai.configure(api_key=gemini_api_key)

### 리뷰 텍스트 전처리

# 파일 경로 설정 불러오기 
path='sweatshirt_review1.csv'

# 칼럼 이름만 확인하려고해서 필요없다... 
# DataFrame 생성
df = pd.read_csv(path)
columns = df.columns
print(f'컬럼 이름 : {columns}')

# '리뷰내용'을 리스트로 만든다.
# '리뷰 텍스트' 생성
review_text = df.loc[:, '리뷰내용'].to_list()


### 감성 분석 및 근거가 되는 'keyword' 추출 함수 정의
def analyze_review(text_input):   
    # prompt 생성하는데 빨간색 전체 다... 
    prompt = f"""
    다음 텍스트는 의류에 관한 소비자 리뷰입니다. 해당 리뷰의 내용이 긍정인지 부정인지를 분류를 하고, 판단의 근거가 되는 키워드들을 추출하여 JSON 형식으로 제시해 주세요.

    텍스트: {text_input}

    출력 형식 예시:
    {{
      "감성_분석_결과": "긍정" 또는 "부정",
      "정확도": 85,
      "판단_근거_키워드": {{
        "긍정": ["키워드1", "키워드2", ...],
        "부정": ["키워드1", "키워드2", ...],
        "중립_또는_기타": ["키워드1", "키워드2", ...]
      }}
    }}
    """
    
    # 모델 실행하기 전 예외처리 
    try:
        # 텍스트 분석 결과 생성성 
        model = generativeai.GenerativeModel('gemini-2.0-flash-exp')
        response=model.generate_content(
            contents=[prompt]
        )        
        if response:
            # print(f'키워드 추출의 결과 : {response.text}')
            text_response = response.text
            # print(type(text_response))
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
                print(f"Gemini API 텍스트 응답: {text_response}") # 전체 텍스트 응답 출력
                return None

        else:
            print("Gemini API 응답에 텍스트가 없습니다.")
            print(f"Gemini API 전체 응답: {response}")
            return None
        
    except Exception as e:
        print(f'Gemini API 호출 오류 : {e}')
        return None
    
### 전체 텍스트를 처리하는 함수 정의
#불규칙한 간격으로 하면 랜덤하게 줘서  api가 봇으로 판단하지 않는다... 
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
    
    # for i, text_input in enumerate(text_list):
    #     print(f"텍스트 {i+1} 처리 중...")
    #     result = analyze_review(text_input)
    #     if result:
    #         results[f"텍스트 {i+1}"] = result
    #     else:
    #         results[f"텍스트 {i+1}"] = "텍스트 분석 실패"  
    #     # 각 요청 사이에 1초 지연 추가
    #     time.sleep(1)
    return results

# 여러 텍스트 처리
all_results = process_multiple_texts(review_text[:10])

# 최종 결과 출력
print("결과 저장 중...")

# 결과를 JSON 파일로 저장
output_json_path = 'review_analysis_results.json'
with open(output_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(all_results, json_file, ensure_ascii=False, indent=4)

# 저장된 JSON 파일 경로 출력
print(f"리뷰 데이터 분석 결과가 JSON 파일로 저장되었습니다: {output_json_path}")


# # 여러 텍스트 처리
# all_results = process_multiple_texts(review_text[:10])

# # 최종 결과 출력
# # print(all_results)

# # 최종 결과를 dict 자료 구조로 변환
# with open('review_analysis.pkl', 'wb') as fw:
#     pickle.dump(all_results, fw) 

# # 저장된 결과를 다시 불러오기
# #딕셔너리로 저장해서 데이터프레임으로만들던..적절한전처리 후에 분석하면 된다.
# #리뷰가 긍정/부정인지/ 판단근거가 긍정이 많으면 긍정으로 뷴류.. 
# # 호출시 콜수가 정해짐. 1000번.  csv파일을 챗한테주고.     다음 텍스트는 의류에 관한 소비자 리뷰입니다. 해당 리뷰의 내용이 긍정인지 부정인지를 분류를 하고, 판단의 근거가 되는 키워드들을 추출하여 JSON 형식으로 제시해 주세요.
# # 
# with open('review_analysis.pkl', 'rb') as fr:
#     loaded_data = pickle.load(fr) 

# print(f'리뷰 데이터 분석의 결과 : \n{loaded_data}')
