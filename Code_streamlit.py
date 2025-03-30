
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import streamlit as st

# Saramin
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

url = 'https://www.saramin.co.kr/zf_user/search?search_area=main&search_done=y&search_optional_item=n&searchType=search&searchword=%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D'
driver.get(url)

wait = WebDriverWait(driver, 10)

html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, 'html.parser')

job_contents = soup.find_all('div', class_='item_recruit')

job = []

for i in job_contents:
    job_info = {}

    job_corp = i.find('strong', class_='corp_name').text.strip()
    job_recruit = i.find('h2', class_='job_tit').text.strip()
    job_detail = i.find('div', class_='job_condition').text.strip()

    job_url = soup.find('a', class_='data_layer')['href']
    base_url = "https://www.saramin.co.kr"
    full_url = base_url + job_url

    job_info['Site'] = 'Saramin'
    job_info['Col_Company'] = job_corp
    job_info['Col_Recruit'] = job_recruit
    job_info['Col_detail'] = [job_detail]
    job_info['Col_url'] = full_url

    job.append(job_info)

df_job = pd.DataFrame(job)

# Job_Korea
# Chrome 드라이버 세팅
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# URL 열기
url = 'https://www.jobkorea.co.kr/Search/?stext=%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B6%84%EC%84%9D&tabType=recruit&Page_No=1'
driver.get(url)

# 페이지 소스 가져오기
wait = WebDriverWait(driver, 10)
html = driver.page_source
driver.quit()

# BeautifulSoup로 HTML 파싱
soup = BeautifulSoup(html, 'html.parser')

# jobkor_contents 추출
jobkor_contents = soup.find_all('article', class_='list')

# 데이터를 저장할 리스트
jobkor = []

# 기본 URL
base_url = "https://www.jobkorea.co.kr"

# jobkor_contents에서 데이터 추출
for i in jobkor_contents:
    jobkor_list = i.find_all('article', class_='list-item')

    for i in jobkor_list:
        jobkor_info = {}

        # 회사명 추출
        jobkor_corp_tag = i.find('a', class_='corp-name-link')
        jobkor_corp = jobkor_corp_tag.get('title')

        # 모집 직무 추출
        jobkor_recruit_tag = i.find('a', class_='information-title-link')
        jobkor_recruit = jobkor_recruit_tag.text.strip()

        # 상세 정보 추출 (줄바꿈 및 불필요한 공백 제거)
        jobkor_detail_tag = i.find('ul', class_='chip-information-group')
        if jobkor_detail_tag:
            jobkor_detail = jobkor_detail_tag.text.strip().replace("\n", " ").replace("\r", "").strip()
        else:
            jobkor_detail = ""

        # 채용 공고 URL 추출
        jobkor_url_tag = i.find('a', class_='information-title-link')
        jobkor_url = jobkor_url_tag['href']
        full_url = base_url + jobkor_url

        # jobkor_info 딕셔너리 초기화
        jobkor_info['Site'] = 'Job_Korea'
        jobkor_info['Col_Company'] = jobkor_corp
        jobkor_info['Col_Recruit'] = jobkor_recruit.strip()
        jobkor_info['Col_detail'] = [jobkor_detail]  # 리스트로 초기화
        jobkor_info['Col_url'] = full_url

        # 혜택 정보 추출 (줄바꿈 및 불필요한 공백 제거)
        jobkor_corp_tags = i.find('ul', class_='chip-benefit-group')
        if jobkor_corp_tags:
            jobkor_benefit_detail = jobkor_corp_tags.text.strip().replace("\n", " ").replace("\r", "").strip()
            jobkor_info['Col_detail'].append(jobkor_benefit_detail)  # 리스트에 추가

        # jobkor 리스트에 jobkor_info 추가
        jobkor.append(jobkor_info)

# DataFrame으로 변환
df_jobkor = pd.DataFrame(jobkor)

# DataFrame 합치기
result = pd.concat([df_job, df_jobkor], axis=0, ignore_index=True)
result = result[['Site', 'Col_Company', 'Col_Recruit']]

# 구인 비율 계산
result_ratio = result.groupby('Site')['Col_Recruit'].count().reset_index().rename(columns={'Col_Recruit': 'Count'})
result_ratio['Ratio'] = round((result_ratio['Count'] / result_ratio['Count'].sum()) * 100, 2)

# CSV 파일로 저장
result.to_csv("result.csv", index=False, encoding="utf-8-sig")
result_ratio.to_csv("result_ratio.csv", index=False, encoding="utf-8-sig")

# Streamlit 캐싱 함수
@st.cache_data
def load_data():
    Saramin_df = pd.read_csv('data_tmp/data_Saramin.csv')
    Job_Korea_df = pd.read_csv('data_tmp/data_jobkorea.csv')
    result_df = pd.read_csv('./result.csv')
    result_ratio_df = pd.read_csv('./result_ratio.csv')
    return Saramin_df, Job_Korea_df, result_df, result_ratio_df

# 데이터 로드
Saramin_df, Job_Korea_df, result_df, result_ratio_df = load_data()

# Streamlit UI
st.title('Title')

# 첫 번째 폼
with st.form('form1', clear_on_submit=True):
    submitted1 = st.form_submit_button('Recruit Searching')
    if submitted1:
        # 데이터프레임 출력
        st.dataframe(result_df)
        st.dataframe(result_ratio_df)

        # 파이 차트 시각화
        fig = px.pie(
            result_ratio,  # 비율 계산된 결과 사용
            names='Site',
            values='Ratio',
            title='Recruitment Ratio'
        )

        # Streamlit에서 Plotly 그래프 출력
        st.plotly_chart(fig)
