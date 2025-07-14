import streamlit as st
import pandas as pd
import numpy as np
import re
import requests  # 네이버 API 요청을 위한 라이브러리
import json

# ----------------------------------------------------------------------
# 0. 네이버 검색 API 호출 모듈 (NEW)
# ----------------------------------------------------------------------
def search_naver(query, client_id, client_secret):
    """
    네이버 검색 API를 호출하여 결과를 가져오는 함수
    """
    # 네이버 검색 API URL
    url = "https://openapi.naver.com/v1/search/blog.json" # 블로그 검색을 예시로 함
    
    # API 요청 헤더
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    
    # 검색 파라미터
    params = {
        "query": query,
        "display": 20,  # 최대 20개 결과 가져오기
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # 오류 발생 시 예외 처리
        
        search_data = response.json()
        
        # API 결과를 분석 함수가 사용하기 좋은 형태로 가공
        results = []
        for i, item in enumerate(search_data.get('items', [])):
            # HTML 태그 제거
            clean_title = re.sub('<[^<]+?>', '', item['title'])
            clean_snippet = re.sub('<[^<]+?>', '', item['description'])
            results.append({
                'index': i + 1,
                'title': clean_title,
                'snippet': clean_snippet,
            })
        return results

    except requests.exceptions.RequestException as e:
        st.error(f"네이버 API 연동 중 오류가 발생했습니다: {e}")
        # 오류 발생 시 빈 리스트 반환
        return []
    except json.JSONDecodeError:
        st.error("네이버 API로부터 받은 응답을 파싱하는 데 실패했습니다.")
        return []

# ----------------------------------------------------------------------
# 1. AI 분석 모듈 (Back-end) - 이전 코드와 거의 동일
# ----------------------------------------------------------------------

def analyze_demand_popularity(product_name, search_results):
    st.write(f"### 💡 수요 및 인기도 분석 중...")
    keywords = ['후기', '리뷰', '레시피', '만들기', '맛집', '추천', '인기']
    demand_score = 1
    evidence = []
    for result in search_results:
        combined_text = result.get('title', '') + result.get('snippet', '')
        for keyword in keywords:
            if keyword in combined_text:
                demand_score += 1
                if len(evidence) < 5:
                    evidence.append(f"'{keyword}' 언급: {result['title']} [검색결과 {result['index']}]")
    demand_score = min(10, demand_score)
    explanation = f"'{product_name}' 관련 웹 문서에서 **'{', '.join(keywords)}'** 등의 키워드가 다수 발견되어 소비자 관심도가 **{'높음' if demand_score > 6 else '보통' if demand_score > 3 else '낮음'}**으로 판단됩니다."
    return demand_score, explanation, evidence

def analyze_competition(product_name, search_results):
    st.write(f"### ⚔️ 경쟁 환경 분석 중...")
    competitor_count = 0
    prices = []
    evidence = []
    price_pattern = re.compile(r'([\d,]+)원')
    for result in search_results:
        combined_text = result.get('title', '') + result.get('snippet', '')
        if any(keyword in combined_text for keyword in ['판매', '구매', '쇼핑', '마켓', '가격']):
            competitor_count += 1
            if len(evidence) < 5:
                 evidence.append(f"경쟁사 추정: {result['title']} [검색결과 {result['index']}]")
            found_prices = price_pattern.findall(combined_text)
            for price_str in found_prices:
                try:
                    price_num = int(price_str.replace(',', ''))
                    if 100 < price_num < 1000000:
                        prices.append(price_num)
                except ValueError:
                    continue
    competition_score = min(10, competitor_count) # 네이버 블로그 검색 기준이므로 점수 산정 로직 완화
    avg_price = int(np.mean(prices)) if prices else 0
    explanation = f"온라인에서 **{competitor_count}개 이상의 경쟁 관련 포스팅**이 식별되었습니다. 경쟁 강도는 **{'치열함' if competition_score > 6 else '보통' if competition_score > 3 else '낮음'}** 수준입니다."
    if avg_price > 0:
        explanation += f" 평균 경쟁사 판매가는 **약 {avg_price:,}원**으로 추정됩니다."
    return competition_score, avg_price, explanation, evidence

def analyze_rarity_cost(product_name, search_results):
    st.write(f"### 💎 원재료 희소성 및 원가 분석 중...")
    if '타코와사비' in product_name:
        raw_materials = ['문어', '고추냉이']
    else:
        raw_materials = [product_name]
    rarity_score = 1
    evidence = []
    for result in search_results:
        combined_text = result.get('title', '') + result.get('snippet', '')
        if any(mat in combined_text for mat in raw_materials) and any(kw in combined_text for kw in ['급등', '인상', '부족', '어획량 감소', '수급 불안', '동향']):
            rarity_score += 2
            if len(evidence) < 5:
                evidence.append(f"원가 변동 요인: {result['title']} [검색결과 {result['index']}]")
    rarity_score = min(10, rarity_score)
    explanation = f"핵심 원재료({', '.join(raw_materials)})의 수급 또는 가격 관련 정보가 식별되어 희소성이 **{'높음' if rarity_score > 6 else '보통' if rarity_score > 3 else '낮음'}**으로 분석됩니다."
    return rarity_score, explanation, evidence

def suggest_margin(scores, base_cost):
    demand_score = scores['demand']
    competition_score = scores['competition']
    rarity_score = scores['rarity']
    avg_competitor_price = scores['avg_price']
    base_margin = 30.0
    demand_bonus = (demand_score - 5) * 1.0
    rarity_bonus = (rarity_score - 5) * 1.0
    competition_penalty = (competition_score - 5) * 1.0
    suggested_margin = base_margin + demand_bonus + rarity_bonus - competition_penalty
    suggested_margin = max(10.0, min(70.0, suggested_margin))
    suggested_price = int(base_cost / (1 - (suggested_margin / 100)))
    if avg_competitor_price > 0 and suggested_price > avg_competitor_price * 1.3:
        final_price = int(avg_competitor_price * 1.2)
    else:
        final_price = suggested_price
    final_price = round(final_price / 100) * 100
    final_margin = (1 - (base_cost / final_price)) * 100 if final_price > 0 else 0
    return final_margin, final_price

# ----------------------------------------------------------------------
# 2. Streamlit UI (Front-end)
# ----------------------------------------------------------------------

st.set_page_config(page_title="AI 신제품 마진 제안 시스템 (Naver 기반)", layout="wide")

st.title("🤖 AI 신제품 마진 제안 시스템 (Naver 기반)")
st.write("제품명과 예상 제조원가를 입력하면, AI가 네이버 검색 데이터를 분석하여 최적의 마진율과 판매가를 제안합니다.")

# --- API 키 입력 섹션 ---
with st.sidebar:
    st.header("🔑 네이버 API 키 입력")
    st.write("[네이버 개발자 센터](https://developers.naver.com/)에서 발급받은 키를 입력하세요.")
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")

# --- 메인 화면 ---
product_name = st.text_input("분석할 제품명을 입력하세요:", "타코와사비")
base_cost = st.number_input("제품의 예상 제조원가(1개 당)를 입력하세요 (원):", min_value=100, value=3000, step=100)

if st.button("분석 시작"):
    if not client_id or not client_secret:
        st.error("사이드바에 네이버 API 키를 먼저 입력해주세요!")
    elif not product_name or base_cost <= 0:
        st.error("제품명과 제조원가를 올바르게 입력해주세요.")
    else:
        with st.spinner(f"'{product_name}'에 대한 네이버 검색 데이터를 실시간으로 분석 중입니다..."):
            
            # 네이버 검색 실행 (다양한 키워드로 검색하여 정보 수집)
            query1 = f'"{product_name}" 후기 레시피'
            query2 = f'"{product_name}" 가격 판매'
            query3 = '문어 가격 동향' # 원재료 키워드는 고정 또는 제품별 DB화 필요

            results1 = search_naver(query1, client_id, client_secret)
            results2 = search_naver(query2, client_id, client_secret)
            results3 = search_naver(query3, client_id, client_secret)
            
            # 모든 검색 결과 합치기
            all_results = results1 + results2 + results3

            if not all_results:
                st.warning("네이버에서 관련 정보를 찾을 수 없거나 API 호출에 실패했습니다. 키워드나 API 설정을 확인해주세요.")
            else:
                # 분석 모듈 실행
                demand_score, demand_exp, demand_evi = analyze_demand_popularity(product_name, all_results)
                comp_score, avg_price, comp_exp, comp_evi = analyze_competition(product_name, all_results)
                rarity_score, rarity_exp, rarity_evi = analyze_rarity_cost(product_name, all_results)
                
                scores = {"demand": demand_score, "competition": comp_score, "rarity": rarity_score, "avg_price": avg_price}

                # 최종 마진 및 가격 제안
                final_margin, final_price = suggest_margin(scores, base_cost)
            
                st.success("✅ 분석이 완료되었습니다!")
                
                # --- 최종 결과 표시 ---
                st.header("📊 최종 분석 결과 및 마진 제안")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="🎯 최종 제안 마진율", value=f"{final_margin:.1f}%")
                with col2:
                    st.metric(label="💰 최종 제안 판매가", value=f"{final_price:,} 원")

                st.info(f"제조원가 **{base_cost:,}원** 기준, **{final_margin:.1f}%**의 마진을 적용한 **{final_price:,}원**의 판매가를 제안합니다.")
                
                # --- 세부 분석 결과 ---
                st.subheader("📝 항목별 세부 분석 결과")
                with st.expander("💡 수요 및 인기도 분석 (자세히 보기)"):
                    st.metric("수요/인기도 점수 (10점 만점)", f"{demand_score}/10")
                    st.write(demand_exp)
                    st.write("**주요 근거:**"); [st.markdown(f"- {e}") for e in demand_evi]

                with st.expander("⚔️ 경쟁 환경 분석 (자세히 보기)"):
                    st.metric("경쟁 강도 점수 (높을수록 치열)", f"{comp_score}/10")
                    st.write(comp_exp)
                    st.write("**주요 근거:**"); [st.markdown(f"- {e}") for e in comp_evi]

                with st.expander("💎 원재료 희소성/원가 분석 (자세히 보기)"):
                    st.metric("희소성/원가상승 점수 (높을수록 희소)", f"{rarity_score}/10")
                    st.write(rarity_exp)
                    st.write("**주요 근거:**"); [st.markdown(f"- {e}") for e in rarity_evi]

                st.caption("주의: 본 결과는 네이버 검색 정보를 기반으로 한 AI의 자동 분석 결과이며, 최종 의사결정은 담당자의 검토가 필요합니다.")
