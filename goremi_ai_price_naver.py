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

# API 요청 헤더 생성 함수
def get_naver_headers(client_id, client_secret):
    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }

# 네이버 검색 API 호출 함수
def search_naver(query, headers):
    url = "https://openapi.naver.com/v1/search/blog.json"
    params = {"query": query, "display": 20}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        search_data = response.json()
        results = []
        for i, item in enumerate(search_data.get('items', [])):
            clean_title = re.sub('<[^<]+?>', '', item.get('title', ''))
            clean_snippet = re.sub('<[^<]+?>', '', item.get('description', ''))
            results.append({'index': i + 1, 'title': clean_title, 'snippet': clean_snippet})
        return results
    except requests.exceptions.RequestException as e:
        st.error(f"네이버 검색 API 연동 중 오류: {e}")
        return []

# 네이버 데이터랩 API 호출 함수
def call_datalab_api(api_url, headers, body):
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"네이버 데이터랩 API 연동 중 오류: {e}")
        return None

# ----------------------------------------------------------------------
# 1. AI 분석 모듈 (데이터랩 통합)
# ----------------------------------------------------------------------

# 1-1. 데이터랩 (검색어 트렌드) 분석
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
        df = pd.DataFrame(trend_data)
        df['ratio'] = df['ratio'].astype(float)
        df['period'] = pd.to_datetime(df['period'])
        df = df.set_index('period')

        # 최근 3개월 추세 분석
        recent_avg = df['ratio'][-3:].mean()
        past_avg = df['ratio'][-6:-3].mean()
        
        trend_score = 5  # 기본 점수
        if recent_avg > past_avg * 1.2:
            trend_status = "상승세"
            trend_score += 3
        elif recent_avg < past_avg * 0.8:
            trend_status = "하락세"
            trend_score -= 2
        else:
            trend_status = "보합세"
        
        explanation = f"지난 1년간의 검색량 분석 결과, **'{product_name}'**에 대한 관심도는 현재 **'{trend_status}'** 입니다. 최근 3개월 평균 검색량이 이전 3개월 대비 변화를 보였습니다."
        return min(10, max(1, trend_score)), explanation, df
    else:
        return 1, "검색어 트렌드 데이터를 가져오지 못했습니다. 일반적인 키워드가 아닐 수 있습니다.", None


# 1-2. 데이터랩 (쇼핑 인사이트) 분석
def analyze_shopping_insight(product_name, headers):
    st.write("### 🛍️ 데이터랩 쇼핑 인사이트 분석 중...")
    api_url = "https://openapi.naver.com/v1/datalab/shopping/category/keywords"
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "date",
        "category": "50000006",  # 식품 카테고리
        "keyword": product_name,
        "device": "",
        "gender": "",
        "ages": [],
    }

    data = call_datalab_api(api_url, headers, body)

    if data and data.get('results'):
        insight_data = data['results'][0]['data']
        df = pd.DataFrame(insight_data)
        df['ratio'] = df['ratio'].astype(float)
        total_ratio = df['ratio'].sum()

        # 성별/연령별 분석을 위해 별도 API 호출 필요 (이 프로토타입에서는 합산된 클릭량으로 시장 크기 추정)
        market_size_score = min(10, max(1, total_ratio / 10)) # 비율 합계로 점수화 (스케일링 필요)

        # 주요 타겟층 분석 (별도 호출이 필요하나 여기선 예시로 작성)
        # 실제로는 gender, ages를 바꿔가며 여러번 호출 후 가장 높은 비율을 찾습니다.
        target_audience = "정보 확인 불가 (API 제약)"
        explanation = f"최근 1개월간 쇼핑 분야에서 **'{product_name}'** 관련 클릭량은 총합 **{total_ratio:.2f}** 수준으로, 시장 관심도가 **{'높음' if market_size_score > 6 else '보통' if market_size_score > 3 else '낮음'}**으로 판단됩니다."
        return market_size_score, explanation, target_audience, df
    else:
        return 1, "쇼핑 인사이트 데이터를 가져오지 못했습니다. 쇼핑 관련 키워드가 아닐 수 있습니다.", "정보 확인 불가", None


# 1-3. 경쟁 및 희소성 분석 (네이버 검색 활용)
def analyze_competition_and_rarity(product_name, headers):
    st.write("### ⚔️ 경쟁 및 원가 정보 분석 중...")
    
    # 경쟁사 분석
    search_results_comp = search_naver(f'"{product_name}" 판매 가격', headers)
    competitor_count = 0
    prices = []
    price_pattern = re.compile(r'([\d,]+)원')
    for result in search_results_comp:
        combined_text = result.get('title', '') + result.get('snippet', '')
        if any(keyword in combined_text for keyword in ['판매', '구매', '쇼핑']):
            competitor_count += 1
        found_prices = price_pattern.findall(combined_text)
        for price_str in found_prices:
            try:
                price_num = int(price_str.replace(',', ''))
                if 100 < price_num < 1000000: prices.append(price_num)
            except ValueError: continue
    
    competition_score = min(10, competitor_count)
    avg_price = int(np.mean(prices)) if prices else 0
    
    # 희소성 분석
    raw_materials = ['문어', '고추냉이'] if '타코와사비' in product_name else [product_name]
    search_results_rarity = search_naver(f"{' '.join(raw_materials)} 가격 급등 수급", headers)
    rarity_score = 1
    if search_results_rarity: rarity_score = min(10, 1 + len(search_results_rarity) * 2)

    return competition_score, avg_price, rarity_score

