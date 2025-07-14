import streamlit as st

# 요소별 점수표
competition_margin = {"낮음": 0.04, "보통": 0.02, "높음": -0.02}
demand_margin = {"높음": 0.04, "보통": 0.02, "낮음": -0.02}
scale_margin = {"소량": 0.04, "중간": 0.02, "대량": -0.02}
production_margin = {"적음": 0.04, "중간": 0.02, "높음": -0.01}
ingredient_margin = {"예": -0.03, "아니오": 0.00}
retail_margin = {"예": 0.04, "아니오": 0.00}

# 예상 마진율 계산 함수
def calc_expected_margin(competition, demand, scale, prod_scale, ingredient, retail):
    base_margins = [
        competition_margin[competition],
        demand_margin[demand],
        scale_margin[scale],
        production_margin[prod_scale],
        ingredient_margin[ingredient],
        retail_margin[retail],
    ]
    margin = sum(base_margins)
    return round(margin, 4)

# UI
st.title("📊 고래미 신제품 마진 시뮬레이터")

col1, col2 = st.columns(2)

with col1:
    competition = st.selectbox("1. 경쟁강도", ["낮음", "보통", "높음"])
    demand = st.selectbox("2. 수요예상", ["높음", "보통", "낮음"])
    prod_scale = st.selectbox("3. 하루 생산량", ["적음", "중간", "높음"])
    ingredient = st.radio("4. 식자재용인가요?", ["예", "아니오"])

with col2:
    scale = st.selectbox("5. 생산규모", ["소량", "중간", "대량"])
    retail = st.radio("6. 리테일용(소매 판매용)인가요?", ["예", "아니오"])

# 예상 마진율 계산
expected_margin = calc_expected_margin(competition, demand, scale, prod_scale, ingredient, retail)

st.subheader("📈 예상 마진율")
st.metric("예상 마진율", f"{expected_margin * 100:.1f} %")

# 가격 계산기
st.markdown("---")
st.subheader("💰 도매/소비자 단가 계산기 (부가세 별도 기준)")

cogs = st.number_input("1. 제조원가 (부가세 별도, ₩)", min_value=0.0, step=10.0)
input_margin = st.number_input("2. 적용할 마진율 (%)", min_value=0.0, max_value=100.0, value=expected_margin * 100)

if cogs > 0 and input_margin > 0:
    margin_ratio = input_margin / 100
    wholesale_price = round(cogs / (1 - margin_ratio), -1)
    retail_price = round(wholesale_price * 1.5, -1) if retail == "예" else round(wholesale_price * 1.2, -1)

    st.metric("권장 도매 단가 (₩)", f"{wholesale_price:,.0f}")
    st.metric("권장 소비자 가격 (₩)", f"{retail_price:,.0f}")
else:
    st.info("제조원가와 적용 마진율을 입력해주세요.")
