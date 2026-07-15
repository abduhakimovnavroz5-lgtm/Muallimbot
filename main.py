import os
import sys
import threading
import sqlite3
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Telegram bot tokeni va aloqa manzili
BOT_TOKEN = "8404509030:AAHknnOHP2p5KYHHUJKqk3NxuKcnq1dl6vY"
API_URL = f"https://telegram.org{BOT_TOKEN}/"

# 2. Arab tili darslari va savollar bazasini yaratish
def init_db():
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Darslar va savollar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level_name TEXT NOT NULL,       
        lesson_number INTEGER NOT NULL, 
        question_text TEXT NOT NULL,    
        variant_a TEXT,
        variant_b TEXT,
        variant_c TEXT,
        correct_answer TEXT             
    )
    """)
    
    # Baza bo'sh bo'lsa, ichini professional Arab tili darslari bilan to'ldirish
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        arabic_lessons = [
            # 1-daraja: Alifbo darslari
            ("Alifbo", 1, "Arab alifbosining birinchi harfi qaysi va u qanday tovushni beradi?", "ب (Ba)", "ا (Alif)", "ت (Ta)", "B"),
            ("Alifbo", 2, "Qaysi harf maxraji (talaffuzi) tishlar orasidan chiqadigan chuchuk tovush hisoblanadi?", "ث (Saa)", "ج (Jiym)", "ح (Haa)", "A"),
            ("Alifbo", 3, "Arab tilida harflarni qisqa cho'zib o'qishni ta'minlaydigan belgilar (A, I, U) nima deyiladi?", "Harakatlar (Harakat)", "Sukun", "Tashdid", "A"),
            
            # 2-daraja: So'zlashuv boshlang'ich
            ("So'zlashuv", 1, "Arab tilida 'Sizga tinchlik bo'lsin' (Assalomu alaykum) iborasiga qanday javob qaytariladi?", "Ahlan va sahlan", "Va alaykum assalom", "Shukran", "B"),
            ("So'zlashuv", 2, "Suhbatdoshdan hol-ahvol so'rash uchun qaysi ibora ishlatiladi?", "Kayfa haluk?", "Masmuka?", "Min ayna anta?", "A")
        ]
        cursor.executemany("""
        INSERT INTO questions (level_name, lesson_number, question_text, variant_a, variant_b, variant_c, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, arabic_lessons)
        print("Arab tili ta'lim tizimi bazaga muvaffaqiyatli yuklandi!")
        
    conn.commit()
    conn.close()

# Bazani ishga tushirish
init_db()

# 3. Render ulanishi uchun HTTP Web Server (Render talab qiladigan portni ushlab turadi)
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"MuallimBot (Arab tili ustozi) muvaffaqiyatli ishlamoqda!")

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), WebServerHandler)
    server.serve_forever()

# Veb serverni alohida oqimda (thread) orqa fonda ishga tushiramiz
threading.Thread(target=run_web_server, daemon=True).start()

# 4. Telegram orqali xabarlarni yuborish funksiyasi
def send_msg(chat_id, text):
    requests.post(f"{API_URL}sendMessage", json={"chat_id": chat_id, "text": text})

# 5. Telegram Botning asosiy ishlash sikli (Polling)
def check_updates():
    offset = 0
    print("MuallimBot foydalanuvchilarni kutmoqda...")
    while True:
        try:
            response = requests.get(f"{API_URL}getUpdates", params={"offset": offset, "timeout": 20}, timeout=25)
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    for update in result["result"]:
                        offset = update["update_id"] + 1
                        
                        if "message" in update and "text" in update["message"]:
                            chat_id = update["message"]["chat"]["id"]
                            text = update["message"]["text"]
                            
                            # /start bosilganda kutib olish va menyu
                            if text == "/start":
                                menu = (
                                    "Assalomu alaykum! MuallimBot-ga xush kelibsiz! 📚\n\n"
                                    "Men sizga Arab alifbosini va Arab tilida gaplashishni noldan boshlab o'rgataman.\n\n"
                                    "Quyidagi buyruqlarni yuboring:\n"
                                    "📖 /alifbo - Harflarni o'rganish va test topshirish\n"
                                    "🗣 /sozlashuv - Kundalik gaplarni o'rganish"
                                )
                                send_msg(chat_id, menu)
                            
                            # Alifbo darajasidagi savollar (Indekslar 100% to'g'rilandi)
                            elif text == "/alifbo":
                                conn = sqlite3.connect('radar_base.db')
                                cursor = conn.cursor()
                                cursor.execute("SELECT question_text, variant_a, variant_b, variant_c FROM questions WHERE level_name='Alifbo' ORDER BY RANDOM() LIMIT 1")
                                row = cursor.fetchone()
                                conn.close()
                                
                                if row:
                                    savol = f"🟢 Alifbo darsi:\n\n{row[0]}\n\nA) {row[1]}\nB) {row[2]}\nC) {row[3]}"
                                    send_msg(chat_id, savol)
                            
                            # So'zlashuv darajasidagi savollar (Indekslar 100% to'g'rilandi)
                            elif text == "/sozlashuv":
                                conn = sqlite3.connect('radar_base.db')
                                cursor = conn.cursor()
                                cursor.execute("SELECT question_text, variant_a, variant_b, variant_c FROM questions WHERE level_name='So'zlashuv' ORDER BY RANDOM() LIMIT 1")
                                row = cursor.fetchone()
                                conn.close()
                                
                                if row:
                                    savol = f"🔵 So'zlashuv darsi:\n\n{row[0]}\n\nA) {row[1]}\nB) {row[2]}\nC) {row[3]}"
                                    send_msg(chat_id, savol)
                                    
        except Exception as e:
            print(f"Tizimda xatolik yuz berdi: {e}")

if __name__ == "__main__":
    check_updates()
