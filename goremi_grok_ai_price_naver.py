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

def get_naver_headers(client_id: str, client_secret: str) -> Dict[str, str]:
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

def analyze_product_competitiveness(product_name: str, client_id: str, client_secret: str, fallback_mode: bool = False) -> Tuple[Dict[str, float], List[str]]:
    """
    Analyze using Naver APIs. Return scores and list of evidences (up to 10).
    If fallback_mode, use estimated defaults.
    """
    scores = {"rarity": 0.5, "popularity": 0.5, "demand": 0.5, "competition": 0.5}
    evidences = []  # List of evidence strings, max 10

    if fallback_mode:
        scores["rarity"] = 0.7
        scores["popularity"] = 0.4
        scores["demand"] = 0.6
        scores["competition"] = 0.5
        evidences = [
            "추정 모드: 신제품으로 가정하여 희소성 높음 (0.7)",
            "추정 모드: 초기 인기 중간 수준 (0.4)",
            "추정 모드: 시장 수요 성장 예상 (0.6)",
            "추정 모드: 경쟁 중간 (0.5)"
        ]
        st.warning("데이터 부족으로 추정 모드 사용. 실제 데이터 입력 추천.")
        return scores, evidences[:10]

    headers = get_naver_headers(client_id, client_secret)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    api_success = True

    try:
        # 1. Search API for competition and rarity
        search_params = {"query": product_name, "display": 100}
        response = requests.get(SEARCH_API_URL, headers=headers, params=search_params)
        if response.status_code == 200:
            data = response.json()
            total_results = data.get("total", 0)
            scores["competition"] = min(total_results / 10000, 1.0)
            scores["rarity"] = 1 - scores["competition"]
            # Evidences: top 5 shop titles/links, labeled as our brand or competitor
            items = data.get("items", [])[:5]
            for item in items:
                label = "자사 제품" if any(brand in item['title'] for brand in OUR_BRANDS) else "경쟁 제품"
                evidences.append(f"{label}: {item['title']} (링크: {item['link']})")
        else:
            api_success = False

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
                scores["popularity"] = min(avg_ratio / 100, 1.0)
                # Evidences: top 3 monthly ratios
                for item in results[:3]:
                    evidences.append(f"트렌드: {item['period']} - 검색 비율 {item['ratio']}")
            else:
                api_success = False
        else:
            api_success = False

        # 3. Datalab Shopping Insight for demand
        insight_body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "month",
            "category": [{"name": product_name, "param": ["50000000"]}],  # Adjust as needed
            "device": "",
            "ages": [],
            "gender": ""
        }
        response = requests.post(SHOPPING_INSIGHT_URL, headers=headers, json=insight_body)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [{}])[0].get("data", [])
            if results:
                avg_click = sum(item.get("clickCount", 0) for item in results) / len(results)
                scores["demand"] = min(avg_click / 100000, 1.0)
                # Evidences: top 2 click counts
                for item in results[:2]:
                    evidences.append(f"쇼핑 인사이트: {item['period']} - 클릭 수 {item.get('clickCount', 'N/A')}")
            else:
                api_success = False
        else:
            api_success = False

    except Exception as e:
        st.error(f"API 호출 중 오류: {str(e)}")
        api_success = False

    if not api_success:
        return analyze_product_competitiveness(product_name, client_id, client_secret, fallback_mode=True)

    return scores, evidences[:10]

def suggest_margin(analysis: Dict[str, float]) -> float:
    avg_score = (analysis["rarity"] + analysis["popularity"] + analysis["demand"] - analysis["competition"]) / 4
    margin = avg_score * 50
    return max(10, min(40, margin))

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
""")

# Session state for API keys persistence
if 'client_id' not in st.session_state:
    st.session_state['client_id'] = ''
if 'client_secret' not in st.session_state:
    st.session_state['client_secret'] = ''

# Sidebar for API credentials (persistent)
with st.sidebar:
    st.header("Naver API 설정")
    st.session_state['client_id'] = st.text_input("클라이언트 ID", value=st.session_state['client_id'], type="password")
    st.session_state['client_secret'] = st.text_input("클라이언트 시크릿", value=st.session_state['client_secret'], type="password")
    fallback_mode = st.checkbox("추정 모드 강제 사용")

product_name = st.text_input("제품 이름 입력:", key="product_input")

if st.button("분석 시작 🚀"):
    if not product_name:
        st.warning("제품 이름을 입력해주세요.")
    elif not st.session_state['client_id'] or not st.session_state['client_secret']:
        st.warning("Naver API 키를 입력해주세요.")
    else:
        with st.spinner("고래미 AI가 분석 중입니다... 🐳"):
            analysis, evidences = analyze_product_competitiveness(
                product_name, st.session_state['client_id'], st.session_state['client_secret'], fallback_mode
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
        
        with st.expander("근거 자료 (최대 10개)"):
            if evidences:
                for ev in evidences:
                    st.write(f"- {ev}")
            else:
                st.write("근거 자료 없음.")

st.markdown("---")
st.write("고래미 내부용 시스템. 브랜드: 고래미, 씨포스트, 설래담. 버전: 4.1")
