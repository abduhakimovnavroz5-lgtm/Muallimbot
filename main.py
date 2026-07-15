import os
import sys
import threading
import sqlite3
import requests
import time
import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Telegram bot tokeni
TOKEN = "8404509030:AAHknnOHP2p5KYHHUJKqk3NxuKcnq1dl6vY"
bot = telebot.TeleBot(TOKEN)

# 2. Ma'lumotlar bazasini va professional darslar zanjirini yaratish
def init_db():
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_number INTEGER NOT NULL, 
        lesson_title TEXT NOT NULL,
        lesson_text TEXT NOT NULL,    
        question_text TEXT NOT NULL,    
        variant_a TEXT NOT NULL,
        variant_b TEXT NOT NULL,
        variant_c TEXT NOT NULL,
        correct_answer TEXT NOT NULL             
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_progress (
        chat_id INTEGER PRIMARY KEY,
        current_lesson INTEGER DEFAULT 1
    )
    """)
    
    # Yangi dars tizimi to'g'ri ishlashi uchun eski foydalanuvchi natijalarini tozalaydi
    cursor.execute("DELETE FROM user_progress")
    
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        arabic_course = [
            (
                1, 
                "1-Dars: Alif harfi va Harakatlar (Fatha, Kasra, Damma)", 
                "Arab alifbosi o'ngdan chapga qarab yoziladi va 28 ta harfdan iborat. Birinchi harf - 'Alif' (A) harfidir. U o'zi mustaqil tovushga ega emas, unga unli tovushni berish uchun Harakatlar (belgilar) ishlatiladi:\n1. Fatha (harf ustidagi chiziq) - 'A' tovushini beradi.\n2. Kasra (harf ostidagi chiziq) - 'I' tovushini beradi.\n3. Damma (harf ustidagi kichik vergul) - 'U' tovushini beradi.",
                "Alif harfining ostiga chiziqcha (kasra) qo'yilsa, u qanday tovush berib o'qiladi?", 
                "A tovushini", "I tovushini", "U tovushini", "B"
            ),
            (
                2, 
                "2-Dars: Ba harfi va uning so'z ichida yozilishi", 
                "Ikkinchi harf - 'Ba' harfi. U o'zbek tilidagi chiziqli 'B' tovushini beradi. Pastida bitta nuqtasi bo'ladi.\nArab harflari so'zdagi o'rniga qarab shaklini o'zgartiradi:\n- Alohida shakli: Ba\n- So'z boshida yozilishi: Ba- (chap tomonga bog'lanadi)\n- So'z o'rtasida yozilishi: -Ba- (ikki tomonga bog'lanadi)\n- So'z oxirida yozilishi: -Ba (o'ng tomonga bog'lanadi)",
                "'Ba' harfining so'z boshida yozilishi qaysi variantda to'g'ri ko'rsatilgan?", 
                "So'z boshida", "So'z o'rtasida", "So'z oxirida", "A"
            ),
            (
                3, 
                "3-Dars: Ta va Sa harflari (Maxraj qoidalari)", 
                "3. 'Ta' harfi - ustida ikkita nuqtasi bor. Oddiy o'zbekcha 'T' tovushini beradi.\n4. 'Sa' harfi - ustida uchta nuqtasi bor. Diqqat qiling, bu harf maxraji (talaffuzi) tishlar orasidan chiqadigan yumshoq, chuchuk 'S' tovushidir. Til uchi oldingi tishlar orasiga bir oz tegib turadi.",
                "Qaysi harf maxraji tishlar orasidan chiqadigan chuchuk 'S' tovushini ifodalaydi?", 
                "Ta harfi", "Ba harfi", "Sa harfi", "C"
            )
        ]
        cursor.executemany("""
        INSERT INTO questions (lesson_number, lesson_title, lesson_text, question_text, variant_a, variant_b, variant_c, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, arabic_course)
    conn.commit()
    conn.close()

