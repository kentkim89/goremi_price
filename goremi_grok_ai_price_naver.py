import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Company brands
OUR_BRANDS = ["고래미", "씨포스트", "설래담"]

# Naver API endpoints
SEARCH_API_URL = "https://openapi.naver.com/v1/search/shop.json"
TREND_API_URL = "https://openapi.naver.com/v1/datalab/search"
SHOPPING_INSIGHT_URL = "https://openapi.naver.com/v1/datalab/shopping/categories"
BLOG_API_URL = "https://openapi.naver.com/v1/search/blog.json"
CAFE_API_URL = "https://openapi.naver.com/v1/search/cafearticle.json"

def get_naver_headers(client_id: str, client_secret: str) -> Dict[str, str]:
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

def analyze_product_competitiveness(product_name: str, client_id: str, client_secret: str, category_id: str = "50000008", fallback_mode: bool = False) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
    """
    Analyze using Naver APIs including blog and cafe. Return scores and categorized evidences (up to 50 total).
    Demand uses 'ratio' from shopping insight (click share percentage).
    Default category_id set to 50000008 for food products.
    """
    scores = {"rarity": 0.5, "popularity": 0.5, "demand": 0.5, "competition": 0.5}
    evidences = {
        "쇼핑 검색 결과": [],
        "검색 트렌드": [],
        "쇼핑 인사이트": [],
        "블로그 포스트": [],
        "카페 아티클": []
    }  # Categorized evidences

    if fallback_mode:
        scores["rarity"] = 0.7
        scores["popularity"] = 0.4
        scores["demand"] = 0.6
        scores["competition"] = 0.5
        evidences["추정 모드"] = [
            "신제품으로 가정하여 희소성 높음 (0.7)",
            "초기 인기 중간 수준 (0.4)",
            "시장 수요 성장 예상 (0.6)",
            "경쟁 중간 (0.5)"
        ]
        st.warning("데이터 부족으로 추정 모드 사용. 실제 데이터 입력 추천.")
        return scores, evidences

    headers = get_naver_headers(client_id, client_secret)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    api_success = True

    try:
        # 1. Shop Search API for competition and rarity
        search_params = {"query": product_name, "display": 100}
        response = requests.get(SEARCH_API_URL, headers=headers, params=search_params)
        if response.status_code == 200:
            data = response.json()
            total_results = data.get("total", 0)
            scores["competition"] = min(total_results / 10000, 1.0)
            scores["rarity"] = 1 - scores["competition"]
            # Evidences: top 15 shop items
            items = data.get("items", [])[:15]
            for item in items:
                label = "자사 제품" if any(brand in item['title'] for brand in OUR_BRANDS) else "경쟁 제품"
                evidences["쇼핑 검색 결과"].append(f"{label}: {item['title']} (링크: {item['link']})")
            # Fallback for demand if insight fails
            if total_results > 0:
                scores["demand"] = min(total_results / 5000, 1.0)  # Proxy: high search results imply demand
        else:
            api_success = False

        # 2. Datalab Search Trend for popularity (search volume)
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
                scores["popularity"] = min(avg_ratio / 100, 1.0)
                # Evidences: all monthly ratios (up to 12 for 1 year)
                for item in results:
                    evidences["검색 트렌드"].append(f"{item['period']} - 검색 비율 {item['ratio']}")
        else:
            api_success = False

        # 3. Datalab Shopping Insight for demand (use 'ratio' for click share)
        insight_body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "month",
            "category": [{"name": product_name, "param": [category_id]}] if category_id else [],
            "device": "",
            "ages": [],
            "gender": ""
        }
        response = requests.post(SHOPPING_INSIGHT_URL, headers=headers, json=insight_body)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [{}])[0].get("data", [])
            if results:
                avg_ratio = sum(item.get("ratio", 0) for item in results) / len(results)
                scores["demand"] = min(avg_ratio / 100, 1.0)  # ratio is click share percentage
                # Evidences: all click shares (up to 12)
                for item in results:
                    evidences["쇼핑 인사이트"].append(f"{item['period']} - 클릭 비율 {item.get('ratio', 'N/A')}")
        else:
            api_success = False
            # Fallback already set from shop total

        # 4. Blog Search for additional popularity/demand (reviews, mentions)
        blog_params = {"query": product_name, "display": 100}
        response = requests.get(BLOG_API_URL, headers=headers, params=blog_params)
        if response.status_code == 200:
            data = response.json()
            blog_total = data.get("total", 0)
            # Adjust popularity with blog mentions (proxy for buzz/reviews)
            scores["popularity"] = (scores["popularity"] + min(blog_total / 10000, 1.0)) / 2
            # Evidences: top 10 blog posts
            items = data.get("items", [])[:10]
            for item in items:
                evidences["블로그 포스트"].append(f"{item['title']} (링크: {item['link']})")
        else:
            api_success = False

        # 5. Cafe Search for additional demand (community discussions)
        cafe_params = {"query": product_name, "display": 100}
        response = requests.get(CAFE_API_URL, headers=headers, params=cafe_params)
        if response.status_code == 200:
            data = response.json()
            cafe_total = data.get("total", 0)
            # Adjust demand with cafe mentions (proxy for interest/purchases)
            scores["demand"] = (scores["demand"] + min(cafe_total / 10000, 1.0)) / 2
            # Evidences: top 10 cafe articles
            items = data.get("items", [])[:10]
            for item in items:
                evidences["카페 아티클"].append(f"{item['title']} (링크: {item['link']})")
        else:
            api_success = False

    except Exception as e:
        st.error(f"API 호출 중 오류: {str(e)}")
        api_success = False

    if not api_success:
        return analyze_product_competitiveness(product_name, client_id, client_secret, category_id, fallback_mode=True)

    # Limit total evidences to 50 by trimming each category if needed
    total_evidences = sum(len(lst) for lst in evidences.values())
    if total_evidences > 50:
        for key in evidences:
            evidences[key] = evidences[key][:max(1, len(evidences[key]) * 50 // total_evidences)]

    return scores, evidences

def suggest_margin(analysis: Dict[str, float]) -> float:
    avg_score = (analysis["rarity"] + analysis["popularity"] + analysis["demand"] - analysis["competition"]) / 4
    margin = avg_score * 50
    return max(10, min(40, margin))

def generate_summary(analysis: Dict[str, float], margin: float) -> str:
    """
    Generate a summary for the recommended margin.
    """
    rarity = analysis["rarity"]
    popularity = analysis["popularity"]
    demand = analysis["demand"]
    competition = analysis["competition"]
    
    reasons = []
    if rarity > 0.7:
        reasons.append("높은 희소성으로 인해 프리미엄 가격 전략이 가능합니다.")
    elif rarity < 0.3:
        reasons.append("희소성이 낮아 마진을 보수적으로 설정하였습니다.")
    
    if popularity > 0.7:
        reasons.append("높은 인기로 인해 수요가 안정적입니다.")
    elif popularity < 0.3:
        reasons.append("인기가 낮아 마케팅 강화가 필요합니다.")
    
    if demand > 0.7:
        reasons.append("강한 수요로 인해 높은 마진을 적용할 수 있습니다.")
    elif demand < 0.3:
        reasons.append("수요가 약해 마진을 조정하였습니다.")
    
    if competition > 0.7:
        reasons.append("치열한 경쟁으로 인해 마진을 낮춰 경쟁력을 확보합니다.")
    elif competition < 0.3:
        reasons.append("낮은 경쟁으로 인해 여유로운 마진 설정이 가능합니다.")
    
    summary = f"추천 마진율 {margin:.1f}%는 제품의 희소성({rarity:.2f}), 인기({popularity:.2f}), 수요({demand:.2f}), 경쟁({competition:.2f})을 종합적으로 평가하여 산출되었습니다. "
    summary += " ".join(reasons) + " 이 마진은 시장 경쟁력과 수익성을 균형 있게 고려한 결과입니다."
    return summary

def calculate_prices(cost_price: float, margin: float) -> Dict[str, float]:
    """
    Calculate prices based on cost and margin (VAT excluded).
    Apply suggested margin to wholesale price.
    - Wholesale price: cost / (1 - margin/100)
    - Business member price: wholesale * 1.2 (example multiplier; customize)
    - Retail price: wholesale * 1.5 (example multiplier; customize)
    Prices rounded to nearest integer (no decimals).
    """
    if cost_price <= 0:
        return {}
    
    wholesale_price = cost_price / (1 - margin / 100)
    business_price = wholesale_price * 1.2  # Example: 20% markup from wholesale
    retail_price = wholesale_price * 1.5    # Example: 50% markup from wholesale
    
    return {
        "도매단가": round(wholesale_price),
        "사업자회원가": round(business_price),
        "일반소비자가": round(retail_price)
    }

# Streamlit App
st.set_page_config(page_title="고래미 AI 시스템", page_icon="🐋", layout="wide")

# Custom CSS for better UX/UI
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f8ff;
    }
    .stButton > button {
        background-color: #007bff;
        color: white;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .stNumberInput > div > div > input {
        border-radius: 10px;
    }
    h1 {
        color: #004085;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🐋 고래미 AI 신제품 마진 제안 시스템")

st.write("""
고래미, 씨포스트, 설래담 브랜드의 신제품을 위한 AI 분석 시스템입니다.  
타 브랜드는 경쟁사로 간주하여 분석합니다. 제품 이름을 입력하세요. 예: 타코와사비
네이버 블로그/카페 검색 추가, 수요 계산 개선 (쇼핑 인사이트 'ratio' 사용으로 클릭 비율 집계), 근거 최대 50개 (카테고리별 그룹화).
원가 입력 시 마진을 더한 도매단가, 사업자회원가, 일반소비자가 계산 (부가세 별도).
모든 상품이 식품이므로 쇼핑 카테고리 ID를 50000008 (식품)로 기본 설정. 필요 시 사이드바에서 변경.
가격은 정수로 반올림. 최종 추천 마진에 대한 요약 총평 추가.
""")

# Session state for API keys persistence
if 'client_id' not in st.session_state:
    st.session_state['client_id'] = ''
if 'client_secret' not in st.session_state:
    st.session_state['client_secret'] = ''

# Sidebar for API credentials and category ID
with st.sidebar:
    st.header("Naver API 설정")
    st.session_state['client_id'] = st.text_input("클라이언트 ID", value=st.session_state['client_id'])
    st.session_state['client_secret'] = st.text_input("클라이언트 시크릿", value=st.session_state['client_secret'])
    category_id = st.text_input("쇼핑 카테고리 ID (기본: 50000008 - 식품)", value="50000008")
    fallback_mode = st.checkbox("추정 모드 강제 사용")

product_name = st.text_input("제품 이름 입력:", key="product_input")
cost_price = st.number_input("원가 입력 (부가세 별도, 원):", min_value=0.0, step=100.0)

if st.button("분석 시작 🚀"):
    if not product_name:
        st.warning("제품 이름을 입력해주세요.")
    elif not st.session_state['client_id'] or not st.session_state['client_secret']:
        st.warning("Naver API 키를 입력해주세요.")
    else:
        with st.spinner("고래미 AI가 분석 중입니다... 🐳"):
            analysis, evidences = analyze_product_competitiveness(
                product_name, st.session_state['client_id'], st.session_state['client_secret'], category_id, fallback_mode
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("분석 결과 그래프")
            chart_data = {
                "metric": list(analysis.keys()),
                "score": list(analysis.values())
            }
            st.bar_chart(chart_data, x="metric", y="score")
        
        with col2:
            st.subheader("상세 스코어")
            for key, value in analysis.items():
                st.progress(value, text=f"{key.capitalize()}: {value:.2f}")
        
        margin = suggest_margin(analysis)
        st.subheader("제안 마진")
        st.metric("추천 마진율", f"{margin:.1f}%", delta=None)
        
        if cost_price > 0:
            prices = calculate_prices(cost_price, margin)
            if prices:
                st.subheader("계산된 가격 (부가세 별도)")
                st.table({
                    "가격 유형": list(prices.keys()),
                    "가격 (원)": list(prices.values())
                })
        
        with st.expander("근거 자료 (최대 50개, 카테고리별 그룹화)"):
            for category, items in evidences.items():
                if items:
                    st.subheader(category)
                    for item in items:
                        st.write(f"- {item}")
        
        st.subheader("최종 추천 마진 총평")
        summary = generate_summary(analysis, margin)
        st.info(summary)

st.markdown("---")
st.write("고래미 내부용 시스템. 브랜드: 고래미, 씨포스트, 설래담. 버전: 9.0")
