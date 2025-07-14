import streamlit as st
import openai

# GPT API 키 설정
openai.api_key = "ff"  # 실제 키로 바꾸세요

# 상품 분석 함수
def get_price_recommendation(product_name):
    prompt = f"""
    상품명: {product_name}

    이 상품의 시장 경쟁 강도, 마진 구조, 적정 소비자 가격대를 GPT 데이터 기반으로 분석해줘.
    간단한 근거와 함께 아래의 형식으로 출력해줘.

    1. 경쟁강도: 낮음 / 중간 / 높음
    2. 마진구조: 하 / 중 / 상
    3. 적정 소비자 가격대 (B2C): ~ 원
    4. 적정 납품 가격대 (B2B): ~ 원
    5. 비고 및 전략 제안: 한 줄 정도
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response['choices'][0]['message']['content']

# Streamlit UI
st.title("🧠 GPT 기반 가격 제안 도우미")
product = st.text_input("상품명을 입력하세요 (예: 타코와사비, 가니미소 등)")

if st.button("가격 제안받기"):
    with st.spinner("GPT가 분석 중입니다..."):
        result = get_price_recommendation(product)
        st.markdown(result)