init_db()

# 3. Render ulanishi uchun HTTP Web Server
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"MuallimBot faol holatda!")

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), WebServerHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# 🔄 ANTI-UYQU TIZIMI
def keep_alive():
    time.sleep(30)
    while True:
        try:
            requests.get("http://localhost:8000/", timeout=5)
        except:
            pass
        time.sleep(600)

threading.Thread(target=keep_alive, daemon=True).start()

# 4. Foydalanuvchiga joriy darsni yuborish funksiyasi
def send_current_lesson(chat_id):
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_lesson FROM user_progress WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO user_progress (chat_id, current_lesson) VALUES (?, 1)", (chat_id,))
        conn.commit()
        lesson_num = 1
    else:
        lesson_num = row[0]
        
    cursor.execute("SELECT lesson_title, lesson_text, question_text, variant_a, variant_b, variant_c FROM questions WHERE lesson_number = ?", (lesson_num,))
    lesson = cursor.fetchone()
    conn.close()
    
    if lesson:
        matn = f"📖 *{lesson[0]}*\n\n{lesson[1]}\n\n"
        matn += f"❓ *Ushbu dars bo'yicha Savol:* {lesson[2]}\n\n"
        matn += f"A) {lesson[3]}\nB) {lesson[4]}\nC) {lesson[5]}\n\n"
        matn += "👉 Javob berish uchun shunchaki variant harfini (*A, B yoki C*) yozib yuboring."
        bot.send_message(chat_id, matn, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "🎉 *MASHALLOH!* Siz Arab alifbosi darslarini muvaffaqiyatli tugatdingiz! 🕋\n\nSiz endi Arab tilida ilk mustaqil savodxonlik darajasiga erishdingiz. Barakalloh!")

# 5. Bot buyruqlarini boshqarish
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "Assalomu alaykum! *MuallimBot* mukammal ta'lim tizimiga xush kelibsiz! 🕋📚\n\n"
        "Men sizga Arab alifbosini va Arab tilida gaplashishni 0 dan boshlab, bosqichma-bosqich o'rgataman.\n"
        "🛑 *Qat'iy qoida:* Oldingi dars testini to'g'ri topshirmasangiz, keyingi dars ochilmaydi!\n\n"
        "🚀 O'rganishni boshlash uchun /dars buyrug'ini yuboring."
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['dars'])
def start_lesson(message):
    send_current_lesson(message.chat.id)

# 6. Foydalanuvchi javoblarini tekshirish va cheklov tizimi
@bot.message_handler(func=lambda msg: msg.text.upper() in ['A', 'B', 'C'])
def check_answer(message):
    chat_id = message.chat.id
    user_ans = message.text.upper()
    
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT current_lesson FROM user_progress WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    
    if row:
        lesson_num = row[0]
        
        cursor.execute("SELECT correct_answer FROM questions WHERE lesson_number = ?", (lesson_num,))
        correct_row = cursor.fetchone()
        
        if correct_row:
            correct_ans = correct_row[0]
            
            if user_ans == correct_ans:
                next_lesson = lesson_num + 1
                cursor.execute("UPDATE user_progress SET current_lesson = ? WHERE chat_id = ?", (next_lesson, chat_id))
                conn.commit()
                conn.close()
                bot.send_message(chat_id, "✅ *To'g'ri! Barakalloh.* Siz ushbu bosqichdan o'tdingiz. Keyingi dars yuklanmoqda... 👇")
                send_current_lesson(chat_id)
                return

    conn.close()
    bot.send_message(chat_id, "❌ *Noto'g'ri javob.* Siz ushbu dars qoidasini yaxshi o'zlashtirmabsiz. Keyingi bosqich ochilishi uchun dars matnini qayta o'qib ko'ring va qaytadan to'g'ri javob bering!")

if __name__ == "__main__":
    print("MuallimBot ishga tushdi...")
    bot.infinity_polling()
