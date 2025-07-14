import streamlit as st
import requests
from bs4 import BeautifulSoup

# 🟡 네이버 쇼핑 크롤링 함수 (로컬에서만 작동)
def crawl_naver_shopping(query, max_items=10):
    url = f"https://search.shopping.naver.com/search/all?query={query}&cat_id=&frm=NVSHATC"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    items = soup.select("div.product_info_area")[:max_items]
    for item in items:
        title_tag = item.select_one("a.product_link")
        price_tag = item.select_one("span.price_num")

        if title_tag and price_tag:
            title = title_tag.get_text(strip=True)
            price_text = price_tag.get_text(strip=True).replace(",", "").replace("원", "")
            try:
                price = int(price_text)
                results.append((title, price))
            except:
                continue
    return results

# 🔵 경쟁강도 분석 및 마진율 제안
def classify_competition(product_count, brand_count):
    if product_count >= 20 and brand_count >= 5:
        return "높음", 0.30
    elif product_count >= 10:
        return "보통", 0.40
    else:
        return "낮음", 0.55

# 평균 계산
def avg_price(prices):
    return sum(prices) / len(prices) if prices else 0

# 브랜드명 추출 간단 처리
def extract_brands(titles):
    brands = []
    for title in titles:
        brand = title.split()[0]
        if brand not in brands:
            brands.append(brand)
    return brands

# 🟢 Streamlit 시작
st.title("🧠 실시간 AI 마진율 제안기 (네이버 쇼핑 기반)")

product_name = st.text_input("신제품명을 입력하세요", placeholder="예: 타코와사비, 성게알")

if product_name:
    with st.spinner("네이버 쇼핑에서 데이터 수집 중..."):
        try:
            crawled = crawl_naver_shopping(product_name, max_items=20)
        except:
            st.error("❌ 네이버 쇼핑 접속에 실패했습니다. 네트워크 또는 로컬 환경 확인 바랍니다.")
            st.stop()

    if crawled:
        titles = [t for t, p in crawled]
        prices = [p for t, p in crawled]
        brands = extract_brands(titles)
        product_count = len(crawled)
        brand_count = len(brands)
        avg = avg_price(prices)
        competition, suggested_margin = classify_competition(product_count, brand_count)

        st.subheader("🔍 시장 정보 요약")
        st.write(f"• 상품 수: {product_count}개")
        st.write(f"• 브랜드 수: {brand_count}개 ({', '.join(brands)})")
        st.write(f"• 평균 가격: {avg:,.0f}원")
        st.write(f"• 가격 예시: {', '.join([f'{p:,}원' for p in prices[:5]])}")

        st.subheader("📊 경쟁강도 및 제안 마진율")
        st.metric("경쟁강도", competition)
        st.metric("제안 마진율", f"{suggested_margin * 100:.1f} %")

        st.markdown("---")
        st.subheader("💰 단가 계산기 (부가세 별도 기준)")

        cogs = st.number_input("제조원가 (₩)", min_value=0.0, step=10.0)
        use_ai_margin = st.checkbox("AI 제안 마진율 사용", value=True)

        if use_ai_margin:
            input_margin = suggested_margin * 100
        else:
            input_margin = st.number_input("직접 마진율 입력 (%)", min_value=0.0, max_value=100.0, value=40.0)

        if cogs > 0:
            margin_ratio = input_margin / 100
            wholesale = round(cogs / (1 - margin_ratio), -1)
            retail_price = round(wholesale * 1.5, -1)

            st.metric("권장 도매 단가", f"{wholesale:,.0f} ₩")
            st.metric("권장 소비자 가격", f"{retail_price:,.0f} ₩")

    else:
        st.warning("검색 결과가 충분하지 않습니다. 다른 제품명을 시도해보세요.")
