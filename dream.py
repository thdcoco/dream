import streamlit as st
import requests
import openai
from datetime import datetime
import re
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI

# OpenAI API 키 설정
openai_api_key = "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"
openai.api_key = openai_api_key

# Naver API 설정
CLIENT_ID = 'kOTwXT4d09oyxlqSO_Vg'
CLIENT_SECRET = 'uKa8vmVcsI'

# Naver 백과사전 검색 API 호출 함수
def search_dream(query):
    url = f"https://openapi.naver.com/v1/search/encyc.json?query={query}"
    headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        st.error(f"백과사전 API 호출 중 오류가 발생했습니다: {e}")
        return None

# HTML 태그 제거 함수
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# LangChain 설정 함수: qa_chain 설정
def get_qa_chain():
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    llm = OpenAI(openai_api_key=openai_api_key)
    memory = ConversationBufferMemory()
    vectorstore = Chroma(embedding_function=embeddings)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return qa_chain

# 한국형 스트레스 척도 설문지 질문과 답변 리스트
def stress_scale_questions():
    questions = [
        "최근 일주일 동안 자주 스트레스를 느꼈습니까?",
        "스트레스가 내 일상에 영향을 미쳤다고 느꼈습니까?",
        "최근에 과중한 업무나 공부를 했습니까?",
        "스트레스가 내가 사는 환경에 영향을 미쳤습니까?",
        "가장 최근의 스트레스 상황에 대해 어떻게 느꼈습니까?"
    ]
    answers = ["매우 그렇다", "그렇다", "보통이다", "아니다", "전혀 아니다"]
    return questions, answers

# 한국형 스트레스 척도를 기반으로 한 메시지 생성 함수
def create_stress_based_message(stress_responses):
    """
    스트레스 응답을 바탕으로 스트레스 수준을 계산하고 적절한 메시지를 생성합니다.
    
    Args:
        stress_responses (list): 설문 응답 리스트.
        
    Returns:
        str: 스트레스 수준에 따른 메시지.
    """
    # 응답 점수 매핑
    score_map = {"매우 그렇다": 5, "그렇다": 4, "보통이다": 3, "아니다": 2, "전혀 아니다": 1}
    scores = [score_map[response] for response in stress_responses]
    
    # 평균 점수 계산
    avg_score = sum(scores) / len(scores)
    
    # 스트레스 수준 결정
    if avg_score <= 2:
        message = "스트레스 수준이 낮습니다. 현재 마음의 안정을 잘 유지하고 계신 것 같아요. 꾸준히 건강한 일상을 유지하세요!"
    elif 2 < avg_score <= 3.5:
        message = "스트레스가 조금 쌓여있는 것 같네요. 작은 휴식과 자기 관리를 통해 스트레스를 해소해보는 건 어떨까요?"
    else:
        message = "스트레스 수준이 높습니다. 당신의 건강과 마음을 위해 충분한 휴식을 취하고 주변에 도움을 요청해보세요. 당신은 소중한 존재입니다!"
    
    return message

# 스트레스 점수에 따른 상태 메시지 출력 함수
def get_stress_level_message(stress_score):
    if stress_score <= 30:
        return "스트레스 수준이 낮습니다. 잘 관리되고 있는 상태입니다."
    elif 31 <= stress_score <= 70:
        return "스트레스 수준이 보통입니다. 적절한 스트레스 관리가 필요할 수 있습니다."
    else:
        return "스트레스 수준이 높습니다. 휴식과 스트레스 해소 방법을 고려해보세요."

# 메인 실행 함수
def run_ui():
    qa_chain = get_qa_chain()

    # CSS를 사용하여 배경색을 그라데이션으로 설정하고, 제목과 검색창의 색상을 변경
    st.markdown("""
        <style>
            .stApp {
                background: linear-gradient(to bottom, #0b1e2e, #f8c9d4);
                color: #ffffff;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("🌙 당신의 밤은 안녕하신가요?")
    st.markdown("이 플랫폼은 사용자의 스트레스 수준을 평가하고, 이를 바탕으로 맞춤형 관리 메시지와 해소 방법을 제공합니다. 사용자는 스트레스 점수를 일간 또는 주간으로 기록하여, 시간이 지나면서 스트레스 패턴을 시각적으로 확인하고 분석할 수 있습니다. 이를 통해 스트레스 수준에 맞는 실질적인 변화를 유도하고, 적절히 대응할 수 있도록 돕습니다.")

    # 검색 기록을 저장할 리스트
    if 'search_history' not in st.session_state:
        st.session_state['search_history'] = []
    
    # 사용자 입력
    dream_description = st.text_area("꿈 설명을 입력하세요", placeholder="예: 숲 속에서 길을 잃고 어둠 속에서 쫓기는 꿈을 꾸었습니다.")
    stress_score = st.slider("스트레스 수준을 선택하세요", 0, 100, 50)

    # 스트레스 척도 설문지
    st.subheader("한국형 스트레스 척도 설문")
    questions, answers = stress_scale_questions()
    stress_responses = []
    
    for question in questions:
        response = st.selectbox(question, answers, index=2)  # 기본값: '보통이다'
        stress_responses.append(response)

    if st.button("해석하기"):
        if dream_description:
            # 스트레스 기반 메시지 생성
            stress_message = create_stress_based_message(stress_responses)
            st.subheader("📊 체감 스트레스 수준")
            st.write(stress_message)

            # 스트레스 점수에 따른 상태 메시지 출력
            stress_level_message = get_stress_level_message(stress_score)
            st.subheader("📊 설문지를 통한 스트레스 수준")
            st.write(stress_level_message)

            # GPT-3를 통한 꿈 해석
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "당신은 꿈 해몽 전문가입니다."},
                          {"role": "user", "content": f"꿈 설명: {dream_description}\n\n스트레스 척도: {stress_responses}"}]
            )
            st.subheader("어젯밤 꿈의 해석")
            st.write(response['choices'][0]['message']['content'])

            # 네이버 검색
            st.subheader("🔍 관련 자료")
            naver_results = search_dream(dream_description + " 꿈 해몽")  # 네이버 검색 함수 호출
            if naver_results:
                for result in naver_results:
                    title = remove_html_tags(result['title'])
                    description = remove_html_tags(result['description'])
                    st.write(f"- **{title}**: {description} [Read more]({result['link']})")
            else:
                st.write("네이버 검색 결과가 없습니다.")

            # 검색 기록 저장
            search_record = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {dream_description}"
            st.session_state['search_history'].append(search_record)
        else:
            st.warning("꿈 설명을 입력해주세요!")

    # 사이드바에 검색 기록 표시
    st.sidebar.title("지난 밤 꿈 기록")
    for i, record in enumerate(st.session_state['search_history']):
        if st.sidebar.button(f"{i + 1}. {record}"):
            st.session_state['selected_record'] = record

    # 선택된 검색 기록 표시
    if 'selected_record' in st.session_state:
        st.write(f"Selected Record: {st.session_state['selected_record']}")

# 실행
if __name__ == "__main__":
    run_ui()
