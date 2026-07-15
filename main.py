import os
import threading
import sqlite3
import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Telegram bot tokeni 
TOKEN = "8404509030:AAHknnOHP2p5KYHHUJKqk3NxuKcnq1dl6vY"
bot = telebot.TeleBot(TOKEN)

# 2. Arab tili darslari va savollar bazasini yaratish
def init_db():
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
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
    
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone() == 0:
        # Tutuq belgisi muammosini hal qilish uchun "Sozlashuv" deb yozildi
        arabic_lessons = [
            ("Alifbo", 1, "Arab alifbosining birinchi harfi qaysi va u qanday tovushni beradi?", "ب (Ba)", "ا (Alif)", "ت (Ta)", "B"),
            ("Alifbo", 2, "Qaysi harf maxraji (talaffuzi) tishlar orasidan chiqadigan chuchuk tovush hisoblanadi?", "ث (Saa)", "ج (Jiym)", "ح (Haa)", "A"),
            ("Alifbo", 3, "Arab tilida harflarni qisqa cho'zib o'qishni ta'minlaydigan belgilar (A, I, U) nima deyiladi?", "Harakatlar (Harakat)", "Sukun", "Tashdid", "A"),
            ("Sozlashuv", 1, "Arab tilida 'Sizga tinchlik bo'lsin' iborasiga qanday javob qaytariladi?", "Ahlan va sahlan", "Va alaykum assalom", "Shukran", "B"),
            ("Sozlashuv", 2, "Suhbatdoshdan hol-ahvol so'rash uchun qaysi ibora ishlatiladi?", "Kayfa haluk?", "Masmuka?", "Min ayna anta?", "A")
        ]
        cursor.executemany("""
        INSERT INTO questions (level_name, lesson_number, question_text, variant_a, variant_b, variant_c, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, arabic_lessons)
    conn.commit()
    conn.close()

init_db()

# 3. Render ulanishi uchun HTTP Web Server
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"MuallimBot (Telebot versiyasi) muvaffaqiyatli ishlamoqda!")

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), WebServerHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# 4. Telebot orqali xabarlarni qayta ishlash
@bot.message_handler(commands=['start'])
def send_welcome(message):
    menu = (
        "Assalomu alaykum! MuallimBot-ga xush kelibsiz! 📚\n\n"
        "Men sizga Arab alifbosini noldan boshlab o'rgataman.\n\n"
        "Quyidagi buyruqlarni yuboring:\n"
        "📖 /alifbo - Harflarni o'rganish va test topshirish\n"
        "🗣 /sozlashuv - Kundalik gaplarni o'rganish"
    )
    bot.reply_to(message, menu)

@bot.message_handler(commands=['alifbo'])
def send_alifbo(message):
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    cursor.execute("SELECT question_text, variant_a, variant_b, variant_c FROM questions WHERE level_name='Alifbo' ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        savol = f"🟢 Alifbo darsi:\n\n{row[0]}\n\nA) {row[1]}\nB) {row[2]}\nC) {row[3]}"
        bot.send_message(message.chat.id, savol)

@bot.message_handler(commands=['sozlashuv'])
def send_sozlashuv(message):
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    # Bu yerda ham daraja nomi o'zgartirildi
    cursor.execute("SELECT question_text, variant_a, variant_b, variant_c FROM questions WHERE level_name='Sozlashuv' ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        savol = f"🔵 So'zlashuv darsi:\n\n{row[0]}\n\nA) {row[1]}\nB) {row[2]}\nC) {row[3]}"
        bot.send_message(message.chat.id, savol)

# Botni ishga tushiramiz
if __name__ == "__main__":
    print("MuallimBot (Telebot) ishga tushdi...")
    bot.infinity_polling()
