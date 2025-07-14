import streamlit as st
import pandas as pd
import numpy as np
import re
import time

# ----------------------------------------------------------------------
# 1. AI 분석 모듈 (Back-end)
# 실제 시스템에서는 이 부분을 고도화된 AI 모델로 대체할 수 있습니다.
# ----------------------------------------------------------------------

# 가상 데이터베이스 또는 API를 통해 가져왔다고 가정하는 함수들입니다.
# 이 프로토타입에서는 Google 검색 결과를 바탕으로 로직을 시뮬레이션합니다.

def analyze_demand_popularity(product_name, search_results):
    """
    수요 및 인기도 분석 함수
    - 검색 결과에서 '후기', '레시피', '맛집' 등의 키워드 빈도를 바탕으로 점수 산정
    """
    st.write(f"### 💡 수요 및 인기도 분석 중...")
    
    # 검색 결과 스니펫에서 키워드 카운트
    # 실제로는 자연어 처리(NLP) 모델을 사용하여 긍정/부정 감성 분석 등을 수행할 수 있습니다.
    keywords = ['후기', '리뷰', '레시피', '만들기', '맛집', '추천', '인기']
    demand_score = 1
    evidence = []

    for result in search_results:
        snippet = result.get('snippet', '').lower()
        title = result.get('title', '').lower()
        combined_text = title + snippet
        for keyword in keywords:
            if keyword in combined_text:
                demand_score += 1
                if len(evidence) < 5: # 증거는 최대 5개까지만 수집
                    evidence.append(f"'{keyword}' 언급: {result['title']} [검색결과 {result['index']}]")

    # 점수를 1~10점으로 정규화
    demand_score = min(10, demand_score) 
    
    explanation = f"'{product_name}' 관련 소셜 및 웹 문서에서 **'{', '.join(keywords)}'** 등의 키워드가 다수 발견되어 소비자 관심도가 **{'높음' if demand_score > 6 else '보통' if demand_score > 3 else '낮음'}**으로 판단됩니다."
    
    return demand_score, explanation, evidence


def analyze_competition(product_name, search_results):
    """
    경쟁사 및 가격 분석 함수
    - '판매', '가격', '구매' 키워드 및 숫자(가격) 패턴으로 경쟁 강도 분석
    """
    st.write(f"### ⚔️ 경쟁 환경 분석 중...")

    competitor_count = 0
    prices = []
    evidence = []

    # 정규표현식을 사용하여 '숫자,숫자원' 또는 '숫자원' 형태의 가격 정보 추출
    price_pattern = re.compile(r'([\d,]+)원')

    for result in search_results:
        snippet = result.get('snippet', '')
        title = result.get('title', '')
        combined_text = title + snippet
        
        if any(keyword in combined_text for keyword in ['판매', '구매', '쇼핑', '마켓', '가격']):
            competitor_count += 1
            if len(evidence) < 5:
                 evidence.append(f"경쟁사 추정: {result['title']} [검색결과 {result['index']}]")

            # 가격 정보 추출
            found_prices = price_pattern.findall(combined_text)
            for price_str in found_prices:
                try:
                    # 쉼표 제거 후 숫자로 변환
                    price_num = int(price_str.replace(',', ''))
                    # 너무 비현실적인 가격은 제외 (예: 100원 미만, 100만원 초과)
                    if 100 < price_num < 1000000:
                        prices.append(price_num)
                except ValueError:
                    continue

    # 경쟁 강도 점수화 (경쟁사가 많을수록 점수가 높음)
    competition_score = min(10, competitor_count * 2)
    avg_price = int(np.mean(prices)) if prices else 0

    explanation = f"온라인에서 **{competitor_count}개 이상의 경쟁 판매처**가 식별되었습니다. 경쟁 강도는 **{'치열함' if competition_score > 6 else '보통' if competition_score > 3 else '낮음'}** 수준입니다."
    if avg_price > 0:
        explanation += f" 평균 경쟁사 판매가는 **약 {avg_price:,}원**으로 추정됩니다."

    return competition_score, avg_price, explanation, evidence


