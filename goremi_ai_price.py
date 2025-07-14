import streamlit as st

# [모의 요약 및 판단 함수]
def mock_ai_summary(product_name):
    if "타코와사비" in product_name:
        return {
            "summary": "네이버쇼핑에 20개 이상 제품 등록. 고래미, CJ, 다인푸드 등 다양한 브랜드 존재. 평균 가격대는 5,000~7,000원. 리뷰 상위 제품 1,000건 이상.",
            "competition": "높음",
            "suggested_margin": 0.30
        }
    elif "성게알" in product_name:
        return {
            "summary": "브랜드 다양성은 낮으며, 수입산 위주로 제품 수 5개 미만. 평균 가격대는 20,000~35,000원.",
            "competition": "낮음",
            "suggested_margin": 0.55
        }
    else:
        return {
            "summary": "중간 정도의 브랜드 수와 가격대 분포. 제품 수는 10~15개.",
            "competition": "보통",
            "suggested_margin": 0.40
        }

# Streamlit 시작
st.title("🔍 AI 기반 신제품 경쟁 분석 및 마진율 제안기")

product_name = st.text_input("신제품명을 입력하세요", placeholder="예: 타코와사비, 성게알 페이스트")

if product_name:
    result = mock_ai_summary(product_name)

    st.subheader("📄 온라인 시장 요약")
    st.write(result["summary"])

    st.subheader("📊 AI 판단 결과")
    st.metric("경쟁 강도", result["competition"])
    st.metric("제안 마진율", f"{result['suggested_margin'] * 100:.1f} %")

    st.markdown("---")
    st.subheader("💰 단가 계산기 (VAT 별도)")

    cogs = st.number_input("1. 제조원가 (₩)", min_value=0.0, step=10.0)
    use_ai_margin = st.checkbox("AI 제안 마진율 사용", value=True)

    if use_ai_margin:
        input_margin = result["suggested_margin"] * 100
    else:
        input_margin = st.number_input("2. 직접 마진율 입력 (%)", min_value=0.0, max_value=100.0, value=40.0)

    if cogs > 0:
        margin_ratio = input_margin / 100
        wholesale = round(cogs / (1 - margin_ratio), -1)
        retail_price = round(wholesale * 1.5, -1)

        st.metric("권장 도매 단가", f"{wholesale:,.0f} ₩")
        st.metric("권장 소비자 가격", f"{retail_price:,.0f} ₩")
