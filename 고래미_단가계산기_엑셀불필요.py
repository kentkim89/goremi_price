
import streamlit as st

st.title("🧮 고래미 단가 자동 계산기")

# 입력 방식 선택
input_mode = st.radio("기준가 입력 방식 선택", ["판매가 기준", "도매가 기준"])

if input_mode == "판매가 기준":
    price = st.number_input("판매가를 입력하세요 (₩)", min_value=0)
    selling_price = price
    wholesale_price = round(selling_price * 0.58)
else:
    price = st.number_input("도매가를 입력하세요 (₩)", min_value=0)
    selling_price = round(price / 0.58)
    wholesale_price = price

# 계산
result = {
    "📦 판매가": selling_price,
    "🏢 사업자가(24%)": round(selling_price * 0.76),
    "🧾 도매가(42%)": wholesale_price,
    "📦 박스가(일반)": round(selling_price * 0.70),
    "📦 박스가(사업자)": round(selling_price * 0.60),
    "📦 박스가(도매)": round(selling_price * 0.52),
    "🏬 픽업가(일반)": round(selling_price * 0.60),
    "🏬 픽업가(사업자)": round(selling_price * 0.50),
    "🏬 픽업가(도매)": round(selling_price * 0.42),
}

# 출력
st.subheader("💰 계산 결과")
for label, value in result.items():
    st.write(f"{label}: {value:,} 원")