def analyze_rarity_cost(product_name, search_results):
    """
    원재료 희소성 및 원가 변동성 분석 함수
    - 원재료 + '가격', '수입', '급등', '동향' 등의 키워드로 희소성 점수 추정
    """
    st.write(f"### 💎 원재료 희소성 및 원가 분석 중...")
    
    # 제품명으로부터 핵심 원재료 추정 (실제 시스템에서는 원재료 DB 필요)
    # 예시: '타코와사비' -> '문어', '고추냉이'
    # 이 부분은 실제 사내 시스템에서는 '제품별 원재료 구성표' DB와 연동해야 합니다.
    if '타코와사비' in product_name:
        raw_materials = ['문어', '고추냉이']
    else:
        raw_materials = [product_name] # 일반적인 경우 제품명 자체를 원재료로 간주

    rarity_score = 1
    evidence = []
    
    # "문어 가격", "고추냉이 수입" 등의 키워드로 검색된 결과 분석
    for result in search_results:
        snippet = result.get('snippet', '')
        title = result.get('title', '')
        combined_text = title + snippet

        # 가격 상승/수급 불안 관련 키워드가 있는지 확인
        if any(mat in combined_text for mat in raw_materials) and any(kw in combined_text for kw in ['급등', '인상', '부족', '어획량 감소', '수급 불안']):
            rarity_score += 2
            if len(evidence) < 5:
                evidence.append(f"원가 상승 요인: {result['title']} [검색결과 {result['index']}]")

    rarity_score = min(10, rarity_score)
    explanation = f"핵심 원재료({', '.join(raw_materials)})의 수급 불안정 또는 가격 상승 관련 정보가 식별되어 희소성이 **{'높음' if rarity_score > 6 else '보통' if rarity_score > 3 else '낮음'}**으로 분석됩니다."

    return rarity_score, explanation, evidence

def suggest_margin(scores, base_cost):
    """
    최종 마진 제안 함수
    - 각 분석 점수를 바탕으로 최종 마진율과 제안 가격 계산
    """
    demand_score = scores['demand']
    competition_score = scores['competition']
    rarity_score = scores['rarity']
    avg_competitor_price = scores['avg_price']

    # 기본 마진율 설정
    base_margin = 30.0

    # 점수에 따른 마진율 조정
    # 수요가 높을수록 마진 추가 (최대 10%)
    demand_bonus = (demand_score - 5) * 1.0 
    # 희소성이 높을수록 마진 추가 (최대 10%)
    rarity_bonus = (rarity_score - 5) * 1.0
    # 경쟁이 치열할수록 마진 감소 (최대 10%)
    competition_penalty = (competition_score - 5) * 1.0
    
    suggested_margin = base_margin + demand_bonus + rarity_bonus - competition_penalty
    
    # 마진율을 10% ~ 70% 사이로 제한
    suggested_margin = max(10.0, min(70.0, suggested_margin))

    # 제안 판매가 계산
    suggested_price = int(base_cost / (1 - (suggested_margin / 100)))

    # 경쟁사 가격을 고려한 최종 가격 조정 (소비자 저항선 고려)
    # 만약 경쟁사 평균가가 존재하고, 우리 제안가가 30% 이상 비싸면 조정
    if avg_competitor_price > 0 and suggested_price > avg_competitor_price * 1.3:
        final_price = int(avg_competitor_price * 1.2) # 경쟁사보다 20% 높은 수준으로 재조정
    else:
        final_price = suggested_price
    
    # 100원 단위로 반올림
    final_price = round(final_price / 100) * 100
    final_margin = (1 - (base_cost / final_price)) * 100 if final_price > 0 else 0

    return final_margin, final_price


# ----------------------------------------------------------------------
# 2. Streamlit UI (Front-end)
# ----------------------------------------------------------------------

st.set_page_config(page_title="AI 신제품 마진 제안 시스템", layout="wide")

st.title("🤖 AI 신제품 마진 제안 시스템")
st.write("제품명과 예상 제조원가를 입력하면, AI가 시장 데이터를 분석하여 최적의 마진율과 판매가를 제안합니다.")

# 사용자 입력
product_name = st.text_input("분석할 제품명을 입력하세요:", "타코와사비")
base_cost = st.number_input("제품의 예상 제조원가(1개 당)를 입력하세요 (원):", min_value=100, value=3000, step=100)

