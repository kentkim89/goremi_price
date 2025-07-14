import streamlit as st
import requests
from bs4 import BeautifulSoup

def crawl_naver_shopping_bs(query, max_items=15):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    url = f"https://search.shopping.naver.com/search/all?query={query}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.select("div.product_info_area")
    results = []

    for item in items[:max_items]:
        name_tag = item.select_one("a.product_link")
        price_tag = item.select_one("span.price_num")
        if name_tag and price_tag:
            name = name_tag.get_text(strip=True)
            price_text = price_tag.get_text(strip=True).replace(",", "").replace("원", "")
            try:
                price = int(price_text)
                results.append((name, price))
            except:
                continue
    return results

def classify_competition(product_count, brand_count):
    if product_count >= 20 and brand_count >= 5:
        return "높음", 0.30
    elif product_count >= 10:
        return "보통", 0.40
    else:
        return "낮음", 0.55

def average(prices):
    return sum(prices) / len(prices) if prices else 0

def extract_brands(names):
    return list(set([name.split()[0] for name in names]))

# Streamlit App
st.title("🧠 실시간 제품 분석 & 마진율 제안기 (Cloud 버전)")

query = st.text_input("제품명을 입력하세요", value="타코와사비")

if query:
    with st.spinner("🔍 네이버에서 검색 중..."):
        try:
            results = crawl_naver_shopping_bs(query)
        except Exception as e:
            st.error(f"❌ 크롤링 실패: {e}")
            st.stop()

    if results:
        names, prices = zip(*results)
        brands = extract_brands(names)
        avg_price = average(prices)
        product_count = len(prices)
        brand_count = len(brands)
        competition, margin = classify_competition(product_count, brand_count)

        st.markdown("### 📊 AI 요약")
        st.write(f"• 총 상품 수: {product_count}개")
        st.write(f"• 브랜드 수: {brand_count}개")
        st.write(f"• 평균 가격: {avg_price:,.0f}원")
        st.write(f"• 주요 브랜드 예시: {', '.join(brands[:5])}")

        st.metric("경쟁강도", competition)
        st.metric("제안 마진율", f"{margin*100:.1f}%")

        st.markdown("---")
        st.markdown("### 💰 가격 계산기 (부가세 별도 기준)")

        cogs = st.number_input("제조원가 (₩)", min_value=0.0, step=10.0)

        if cogs > 0:
            margin_ratio = margin
            wholesale = round(cogs / (1 - margin_ratio), -1)
            retail = round(wholesale * 1.5, -1)

            st.metric("도매가", f"{wholesale:,.0f} ₩")
            st.metric("소비자가", f"{retail:,.0f} ₩")
    else:
        st.warning("🔍 검색 결과가 충분하지 않습니다. 다른 키워드를 시도해보세요.")
