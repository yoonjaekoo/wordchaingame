import streamlit as st
import random
import re
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai

API_KEY = "AIzaSyCrFIZ2-ip12rNcqY0UBbpXPn-rcDF5tHs"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemma-3-4b-it')

executor = ThreadPoolExecutor(max_workers=1)

# Streamlit 상태 초기화
for key in ['user_score','gemini_score','current_word','used_words','turn','log','word_input']:
    if key not in st.session_state:
        st.session_state[key] = [] if key=='log' or key=='used_words' else 0 if 'score' in key else ""

def get_duum_equivalent(char):
    if char in ['라','래','로','뢰','루','르']: return chr(ord(char)-1024)
    elif char in ['랴','려','례','료','류']: return chr(ord(char)-512)
    elif char=='리': return '이'
    elif char in ['나','내','노','뇌','누','느']: return chr(ord(char)+1024)
    elif char in ['냐','녀','녜','뇨','뉴']: return chr(ord(char)+512)
    elif char=='니': return '이'
    return None

def is_valid_word(word):
    try:
        prompt = f"'{word}'가 끝말잇기 명사로 유효한지 '네' 또는 '아니오'로만 답해줘."
        resp = model.generate_content(prompt)
        return '네' in resp.text
    except:
        return False

def check_chain(last_char, first_char):
    duum = get_duum_equivalent(last_char)
    return first_char == last_char or (duum and first_char == duum)

def gemini_turn():
    last_char = st.session_state.current_word[-1] if st.session_state.current_word else ""
    duum_equiv = get_duum_equivalent(last_char)
    start_chars = f"'{last_char}'"
    if duum_equiv:
        start_chars += f" 또는 '{duum_equiv}'"
    prompt = f"'{st.session_state.current_word}' 다음에 올 명사 한 단어만 말해줘. 반드시 {start_chars}로 시작. 이미 사용된 단어 제외: {st.session_state.used_words}"
    future = executor.submit(model.generate_content, prompt)
    response = future.result()
    candidates = re.findall(r'[가-힣]+', response.text)
    for cand in candidates:
        if cand not in st.session_state.used_words:
            if not st.session_state.current_word or check_chain(st.session_state.current_word[-1], cand[0]):
                if is_valid_word(cand):
                    st.session_state.used_words.append(cand)
                    st.session_state.current_word = cand
                    st.session_state.gemini_score += 1
                    st.session_state.log.append(f"Gemini: {cand}")
                    st.session_state.turn = "user"
                    return
    st.session_state.log.append("Gemini가 유효한 단어를 찾지 못함. Gemini 패배!")
    st.session_state.turn = "end"

def submit_word():
    word = st.session_state.word_input.strip()
    st.session_state.word_input = ""
    if not word: return
    if not re.fullmatch(r'[가-힣]+', word):
        st.session_state.log.append("한글만 입력해주세요.")
        return
    if st.session_state.current_word:
        if not check_chain(st.session_state.current_word[-1], word[0]):
            st.session_state.log.append(f"끝말이 틀렸습니다! '{word}'는 '{st.session_state.current_word[-1]}' 또는 두음법칙 적용 글자로 시작해야 합니다.")
            st.session_state.turn = "end"
            return
    if word in st.session_state.used_words:
        st.session_state.log.append(f"{word} 이미 사용됨!")
        st.session_state.turn = "end"
        return
    if not is_valid_word(word):
        st.session_state.log.append(f"{word} 유효하지 않음!")
        st.session_state.turn = "end"
        return
    st.session_state.used_words.append(word)
    st.session_state.current_word = word
    st.session_state.user_score += 1
    st.session_state.log.append(f"사용자: {word}")
    st.session_state.turn = "gemini"
    gemini_turn()

def reset_game():
    st.session_state.user_score = 0
    st.session_state.gemini_score = 0
    st.session_state.current_word = ""
    st.session_state.used_words = []
    st.session_state.turn = ""
    st.session_state.log = []
    st.session_state.word_input = ""

st.title("끝말잇기 게임 (Gemini AI + 두음법칙)")

col1, col2 = st.columns(2)
col1.metric("사용자 점수", st.session_state.user_score)
col2.metric("Gemini 점수", st.session_state.gemini_score)

st.text(f"현재 단어: {st.session_state.current_word}")

st.text_input("단어 입력", key="word_input", on_change=submit_word)
st.button("게임 초기화", on_click=reset_game)

st.subheader("게임 로그")
for msg in st.session_state.log:
    st.write(msg)
