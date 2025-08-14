import random
import google.generativeai as genai
import re
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# --- Gemini API 설정 ---
# API 키를 환경 변수로 설정하는 것을 권장하지만, 테스트를 위해 직접 입력합니다.
API_KEY = "AIzaSyDw0PZ2k2wfN2f22lJUpiMLl-HbJy-rBWg"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemma-3-4b-it')

# API 호출을 위한 스레드 풀
executor = ThreadPoolExecutor(max_workers=1)

# ipywidgets를 사용할 수 있는지 확인 (Jupyter 환경)
try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output
    IS_JUPYTER = True
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    IS_JUPYTER = False

class WordChainGame:
    def __init__(self, root=None):
        self.root = root
        self.user_score = 0
        self.gemini_score = 0
        self.current_word = ""
        self.used_words = []
        self.turn = ""
        self.is_running = False

        if IS_JUPYTER:
            self.create_ipywidgets_widgets()
            self.display_ipywidgets_rps()
        else:
            self.root.title("Gemini 끝말잇기")
            self.create_tkinter_widgets()
            self.display_tkinter_rps()
    
    # --- ipywidgets 관련 함수 ---
    def create_ipywidgets_widgets(self):
        # 가위바위보 위젯
        self.rps_label = widgets.Label(value="가위바위보로 선공 정하기!")
        self.rock_btn = widgets.Button(description="바위")
        self.scissors_btn = widgets.Button(description="가위")
        self.paper_btn = widgets.Button(description="보")
        self.rps_result_label = widgets.Label(value="")
        self.rock_btn.on_click(lambda b: self.play_rps("바위"))
        self.scissors_btn.on_click(lambda b: self.play_rps("가위"))
        self.paper_btn.on_click(lambda b: self.play_rps("보"))
        self.rps_box = widgets.VBox([self.rps_label, widgets.HBox([self.rock_btn, self.scissors_btn, self.paper_btn]), self.rps_result_label])

        # 게임 진행 위젯
        self.current_word_label = widgets.Label(value="현재 단어: ")
        self.turn_label = widgets.Label(value="차례: ")
        self.word_entry = widgets.Text(placeholder='단어를 입력하세요...', description='')
        self.submit_btn = widgets.Button(description="제출")
        self.status_label = widgets.Label(value="")
        self.log_text = widgets.Textarea(value='', description='게임 로그:', layout=widgets.Layout(height='150px', width='auto'), disabled=True)
        self.submit_btn.on_click(self.submit_word)
        self.game_box = widgets.VBox([
            self.current_word_label, self.turn_label, self.word_entry, self.submit_btn, self.status_label, self.log_text
        ])

    def display_ipywidgets_rps(self):
        clear_output()
        display(self.rps_box)
        
    def display_ipywidgets_game(self):
        clear_output()
        display(self.game_box)

    def log_ipywidgets(self, message):
        self.log_text.value += message + "\n"

    # --- tkinter 관련 함수 ---
    def create_tkinter_widgets(self):
        self.rps_frame = tk.Frame(self.root)
        self.rps_frame.pack()
        self.rps_label = tk.Label(self.rps_frame, text="가위바위보로 선공 정하기!", font=("맑은 고딕", 16))
        self.rps_label.pack(pady=20)
        rps_button_frame = tk.Frame(self.rps_frame)
        rps_button_frame.pack()
        self.rock_btn = tk.Button(rps_button_frame, text="바위", command=lambda: self.play_rps("바위"), font=("맑은 고딕", 12))
        self.scissors_btn = tk.Button(rps_button_frame, text="가위", command=lambda: self.play_rps("가위"), font=("맑은 고딕", 12))
        self.paper_btn = tk.Button(rps_button_frame, text="보", command=lambda: self.play_rps("보"), font=("맑은 고딕", 12))
        self.rock_btn.pack(side=tk.LEFT, padx=10)
        self.scissors_btn.pack(side=tk.LEFT, padx=10)
        self.paper_btn.pack(side=tk.LEFT, padx=10)
        self.rps_result_label = tk.Label(self.rps_frame, text="", font=("맑은 고딕", 14))
        self.rps_result_label.pack(pady=20)

        self.game_frame = tk.Frame(self.root)
        self.game_frame.pack_forget()
        self.current_word_label = tk.Label(self.game_frame, text="현재 단어: ", font=("맑은 고딕", 14))
        self.current_word_label.pack(pady=(10, 5))
        self.turn_label = tk.Label(self.game_frame, text="차례: ", font=("맑은 고딕", 12))
        self.turn_label.pack(pady=(0, 10))
        self.word_entry = tk.Entry(self.game_frame, font=("맑은 고딕", 12), width=30)
        self.word_entry.pack(pady=5)
        self.word_entry.bind("<Return>", self.submit_word)
        self.submit_btn = tk.Button(self.game_frame, text="제출", command=self.submit_word, font=("맑은 고딕", 12))
        self.submit_btn.pack(pady=5)
        self.status_label = tk.Label(self.game_frame, text="", font=("맑은 고딕", 12), fg="blue")
        self.status_label.pack(pady=5)
        self.log_text = tk.Text(self.game_frame, height=10, width=50, state=tk.DISABLED, font=("맑은 고딕", 10))
        self.log_text.pack(pady=10)
        self.reset_btn = tk.Button(self.game_frame, text="게임 다시 시작", command=self.reset_game, font=("맑은 고딕", 12))
        self.reset_btn.pack(pady=10)
        self.reset_btn.pack_forget()

    def display_tkinter_rps(self):
        self.rps_frame.pack()
    
    def display_tkinter_game(self):
        self.rps_frame.pack_forget()
        self.game_frame.pack()
        self.log_text.delete('1.0', tk.END)

    def log_tkinter(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    # --- 공통 게임 로직 ---
    def play_rps(self, user_choice):
        choices = ["가위", "바위", "보"]
        gemini_choice = random.choice(choices)
        result_text = f"나: {user_choice}, Gemini: {gemini_choice}\n"
        
        if IS_JUPYTER:
            self.rps_result_label.value = result_text
        else:
            self.rps_result_label.config(text=result_text)

        if user_choice == gemini_choice:
            result_text += "비겼습니다! 다시 하세요."
        elif (user_choice == "가위" and gemini_choice == "보") or \
             (user_choice == "바위" and gemini_choice == "가위") or \
             (user_choice == "보" and gemini_choice == "바위"):
            result_text += "이겼습니다! 당신이 먼저 시작합니다."
            self.turn = "user"
            self.start_game()
        else:
            result_text += "졌습니다! Gemini가 먼저 시작합니다."
            self.turn = "gemini"
            self.start_game()
        
        if IS_JUPYTER:
            self.rps_result_label.value = result_text
        else:
            self.rps_result_label.config(text=result_text)


    def start_game(self):
        self.is_running = True
        if IS_JUPYTER:
            self.display_ipywidgets_game()
        else:
            self.display_tkinter_game()
        self.log_message("게임 시작!")

        if self.turn == "gemini":
            self.log_message("Gemini 차례입니다...")
            self.update_turn_label("차례: Gemini")
            if IS_JUPYTER:
                self.gemini_turn_start()
            else:
                self.root.after(1000, self.gemini_turn_start)
        else:
            self.update_game_status("당신 차례입니다. 단어를 입력하세요.")
            self.update_turn_label("차례: 사용자")

    def get_duum_equivalent(self, char):
        if char in ['라', '래', '로', '뢰', '루', '르']: return chr(ord(char) - 1024)
        elif char in ['랴', '려', '례', '료', '류']: return chr(ord(char) - 512)
        elif char == '리': return '이'
        elif char in ['나', '내', '노', '뇌', '누', '느']: return chr(ord(char) + 1024)
        elif char in ['냐', '녀', '녜', '뇨', '뉴']: return chr(ord(char) + 512)
        elif char == '니': return '이'
        return None

    def _is_valid_word(self, word_to_check):
        check_prompt = f"'{word_to_check}' 이 단어가 한글 표준어 사전에 등재된 유효한 단어인지, 그리고 끝말잇기 게임에서 명사로 사용될 수 있는 단어인지 '네' 또는 '아니오'로만 대답해줘. 만약 애매하면 '아니오'라고 해줘. 추가 설명은 하지 마."
        try:
            response = model.generate_content(check_prompt)
            check_text = response.text.strip().lower()
            self.log_message(f"단어 유효성 체크 응답 ('{word_to_check}'): {check_text}")
            return "네" in check_text
        except Exception as e:
            self.log_message(f"단어 유효성 체크 중 오류: {e}")
            return False

    def submit_word(self, event=None):
        if self.turn != "user":
            self.update_game_status("아직 당신 차례가 아닙니다.")
            return

        if IS_JUPYTER:
            word = self.word_entry.value.strip()
            self.word_entry.value = ""
        else:
            word = self.word_entry.get().strip()
            self.word_entry.delete(0, tk.END)

        if not word:
            self.update_game_status("단어를 입력해주세요.")
            return

        if not re.fullmatch(r'[가-힣]+', word):
            self.update_game_status("유효하지 않은 단어입니다. 한글만 입력하세요.")
            return
        
        self.update_game_status("사용자 단어 유효성 검사 중...")
        if not IS_JUPYTER:
            self.root.update_idletasks()

        if not self._is_valid_word(word):
            self.end_game(f"사용자가 제시한 단어 '{word}'는 유효한 단어가 아닙니다! 당신 패배!")
            return

        if self.current_word:
            last_char = self.current_word[-1]
            first_char = word[0]
            duum_equiv = self.get_duum_equivalent(last_char)
            if not (first_char == last_char or (duum_equiv and first_char == duum_equiv)):
                self.end_game("끝말이 틀렸습니다! (두음 법칙 포함) 당신 패배!")
                return

        if word in self.used_words:
            self.end_game("이미 사용된 단어입니다! 당신 패배!")
            return

        self.used_words.append(word)
        self.current_word = word
        self.update_current_word_label(f"현재 단어: {self.current_word}")
        self.user_score += 1
        self.log_message(f"사용자: '{word}'")
        self.update_game_status(f"'{word}' 제출. Gemini 차례입니다.")
        self.turn = "gemini"
        self.update_turn_label("차례: Gemini")
        if IS_JUPYTER:
            self.gemini_turn_start()
        else:
            self.root.after(1000, self.gemini_turn_start)

    def gemini_turn_start(self):
        prompt = ""
        if not self.current_word:
            prompt = "한글 끝말잇기 게임의 첫 단어 하나만 말해줘. (명사)"
        else:
            last_char = self.current_word[-1]
            duum_equiv = self.get_duum_equivalent(last_char)
            start_chars = f"'{last_char}'"
            if duum_equiv:
                start_chars += f" 또는 '{duum_equiv}'"
            prompt = f"한글 끝말잇기 게임에서 '{self.current_word}' 다음에 올 수 있는 명사 한 단어만 말해줘. 반드시 {start_chars}으로 시작해야 하고, 이미 사용된 단어는 {self.used_words} 이야. 이 단어들을 제외하고 가장 적합한 한 단어만."
        
        try:
            future = executor.submit(model.generate_content, prompt)
            response = future.result()
            gemini_raw_text = response.text.strip()
            self.log_message(f"Gemini 원본 응답: {gemini_raw_text}")

            gemini_word_candidates = re.findall(r'[가-힣]+', gemini_raw_text)
            gemini_word = ""
            
            if gemini_word_candidates:
                for cand_word in gemini_word_candidates:
                    if (cand_word not in self.used_words):
                        last_char = self.current_word[-1] if self.current_word else cand_word[0]
                        first_char = cand_word[0]
                        duum_equiv = self.get_duum_equivalent(last_char)
                        
                        if first_char == last_char or (duum_equiv and first_char == duum_equiv):
                            if self._is_valid_word(cand_word):
                                gemini_word = cand_word
                                break
                            else:
                                self.log_message(f"Gemini가 제시한 단어 '{cand_word}'는 유효하지 않음.")
                                
            if not gemini_word:
                self.end_game("Gemini가 유효한 단어를 찾지 못했거나, 제시한 단어가 사전에 없는 단어입니다! Gemini 패배!")
                return

            if gemini_word in self.used_words:
                self.end_game(f"Gemini가 이미 사용된 단어 '{gemini_word}'를 말했습니다! Gemini 패배!")
                return

            self.used_words.append(gemini_word)
            self.current_word = gemini_word
            self.update_current_word_label(f"현재 단어: {self.current_word}")
            self.gemini_score += 1
            self.log_message(f"Gemini: '{gemini_word}'")
            self.update_game_status(f"Gemini: '{gemini_word}' 당신 차례입니다.")
            self.turn = "user"
            self.update_turn_label("차례: 사용자")

        except Exception as e:
            self.log_message(f"Gemini API 호출 중 오류 발생: {e}")
            self.end_game("Gemini가 단어를 생성하지 못했습니다! (API 오류로 인한 Gemini 패배)")

    def update_game_status(self, message):
        if IS_JUPYTER:
            self.status_label.value = message
        else:
            self.status_label.config(text=message)

    def update_turn_label(self, message):
        if IS_JUPYTER:
            self.turn_label.value = message
        else:
            self.turn_label.config(text=message)

    def update_current_word_label(self, message):
        if IS_JUPYTER:
            self.current_word_label.value = message
        else:
            self.current_word_label.config(text=message)

    def log_message(self, message):
        if IS_JUPYTER:
            self.log_ipywidgets(message)
        else:
            self.log_tkinter(message)

    def end_game(self, reason):
        self.is_running = False
        self.log_message(f"\n게임 종료! 이유: {reason}")
        self.log_message(f"최종 점수: 사용자 {self.user_score} vs Gemini {self.gemini_score}")
        if IS_JUPYTER:
            self.submit_btn.disabled = True
            self.word_entry.disabled = True
            # ipywidgets는 리셋 버튼이 필요 없음
        else:
            self.submit_btn.config(state=tk.DISABLED)
            self.word_entry.config(state=tk.DISABLED)
            self.reset_btn.pack(pady=10)
    
    def reset_game(self):
        self.user_score = 0
        self.gemini_score = 0
        self.current_word = ""
        self.used_words = []
        self.turn = ""
        if IS_JUPYTER:
            self.rps_result_label.value = ""
            self.log_text.value = ""
            self.submit_btn.disabled = False
            self.word_entry.disabled = False
            self.display_ipywidgets_rps()
        else:
            self.rps_result_label.config(text="")
            self.log_text.delete('1.0', tk.END)
            self.submit_btn.config(state=tk.NORMAL)
            self.word_entry.config(state=tk.NORMAL)
            self.reset_btn.pack_forget()
            self.game_frame.pack_forget()
            self.rps_frame.pack()

if __name__ == "__main__":
    if IS_JUPYTER:
        game = WordChainGame()
    else:
        root = tk.Tk()
        game = WordChainGame(root)
        root.mainloop()
