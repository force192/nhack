import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# 쿠키와 헤더 설정
cookies = {
    'NNB': '5PKUTZRSHAVWO',
    'ASID': '79854401000001931918e1ca00000024',
    '_fwb': '137REjJvNHr4B42NtpaC4vG.1731647952337',
    'landHomeFlashUseYn': 'Y',
    'wcs_bt': '4f99b5681ce60:1732758828',
    'nstore_session': 'Ct/+4C8hvyBZ1HoVUJQXchfS',
    'realestate.beta.lastclick.cortar': '1100000000',
}

headers = {
    'accept': '*/*',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3MzU4NjgzODQsImV4cCI6MTczNTg3OTE4NH0.LZ0qdRkLs-4rIekf_7YUWyXf4EOjw2pCvbj1Mej7zDo',
    'referer': 'https://new.land.naver.com/complexes/1081?ms=37.524355,127.054401,17&a=APT:PRE:ABYG:JGC&e=RETAIL',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

def fetch_real_estate_data(page):
    url = f'https://new.land.naver.com/api/articles/complex/1081'
    params = {
        'realEstateType': 'APT:PRE:ABYG:JGC',
        'tradeType': '',
        'rentPriceMin': 0,
        'rentPriceMax': 900000000,
        'priceMin': 0,
        'priceMax': 900000000,
        'areaMin': 0,
        'areaMax': 900000000,
        'page': page,
        'type': 'list',
        'order': 'rank'
    }

    try:
        response = requests.get(url, cookies=cookies, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"데이터를 가져오는 중 오류 발생: {e}")
        return None

# Streamlit 앱
def main():
    st.title("네이버 부동산 데이터 조회 및 분석")
    st.write("1부터 30페이지까지 데이터를 조회한 뒤, 날짜별로 중개사 이름을 구분하여 등록된 매물을 분석할 수 있습니다.")

    # 전체 데이터 가져오기
    if st.button("데이터 조회"):  
        with st.spinner("데이터를 가져오는 중... 잠시만 기다려주세요."):
            all_data = []
            for page in range(1, 31):
                data = fetch_real_estate_data(page)
                if data and "articleList" in data:
                    all_data.extend(data["articleList"])

            if all_data:
                st.success("30페이지 데이터 조회 성공!")
                df = pd.DataFrame(all_data)

                # 날짜별 중개사 이름 구분하여 등록된 매물 수 집계
                st.subheader("날짜별 중개사 등록 매물 통계")
                if "articleConfirmYmd" in df.columns:
                    df["articleConfirmYmd"] = pd.to_datetime(df["articleConfirmYmd"], format="%Y%m%d")
                    daily_realtor_stats = df.groupby(["articleConfirmYmd", "realtorName"]).size().unstack(fill_value=0)

                    st.line_chart(daily_realtor_stats)

                # 주요 열 선택
                display_columns = [
                    "articleName", "tradeTypeName", "dealOrWarrantPrc",
                    "areaName", "direction", "buildingName", "realtorName", "cpName"
                ]

                # 필터링 옵션 설정
                st.subheader("필터 옵션")
                trade_type_filter = st.multiselect(
                    "거래 유형 필터:", options=df["tradeTypeName"].unique(), default=[]
                )
                realtor_filter = st.multiselect(
                    "중개사 이름 필터:", options=df["realtorName"].unique(), default=[]
                )

                # 필터 적용
                filtered_df = df
                if trade_type_filter:
                    filtered_df = filtered_df[filtered_df["tradeTypeName"].isin(trade_type_filter)]
                if realtor_filter:
                    filtered_df = filtered_df[filtered_df["realtorName"].isin(realtor_filter)]

                # 필터링된 데이터 표시
                st.subheader("필터링된 데이터")
                st.dataframe(filtered_df[display_columns])

                # 중개사별 거래 유형 통계 생성 및 합계 추가
                st.subheader("중개사별 거래 유형 통계")
                summary = df.groupby(["realtorName", "tradeTypeName"]).size().unstack(fill_value=0)
                summary["합계"] = summary.sum(axis=1)
                summary = summary.sort_values("합계", ascending=False)
                st.dataframe(summary)

                # cpName별 합계 추가
                st.subheader("cpName별 매물 통계")
                cpname_summary = df.groupby("cpName").size().reset_index(name="매물 수")
                cpname_summary = cpname_summary.sort_values("매물 수", ascending=False)
                st.dataframe(cpname_summary)

                # 중복 매물 표시
                st.subheader("중개사별 중복 매물 통계")
                duplicate_counts = df.duplicated(subset=["articleName", "realtorName"], keep=False)
                duplicate_df = df[duplicate_counts]
                st.dataframe(duplicate_df[["articleName", "realtorName"]].value_counts().reset_index(name="중복 횟수"))

                # 데이터 요약 정보 표시
                st.subheader("데이터 요약")
                st.write(f"총 매물 수: {len(filtered_df)}건")
            else:
                st.error("데이터를 가져올 수 없습니다.")

if __name__ == "__main__":
    main()