# 2. 마진 제안 로직
def suggest_margin(scores, base_cost):
    trend_score = scores['trend']
    market_size_score = scores['market_size']
    competition_score = scores['competition']
    rarity_score = scores['rarity']
    avg_competitor_price = scores['avg_price']

    base_margin = 35.0
    demand_bonus = (trend_score - 5) * 1.5  # 트렌드 점수 영향력 강화
    market_size_bonus = (market_size_score - 5) * 1.0 # 시장 크기 보너스
    rarity_bonus = (rarity_score - 5) * 1.0
    competition_penalty = (competition_score - 5) * 1.5 # 경쟁 페널티 강화

    suggested_margin = base_margin + demand_bonus + market_size_bonus + rarity_bonus - competition_penalty
    suggested_margin = max(15.0, min(70.0, suggested_margin))
    
    suggested_price = int(base_cost / (1 - (suggested_margin / 100)))

    if avg_competitor_price > 0 and suggested_price > avg_competitor_price * 1.3:
        final_price = int(avg_competitor_price * 1.2)
    else:
        final_price = suggested_price
    
    final_price = round(final_price / 100) * 100
    final_margin = (1 - (base_cost / final_price)) * 100 if final_price > 0 else 0
    return final_margin, final_price


# ----------------------------------------------------------------------
# 3. Streamlit UI (Front-end)
# ----------------------------------------------------------------------

st.set_page_config(page_title="고도화된 AI 마진 제안 시스템", layout="wide")
st.title("🚀 고도화된 AI 신제품 마진 제안 시스템")
st.write("네이버 데이터랩과 검색 API를 통합하여, 시장의 트렌드와 타겟 고객까지 분석 후 최적의 마진을 제안합니다.")

with st.sidebar:
    st.header("🔑 네이버 API 키 입력")
    st.write("[네이버 개발자 센터](https://developers.naver.com/)에서 발급받은 키를 입력하세요.")
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")

product_name = st.text_input("분석할 제품명을 입력하세요:", "타코와사비")
base_cost = st.number_input("제품의 예상 제조원가(1개 당)를 입력하세요 (원):", min_value=100, value=3000, step=100)

if st.button("📈 정밀 분석 시작"):
    if not client_id or not client_secret:
        st.error("사이드바에 네이버 API 키를 먼저 입력해주세요!")
    elif not product_name or base_cost <= 0:
        st.error("제품명과 제조원가를 올바르게 입력해주세요.")
    else:
        with st.spinner(f"'{product_name}'에 대한 데이터랩 및 검색 데이터를 종합 분석 중입니다..."):
            headers = get_naver_headers(client_id, client_secret)

            # 분석 모듈 순차 실행
            trend_score, trend_exp, trend_df = analyze_search_trend(product_name, headers)
            market_size_score, market_exp, target_audience, shopping_df = analyze_shopping_insight(product_name, headers)
            comp_score, avg_price, rarity_score = analyze_competition_and_rarity(product_name, headers)
            
            scores = {
                "trend": trend_score, "market_size": market_size_score,
                "competition": comp_score, "rarity": rarity_score, "avg_price": avg_price
            }
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

        with st.expander("📈 **수요 트렌드 분석 (데이터랩)**", expanded=True):
            st.metric("관심도 트렌드 점수 (10점 만점)", f"{trend_score}/10")
            st.write(trend_exp)
            if trend_df is not None:
                st.line_chart(trend_df)

        with st.expander("🛍️ **타겟 및 시장 크기 분석 (데이터랩)**", expanded=True):
            st.metric("쇼핑 시장 크기 점수 (10점 만점)", f"{market_size_score}/10")
            st.write(market_exp)
            # st.write(f"📊 **주요 타겟 고객층:** {target_audience}") # 상세 분석 시 활성화
            if shopping_df is not None:
                 st.write("최근 1개월간 일별 클릭량 추이:")
                 st.bar_chart(shopping_df.set_index('period'))

        with st.expander("⚔️ **경쟁 및 원가 분석 (네이버 검색)**"):
             col1, col2 = st.columns(2)
             with col1:
                st.metric("경쟁 강도 점수 (높을수록 치열)", f"{comp_score}/10")
             with col2:
                st.metric("희소성/원가 점수 (높을수록 희소)", f"{rarity_score}/10")
             if avg_price > 0:
                st.write(f"- 온라인상에서 식별된 경쟁사 평균 판매가는 약 **{avg_price:,}원** 입니다.")
             st.write(f"- 원재료 수급 불안정 및 가격 상승 관련 뉴스가 **{'다수' if rarity_score > 6 else '일부' if rarity_score > 3 else '거의'}** 발견되었습니다.")

        st.caption("주의: 본 결과는 네이버 API를 통해 수집된 데이터를 기반으로 한 AI의 자동 분석 결과이며, 최종 의사결정은 담당자의 종합적인 검토가 필요합니다.")
