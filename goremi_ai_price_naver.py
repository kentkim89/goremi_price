import streamlit as st
import pandas as pd
import numpy as np
import re
import requests
import json
from datetime import date, timedelta

# ----------------------------------------------------------------------
# 0. 네이버 API 호출 공통 모듈
# ----------------------------------------------------------------------

def get_naver_headers(client_id, client_secret):
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }

def search_naver(query, headers, endpoint="shop"):
    url = f"https://openapi.naver.com/v1/search/{endpoint}.json"
    params = {"query": query, "display": 20}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            st.warning(f"네이버 {endpoint} 검색 API 오류: {response.status_code} - {response.text}")
            return []
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        st.error(f"네이버 {endpoint} 검색 API 연동 중 오류: {e}")
        return []

def call_datalab_api(api_url, headers, body):
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(body, ensure_ascii=False))
        if response.status_code != 200:
            st.error(f"데이터랩 API 오류: {response.status_code} - {response.text}")
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"데이터랩 API 연동 중 오류: {e}")
        return None

# ----------------------------------------------------------------------
# 1. AI 분석 모듈 (데이터랩 통합)
# ----------------------------------------------------------------------

def analyze_search_trend(product_name, headers):
    st.write("### 📈 데이터랩 검색어 트렌드 분석 중...")
    api_url = "https://openapi.naver.com/v1/datalab/search"
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "month",
        "keywordGroups": [{"groupName": product_name, "keywords": [product_name]}],
    }
    
    data = call_datalab_api(api_url, headers, body)
    
    if data and data.get('results'):
        trend_data = data['results'][0]['data']
        if not trend_data:
            return 1, "검색어 트렌드 데이터가 없습니다. 검색량이 매우 적은 키워드일 수 있습니다.", None
        
        df = pd.DataFrame(trend_data)
        df['ratio'] = df['ratio'].astype(float)
        df['period'] = pd.to_datetime(df['period'])
        df = df.set_index('period')

        recent_avg = df['ratio'][-3:].mean()
        past_avg = df['ratio'][-6:-3].mean() if len(df) > 3 else recent_avg
        
        trend_score = 5
        if recent_avg > past_avg * 1.2: trend_status = "상승세"; trend_score += 3
        elif recent_avg < past_avg * 0.8: trend_status = "하락세"; trend_score -= 2
        else: trend_status = "보합세"
        
        explanation = f"지난 1년간 검색량 분석 결과, **'{product_name}'** 관심도는 현재 **'{trend_status}'** 입니다."
        return min(10, max(1, trend_score)), explanation, df
    else:
        return 1, "검색어 트렌드 데이터를 가져오지 못했습니다.", None

def analyze_shopping_insight(product_name, headers):
    st.write("### 🛍️ 데이터랩 쇼핑 인사이트 분석 중...")
    api_url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    
    # [핵심 수정] 쇼핑인사이트 API 요청 본문(body) 형식을 공식 문서에 맞게 완전히 수정
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "month",
        "category": "50000006",  # 식품 카테고리
        "keyword": [ # 'keywordGroups'가 아닌 'keyword' 구조 사용
            {
                "name": product_name,
                "param": [product_name]
            }
        ]
    }

    data = call_datalab_api(api_url, headers, body)

    if data and data.get('results'):
        insight_data = data['results'][0]['data']
        if not insight_data:
            return 1, "쇼핑 인사이트 데이터가 없습니다. 쇼핑 관련 검색량이 매우 적은 키워드일 수 있습니다.", None
            
        df = pd.DataFrame(insight_data)
        df['ratio'] = df['ratio'].astype(float)
        df['period'] = pd.to_datetime(df['period'])
        df = df.set_index('period')

        total_ratio_sum = df['ratio'].sum()
        market_size_score = min(10, max(1, np.log(total_ratio_sum + 1) * 2))

        explanation = f"지난 1년간 쇼핑 분야에서 **'{product_name}'** 클릭량은 꾸준히 발생했으며, 시장 관심도는 **{'높음' if market_size_score > 6 else '보통' if market_size_score > 3 else '낮음'}**으로 판단됩니다."
        return market_size_score, explanation, df
    else:
        return 1, "쇼핑 인사이트 데이터를 가져오지 못했습니다.", None

def analyze_competition_and_rarity(product_name, headers):
    st.write("### ⚔️ 경쟁 및 원가 정보 분석 중...")
    
    shop_results = search_naver(f'"{product_name}"', headers, endpoint="shop")
    competitor_count = len(shop_results)
    
    raw_materials = ['문어', '고추냉이'] if '타코와사비' in product_name else [product_name.replace('와사비', '')]
    news_results = search_naver(f"{' '.join(raw_materials)} 가격 급등 수급 불안", headers, endpoint="news")
    rarity_count = len(news_results)
    
    comp_score_text = f"네이버 쇼핑에서 **{competitor_count}개 이상**의 직접적인 경쟁 상품이 검색되었습니다."
    rarity_score_text = f"주요 원재료 관련 가격/수급 뉴스가 **{rarity_count}건** 검색되었습니다."

    return min(10, competitor_count), min(10, 1 + rarity_count * 2), comp_score_text, rarity_score_text

