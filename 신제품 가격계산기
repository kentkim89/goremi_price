import streamlit as st

# --- 요소별 마진 점수표 ---
competition_margin = {"독점": 0.35, "니치": 0.25, "레드오션": 0.15}
elasticity_margin = {"비탄력": 0.30, "중간": 0.22, "탄력": 0.12}
scale_margin = {"소량": 0.40, "중간": 0.25, "대량": 0.10}
brand_margin = {"있음": 0.05, "없음": 0.00}
production_margin = {"적음": 0.04, "중간": 0.02, "높음": -0.01}
ingredient_margin = {"예": -0.03, "아니오": 0.00}
retail_margin = {"예": 0.04, "아니오": 0.00}

# --- 마진 계산 함수 ---
def calc_margin(competition, elasticity, scale, brand, promo, target_roi, prod_scale, ingredient, retail):
    base_margins = [
        competition_margin[competition],
        elasticity_margin[elasticity],
        scale_margin[scale],
        brand_margin[brand],
        production_margin[prod_scale],
        ingredient_margin[ingredient],
        retail_margin[retail],
    ]
    margin = sum(base_margins) / len(base_margins)

    if promo:
        margin -= 0.03  # 프로모션 감점

    if margin < (target_roi / 100):
        margin = target_roi / 100

    return round(margin, 4)

# --- Streamlit UI ---
st.title("📊 고래미 신제품 가격 계산기")

cogs = st.number_input("1. 제조원가 (₩)", min_value=0.0, step=10.0)

col1, col2 = st.columns(2)

with col1:
    competition = st.selectbox("2. 경쟁강도", ["독점", "니치", "레드오션"])
    elasticity = st.selectbox("3. 수요탄력성", ["비탄력", "중간", "탄력"])
    prod_scale = st.selectbox("6. 하루 생산량", ["적음", "중간", "높음"])
    ingredient = st.radio("7. 식자재용인가요?", ["예", "아니오"])

with col2:
    scale = st.selectbox("4. 생산규모", ["소량", "중간", "대량"])
    brand = st.selectbox("5. 브랜드 프리미엄", ["있음", "없음"])
    retail = st.radio("8. 리테일용(소매 판매용)인가요?", ["예", "아니오"])

promo = st.checkbox("9. 런칭 프로모션 적용")
target_roi = st.slider("10. 목표 마진율 (ROI 기준, %)", 5, 50, 20)

if cogs > 0:
    margin = calc_margin(competition, elasticity, scale, brand, promo, target_roi, prod_scale, ingredient, retail)
    wholesale_price = round(cogs / (1 - margin), -1)
    retail_price = round(wholesale_price * 1.5, -1) if retail == "예" else round(wholesale_price * 1.2, -1)

    st.subheader("📈 계산 결과")
    st.metric("예상 마진율", f"{margin*100:.1f} %")
    st.metric("권장 도매 단가", f"{wholesale_price:,.0f} ₩")
    st.metric("권장 소비자 가격", f"{retail_price:,.0f} ₩")

else:
    st.warning("제조원가를 입력하면 가격이 계산됩니다.")
