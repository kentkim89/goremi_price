import streamlit as st
from openai import OpenAI

# 🔑 API 키 설정 (secrets.toml 또는 직접 입력)
api_key = st.secrets["openai_api_key"] if "openai_api_key" in st.secrets else st.text_input("🔐 OpenAI API Key", type="password")

# OpenAI 클라이언트 생성
client = OpenAI(api_key=api_key)

# GPT에게 가격 제안 요청
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

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",  # ✅ 여기 변경됨
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return completion.choices[0].message.content

# Streamlit UI 구성
st.title("🧠 GPT 기반 가격 제안 시스템")
st.write("상품명을 입력하면 GPT가 시장 분석과 가격 전략을 제시합니다.")

product = st.text_input("📦 상품명 입력", placeholder="예: 타코와사비, 가니미소, 주꾸미볶음 등")

if st.button("🔍 가격 제안 받기") and product:
    with st.spinner("GPT가 분석 중입니다..."):
        try:
            result = get_price_recommendation(product)
            st.markdown("### 💡 GPT 분석 결과")
            st.markdown(result)
        except Exception as e:
            st.error(f"에러 발생: {e}")