def suggest_margin(scores, base_cost):
    trend_score = scores.get('trend', 5)
    market_size_score = scores.get('market_size', 5)
    competition_score = scores.get('competition', 5)
    rarity_score = scores.get('rarity', 5)

    base_margin = 35.0
    demand_bonus = (trend_score - 5) * 1.5
    market_size_bonus = (market_size_score - 5) * 1.0
    rarity_bonus = (rarity_score - 5) * 1.0
    competition_penalty = (competition_score - 5) * 1.5

    suggested_margin = base_margin + demand_bonus + market_size_bonus + rarity_bonus - competition_penalty
    suggested_margin = max(15.0, min(70.0, suggested_margin))
    
    suggested_price = int(base_cost / (1 - (suggested_margin / 100)))
    final_price = round(suggested_price / 100) * 100
    final_margin = (1 - (base_cost / final_price)) * 100 if final_price > 0 else 0
    return final_margin, final_price


# ----------------------------------------------------------------------
# 3. Streamlit UI (Front-end)
# ----------------------------------------------------------------------

st.set_page_config(page_title="고래미 AI 마진 분석", layout="wide")
st.title("🐋 고래미 AI 마진 제안 시스템")
st.write("네이버 데이터랩과 검색 API를 통합하여, 시장의 트렌드와 경쟁상황을 정밀 분석 후 최적의 마진을 제안합니다.")

with st.sidebar:
    st.header("Powered by 고래미")
    st.markdown("---")
    st.header("🔑 네이버 API 키 입력")
    st.write("[네이버 개발자 센터](https://developers.naver.com/)에서 발급받은 키를 입력하세요.")
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")

product_name = st.text_input("분석할 제품명을 입력하세요:", "소라와사비")
base_cost = st.number_input("제품의 예상 제조원가(1개 당)를 입력하세요 (원):", min_value=100, value=3500, step=100)

if st.button("📈 정밀 분석 시작"):
    if not client_id or not client_secret:
        st.error("사이드바에 네이버 API 키를 먼저 입력해주세요!")
    elif not product_name or base_cost <= 0:
        st.error("제품명과 제조원가를 올바르게 입력해주세요.")
    else:
        with st.spinner(f"'{product_name}'에 대한 시장 데이터를 종합 분석 중입니다..."):
            headers = get_naver_headers(client_id, client_secret)

            trend_score, trend_exp, trend_df = analyze_search_trend(product_name, headers)
            market_size_score, market_exp, shopping_df = analyze_shopping_insight(product_name, headers)
            comp_score, rarity_score, comp_text, rarity_text = analyze_competition_and_rarity(product_name, headers)
            
            scores = {"trend": trend_score, "market_size": market_size_score, "competition": comp_score, "rarity": rarity_score}
            final_margin, final_price = suggest_margin(scores, base_cost)
        
        st.success("✅ 정밀 분석이 완료되었습니다!")
        
        st.header("📊 최종 분석 결과 및 마진 제안")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="🎯 최종 제안 마진율", value=f"{final_margin:.1f}%")
        with col2:
            st.metric(label="💰 최종 제안 판매가", value=f"{final_price:,} 원")

        st.info(f"제조원가 **{base_cost:,}원** 기준, 시장 트렌드와 경쟁상황을 종합하여 **{final_margin:.1f}%**의 마진을 적용한 **{final_price:,}원**의 판매가를 제안합니다.")
        
        st.subheader("📝 항목별 세부 분석 결과")

        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("<h5>📈 수요 트렌드 분석 (검색어)</h5>", unsafe_allow_html=True)
                st.metric("관심도 트렌드 점수", f"{trend_score}/10")
                st.write(trend_exp)
                if trend_df is not None and not trend_df.empty:
                    st.line_chart(trend_df, height=200)

        with col2:
            with st.container(border=True):
                st.markdown("<h5>🛍️ 시장 크기 분석 (쇼핑 클릭)</h5>", unsafe_allow_html=True)
                st.metric("쇼핑 시장 크기 점수", f"{market_size_score}/10")
                st.write(market_exp)
                if shopping_df is not None and not shopping_df.empty:
                    st.line_chart(shopping_df, height=200)
        
        with st.container(border=True):
            st.markdown("<h5>⚔️ 경쟁 및 원가 분석 (쇼핑/뉴스)</h5>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("경쟁 강도 점수 (높을수록 치열)", f"{comp_score}/10")
                st.caption(comp_text)
            with c2:
                st.metric("희소성/원가 점수 (높을수록 리스크)", f"{rarity_score}/10")
                st.caption(rarity_text)

        st.caption("주의: 본 결과는 고래미 내부 분석 시스템에 의해 자동 분석된 결과이며, 최종 의사결정은 담당자의 종합적인 검토가 필요합니다.")
