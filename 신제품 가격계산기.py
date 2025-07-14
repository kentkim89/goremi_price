import streamlit as st

# 요소별 점수표 (20~70% 범위 고려)
competition_margin = {"낮음": 0.10, "보통": 0.00, "높음": -0.10}
demand_margin = {"높음": 0.10, "보통": 0.00, "낮음": -0.10}
scale_margin = {"소량": 0.10, "중간": 0.00, "대량": -0.10}
production_margin = {"적음": 0.10, "중간": 0.00, "높음": -0.05}
ingredient_margin = {"예": -0.10, "아니오": 0.00}
retail_margin = {"예": 0.10, "아니오": 0.00}

BASE_MARGIN = 0.45  # 기준점 (45%)

def calc_suggested_margin(competition, demand, scale, prod_scale, ingredient, retail):
    adjustments = [
        competition_margin[competition],
        demand_margin[demand],
        scale_margin[scale],
        production_margin[prod_scale],
        ingredient_margin[ingredient],
        retail_margin[retail],
    ]
    margin = BASE_MARGIN + sum(adjustments)
    return round(min(max(margin, 0.20), 0.70), 4)

# UI 구성
st.title("📊 고래미 신제품 가격 제안 도구")

col1, col2 = st.columns(2)

with col1:
    competition = st.selectbox("1. 경쟁강도", ["낮음", "보통", "높음"])
    demand = st.selectbox("2. 수요예상", ["높음", "보통", "낮음"])
    prod_scale = st.selectbox("3. 하루 생산량", ["적음", "중간", "높음"])
    ingredient = st.radio("4. 식자재용인가요?", ["예", "아니오"])

with col2:
    scale = st.selectbox("5. 생산규모", ["소량", "중간", "대량"])
    retail = st.radio("6. 리테일용(소매 판매용)인가요?", ["예", "아니오"])

# 제안 마진율 계산
suggested_margin = calc_suggested_margin(competition, demand, scale, prod_scale, ingredient, retail)

st.subheader("📈 제안 마진율")
st.metric("제안 마진율", f"{suggested_margin * 100:.1f} %")

# 가격 계산
st.markdown("---")
st.subheader("💰 도매/소비자 단가 계산기 (부가세 별도 기준)")

cogs = st.number_input("1. 제조원가 (₩, VAT 별도)", min_value=0.0, step=10.0)
input_margin = st.number_input("2. 적용할 마진율 (%)", min_value=0.0, max_value=100.0, value=suggested_margin * 100)

if cogs > 0 and input_margin > 0:
    margin_ratio = input_margin / 100
    wholesale = round(cogs / (1 - margin_ratio), -1)
    retail_price = round(wholesale * 1.5, -1) if retail == "예" else round(wholesale * 1.2, -1)

    st.metric("권장 도매 단가 (VAT 별도)", f"{wholesale:,.0f} ₩")
    st.metric("권장 소비자 가격 (VAT 별도)", f"{retail_price:,.0f} ₩")
else:
    st.info("제조원가와 적용 마진율을 입력해주세요.")
