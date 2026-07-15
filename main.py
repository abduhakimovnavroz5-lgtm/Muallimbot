import os
import threading
import sqlite3
import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Telegram bot tokeni
TOKEN = "8404509030:AAHknnOHP2p5KYHHUJKqk3NxuKcnq1dl6vY"
bot = telebot.TeleBot(TOKEN)

# 2. Ma'lumotlar bazasini va darslar tizimini noldan mukammal yaratish
def init_db():
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Darslar jadvali
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
    
    # Foydalanuvchilarning bosqichlarini saqlash jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_progress (
        chat_id INTEGER PRIMARY KEY,
        current_lesson INTEGER DEFAULT 1
    )
    """)
    
    # Bazani professional darslar zanjiri bilan to'ldirish
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone() == 0:
        arabic_course = [
            (
                1, 
                "1-Dars: Alif (ا) harfi va Harakatlar", 
                "Arab alifbosi o'ngdan chapga qarab yoziladi. Birinchi harf - 'Alif' (ا) harfidir. U o'zi mustaqil tovushga ega emas, unga unli tovushni berish uchun Harakatlar (belgilar) ishlatiladi:\n"
                "1. Fatha (harf ustidagi chiziq) - 'A' tovushini beradi. (اَ - A)\n"
                "2. Kasra (harf ostidagi chiziq) - 'I' tovushini beradi. (اِ - I)\n"
                "3. Damma (harf ustidagi kichik vergul) - 'U' tovushini beradi. (اُ - U)",
                "Alif harfining ostiga chiziqcha (kasra) qo'yilsa, u qanday o'qiladi?", 
                "A", "I", "U", "B"
            ),
            (
                2, 
                "2-Dars: Ba (ب) harfi", 
                "Ikkinchi harf - 'Ba' (ب) harfi. U o'zbek tilidagi chiziqli 'B' tovushini beradi. Pastida bitta nuqtasi bo'ladi.\n"
                "Yozilishi:\n"
                "- Alohida: ب\n"
                "- So'z boshida: بـ\n"
                "- So'z o'rtasida: ـبـ\n"
                "- So'z oxirida: ـب\n"
                "Harakatlar bilan: بَ (Ba), بِ (Bi), بُ (Bu)",
                "'Ba' harfining so'z boshida yozilishi qaysi variantda to'g'ri ko'rsatilgan?", 
                "بـ", "ـبـ", "ـب", "A"
            ),
            (
                3, 
                "3-Dars: Ta (ت) va Sa (ث) harflari", 
                "3. 'Ta' (ت) harfi - ustida ikkita nuqtasi bor. Oddiy 'T' tovushini beradi.\n"
                "4. 'Sa' (ث) harfi - ustida uchta nuqtasi bor. Maxraji tishlar orasidan chiqadigan yumshoq, chuchuk 'S' tovushidir.\n"
                "Harakatlar bilan: تَ (Ta), تِ (Ti), تُ (Tu) | ثَ (Sa), ثِ (Si), ثُ (Su)",
                "Qaysi harf tishlar orasidan chiqadigan chuchuk 'S' tovushini ifodalaydi?", 
                "ت", "ب", "ث", "C"
            )
        ]
        cursor.executemany("""
        INSERT INTO questions (lesson_number, lesson_title, lesson_text, question_text, variant_a, variant_b, variant_c, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, arabic_course)
    conn.commit()
    conn.close()

init_db()

# 3. Render port muammosini oldini olish uchun HTTP Server
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

# 4. Foydalanuvchiga joriy darsni yuborish funksiyasi
def send_current_lesson(chat_id):
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Foydalanuvchi nechanchi darsdaligini aniqlash
    cursor.execute("SELECT current_lesson FROM user_progress WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO user_progress (chat_id, current_lesson) VALUES (?, 1)", (chat_id,))
        conn.commit()
        lesson_num = 1
    else:
        lesson_num = row[0]
        
    # Dars ma'lumotlarini bazadan olish
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
        bot.send_message(chat_id, "🎉 Tabriklaymiz! Siz barcha darslarni muvaffaqiyatli tugatdingiz va Arab tilida ilk savodxonlik darajasiga erishdingiz! Xudo xohlasa tez orada yangi suhbat darslari qo'shiladi.")

# 5. Bot buyruqlarini boshqarish
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "Assalomu alaykum! *MuallimBot* ta'lim platformasiga xush kelibsiz! 🕋📚\n\n"
        "Men sizga Arab alifbosini 0 dan boshlab, bosqichma-bosqich o'rgataman.\n"
        "Har bir darsdan so'ng test bo'ladi, to'g'ri topshirsangiz keyingi dars ochiladi.\n\n"
        "🚀 O'rganishni boshlash uchun /dars buyrug'ini yuboring."
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['dars'])
def start_lesson(message):
    send_current_lesson(message.chat.id)

# 6. Foydalanuvchi javoblarini (A, B, C) tekshirish
@bot.message_handler(func=lambda msg: msg.text.upper() in ['A', 'B', 'C'])
def check_answer(message):
    chat_id = message.chat.id
    user_ans = message.text.upper()
    
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Foydalanuvchining joriy dars raqamini olish
    cursor.execute("SELECT current_lesson FROM user_progress WHERE chat_id = ?", (chat_id,))
    lesson_num = cursor.fetchone()[0]
    
    # To'g'ri javobni bazadan tekshirish
    cursor.execute("SELECT correct_answer FROM questions WHERE lesson_number = ?", (lesson_num,))
    correct_ans = cursor.fetchone()[0]
    
    if user_ans == correct_ans:
        # To'g'ri bo'lsa, darajasini 1 taga oshirish
        next_lesson = lesson_num + 1
        cursor.execute("UPDATE user_progress SET current_lesson = ? WHERE chat_id = ?", (next_lesson, chat_id))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, "✅ To'g'ri! Barakalloh. Keyingi darsga o'tishingiz mumkin. 👇")
        send_current_lesson(chat_id)
    else:
        conn.close()
        bot.send_message(chat_id, "❌ Noto'g'ri javob. Dars matnini qayta o'qib ko'ring va qaytadan javob bering.")

# Botni yuritish
if __name__ == "__main__":
    print("MuallimBot (Aqlli Ustoz) ishga tushdi...")
    bot.infinity_polling()
