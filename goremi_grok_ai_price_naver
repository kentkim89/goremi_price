import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from typing import Dict

# Naver API endpoints
SEARCH_API_URL = "https://openapi.naver.com/v1/search/shop.json"  # For competition analysis (number of similar products)
TREND_API_URL = "https://openapi.naver.com/v1/datalab/search"  # Search trend for popularity and demand
SHOPPING_INSIGHT_URL = "https://openapi.naver.com/v1/datalab/shopping/categories"  # Shopping insights for demand and competition

def get_naver_headers(client_id: str, client_secret: str) -> Dict[str, str]:
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

def analyze_product_competitiveness(product_name: str, client_id: str, client_secret: str) -> Dict[str, float]:
    """
    Analyze product competitiveness using Naver APIs.
    - Rarity: Inversely proportional to number of search results (low results = high rarity)
    - Popularity: Average ratio from search trend API
    - Demand: Average click share from shopping insight API
    - Competition: Number of competitors from shop search API (normalized)
    Scores normalized between 0 and 1.
    """
    headers = get_naver_headers(client_id, client_secret)
    scores = {"rarity": 0.5, "popularity": 0.5, "demand": 0.5, "competition": 0.5}  # Defaults

    # Calculate dates: last 1 year
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    try:
        # 1. Search API for competition (shop search)
        search_params = {"query": product_name, "display": 100}  # Max 100 results
        response = requests.get(SEARCH_API_URL, headers=headers, params=search_params)
        if response.status_code == 200:
            data = response.json()
            total_results = data.get("total", 0)
            # Competition: higher total = higher competition (normalize: 0-1, assume max 10000)
            scores["competition"] = min(total_results / 10000, 1.0)
            # Rarity: inverse of competition
            scores["rarity"] = 1 - scores["competition"]

        # 2. Datalab Search Trend for popularity
        trend_body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "month",
            "keywordGroups": [{"groupName": product_name, "keywords": [product_name]}]
        }
        response = requests.post(TREND_API_URL, headers=headers, json=trend_body)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [{}])[0].get("data", [])
            if results:
                avg_ratio = sum(item["ratio"] for item in results) / len(results)
                # Popularity: normalize ratio (assume max ratio 100)
                scores["popularity"] = min(avg_ratio / 100, 1.0)

        # 3. Datalab Shopping Insight for demand
        insight_body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "month",
            "category": [{"name": product_name, "param": ["50000000"]}],  # Example category ID; adjust based on product (50000000: 패션의류 등)
            "device": "",
            "ages": [],
            "gender": ""
        }
        response = requests.post(SHOPPING_INSIGHT_URL, headers=headers, json=insight_body)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [{}])[0].get("data", [])
            if results:
                avg_click = sum(item["clickCount"] for item in results if "clickCount" in item) / len(results)
                # Demand: normalize (assume max 100000 clicks)
                scores["demand"] = min(avg_click / 100000, 1.0)

    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {str(e)}")

    return scores

def suggest_margin(analysis: Dict[str, float]) -> float:
    """
    Suggest a margin based on analysis.
    Simple formula: margin = (rarity + popularity + demand - competition) / 4 * 50%
    This gives a margin percentage between 0% and 50%.
    Customize this formula based on your company's needs.
    """
    avg_score = (analysis["rarity"] + analysis["popularity"] + analysis["demand"] - analysis["competition"]) / 4
    margin = avg_score * 50  # In percentage
    return max(10, min(40, margin))  # Clamp between 10% and 40% for realism

# Streamlit App
st.title("AI 신제품 마진 제안 시스템 (Naver API 기반)")

st.write("""
이 앱은 Naver API(검색, 데이터랩 검색어 트렌드, 데이터랩 쇼핑 인사이트)를 사용하여 신제품의 경쟁력을 분석하고 마진을 제안합니다.
제품 이름을 입력하세요. 예: 타코와사비
""")

# Sidebar for API credentials
st.sidebar.header("Naver API 인증 정보")
client_id = st.sidebar.text_input("클라이언트 ID (X-Naver-Client-Id)", type="password")
client_secret = st.sidebar.text_input("클라이언트 시크릿 (X-Naver-Client-Secret)", type="password")

product_name = st.text_input("제품 이름 입력:")

if st.button("분석 및 마진 제안"):
    if not product_name:
        st.warning("제품 이름을 입력해주세요.")
    elif not client_id or not client_secret:
        st.warning("Naver API 클라이언트 ID와 시크릿을 입력해주세요. (https://developers.naver.com/apps 에서 발급)")
    else:
        with st.spinner("제품 경쟁력 분석 중 (Naver API 호출)..."):
            analysis = analyze_product_competitiveness(product_name, client_id, client_secret)
        
        st.subheader("분석 결과")
        st.write(f"희소성 (rarity): {analysis['rarity']:.2f}")
        st.write(f"인기 (popularity): {analysis['popularity']:.2f}")
        st.write(f"수요 (demand): {analysis['demand']:.2f}")
        st.write(f"경쟁사 (competition): {analysis['competition']:.2f}")
        
        margin = suggest_margin(analysis)
        st.subheader("제안 마진")
        st.write(f"추천 마진율: {margin:.1f}%")
        
        st.info("""
        **참고:** 
        - 분석은 Naver API를 기반으로 하며, 실제 데이터에 따라 다를 수 있습니다.
        - 쇼핑 인사이트의 category param은 제품에 맞게 조정하세요 (현재 예시 ID 사용).
        - API 호출 제한(예: 1일 25,000회)이 있으니 주의하세요.
        - 더 정확한 분석을 위해 공식을 커스터마이징하세요.
        """)

# App footer
st.markdown("---")
st.write("회사 내부용 앱. 개발: [Your Name]. 버전: 2.0")
