import streamlit as st
from playwright.sync_api import sync_playwright

def crawl_naver_shopping(query, max_items=15):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://search.shopping.naver.com/search/all?query={query}")
        page.wait_for_timeout(3000)

        items = page.query_selector_all("div.product_info_area")[:max_items]
        for item in items:
            name_tag = item.query_selector("a.product_link")
            price_tag = item.query_selector("span.price_num")
            if name_tag and price_tag:
                name = name_tag.inner_text()
                price_text = price_tag.inner_text().replace(",", "").replace("원", "")
                try:
                    price = int(price_text)
                    results.append((name, price))
                except:
                    continue
        browser.close()
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

# Streamlit 앱 시작
st.title("🧠 실시간 제품 분석 & 마진율 제안기")

query = st.text_input("제품명을 입력하세요", value="타코와사비")

if query:
    with st.spinner("📡 실시간 시장 분석 중..."):
        try:
            results = crawl_naver_shopping(query)
        except:
            st.error("❌ 크롤링 실패. 인터넷 연결 또는 구조 변경 확인 필요.")
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
        st.warning("검색 결과가 부족하거나 상품이 존재하지 않습니다.")