if st.button("분석 시작"):
    if not product_name or base_cost <= 0:
        st.error("제품명과 제조원가를 올바르게 입력해주세요.")
    else:
        # Google 검색 API 호출 (실제 호출 대신 시뮬레이션)
        # 이 부분에서 실제 google_search.search 툴을 사용합니다.
        # 아래 with 블록은 실제 API 호출 시 시간이 걸리는 것을 표현합니다.
        with st.spinner(f"'{product_name}'에 대한 시장 데이터를 실시간으로 분석 중입니다... 잠시만 기다려주세요."):
            # -------------------- 구글 검색 쿼리 생성 --------------------
            # 실제로는 이 부분에서 google_search.search 툴 코드가 실행됩니다.
            # print(google_search.search(queries=[
            #     f'"{product_name}" 온라인 구매', 
            #     f'"{product_name}" 가격',
            #     f'"{product_name}" 후기', 
            #     f'"{product_name}" 레시피',
            #     '문어 수입 가격 동향', # '타코와사비'의 원재료 예시
            #     '고추냉이 가격'     # '타코와사비'의 원재료 예시
            # ]))
            # -----------------------------------------------------------
            
            # 아래는 위 검색 결과를 받았다고 가정한 더미 데이터입니다.
            # 실제로는 search_results 변수에 API 결과가 담기게 됩니다.
            # 이 코드를 직접 실행하려면 이 더미 데이터를 사용하게 됩니다.
            search_results = [
                {'index': 1, 'title': f'{product_name} 500g 2개 묶음 판매', 'snippet': '신선한 타코와사비 500g을 12,500원에 만나보세요. 온라인 최저가!'},
                {'index': 2, 'title': f'집에서 즐기는 이자카야! {product_name} 레시피', 'snippet': '간단하게 만드는 타코와사비 레시피를 공유합니다. 많은 분들이 추천하는 방법!'},
                {'index': 3, 'title': '수입 문어 가격 급등, 자숙 문어 가격 20% 인상', 'snippet': '최근 어획량 감소로 인해 수입 문어의 가격이 크게 올랐습니다. 관련 제품 가격 인상이 불가피할 전망입니다.'},
                {'index': 4, 'title': f'{product_name} 솔직 후기', 'snippet': '톡 쏘는 맛이 일품! 맥주 안주로 최고라는 후기가 많아요.'},
                {'index': 5, 'title': '대형마트, {product_name} 1kg 19,800원에 판매 시작', 'snippet': '가성비 좋은 대용량 타코와사비를 구매하세요.'},
                {'index': 6, 'title': '생 고추냉이 가격 동향', 'snippet': '일본산 생 와사비 가격은 안정세를 보이고 있으나, 가공 와사비는 물류비 영향으로 소폭 상승했습니다.'}
            ]
            
            # 분석 모듈 실행
            demand_score, demand_exp, demand_evi = analyze_demand_popularity(product_name, search_results)
            comp_score, avg_price, comp_exp, comp_evi = analyze_competition(product_name, search_results)
            rarity_score, rarity_exp, rarity_evi = analyze_rarity_cost(product_name, search_results)
            
            scores = {
                "demand": demand_score,
                "competition": comp_score,
                "rarity": rarity_score,
                "avg_price": avg_price
            }

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
            st.write("**주요 근거:**")
            for e in demand_evi:
                st.markdown(f"- {e}")

        with st.expander("⚔️ 경쟁 환경 분석 (자세히 보기)"):
            st.metric("경쟁 강도 점수 (높을수록 치열)", f"{comp_score}/10")
            st.write(comp_exp)
            st.write("**주요 근거:**")
            for e in comp_evi:
                st.markdown(f"- {e}")

        with st.expander("💎 원재료 희소성/원가 분석 (자세히 보기)"):
            st.metric("희소성/원가상승 점수 (높을수록 희소)", f"{rarity_score}/10")
            st.write(rarity_exp)
            st.write("**주요 근거:**")
            for e in rarity_evi:
                st.markdown(f"- {e}")

        st.caption("주의: 본 결과는 공개된 웹 정보를 기반으로 한 AI의 자동 분석 결과이며, 최종 의사결정은 담당자의 검토가 필요합니다.")
