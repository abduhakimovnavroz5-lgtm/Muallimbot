import os
import threading
import sqlite3
import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Telegram bot tokeni
TOKEN = "8404509030:AAHknnOHP2p5KYHHUJKqk3NxuKcnq1dl6vY"
bot = telebot.TeleBot(TOKEN)

# 2. Ma'lumotlar bazasini va professional darslar zanjirini yaratish
def init_db():
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Darslar va testlar jadvali
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
    
    # Foydalanuvchilarning bosqichlarini (Level) saqlash jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_progress (
        chat_id INTEGER PRIMARY KEY,
        current_lesson INTEGER DEFAULT 1
    )
    """)
    
    # Bazani professional darajali Arab tili darslari bilan to'ldirish
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone() == 0:
        arabic_course = [
            (
                1, 
                "1-Dars: Alif (ا) harfi va Harakatlar (Fatha, Kasra, Damma)", 
                "Arab alifbosi o'ngdan chapga qarab yoziladi va 28 ta harfdan iborat. Birinchi harf - 'Alif' (ا) harfidir. U o'zi mustaqil tovushga ega emas, unga unli tovushni berish uchun Harakatlar (belgilar) ishlatiladi:\n"
                "1. Fatha (harf ustidagi chiziq) - 'A' tovushini beradi. (اَ - A)\n"
                "2. Kasra (harf ostidagi chiziq) - 'I' tovushini beradi. (اِ - I)\n"
                "3. Damma (harf ustidagi kichik vergul) - 'U' tovushini beradi. (اُ - U)",
                "Alif harfining ostiga chiziqcha (kasra) qo'yilsa, u qanday tovush berib o'qiladi?", 
                "A tovushini", "I tovushini", "U tovushini", "B"
            ),
            (
                2, 
                "2-Dars: Ba (ب) harfi va uning so'z ichida yozilishi", 
                "Ikkinchi harf - 'Ba' (ب) harfi. U o'zbek tilidagi chiziqli 'B' tovushini beradi. Pastida bitta nuqtasi bo'ladi.\n"
                "Arab harflari so'zdagi o'rniga qarab shaklini o'zgartiradi:\n"
                "- Alohida shakli: ب\n"
                "- So'z boshida yozilishi: بـ (chap tomonga bog'lanadi)\n"
                "- So'z o'rtasida yozilishi: ـبـ (ikki tomonga bog'lanadi)\n"
                "- So'z oxirida yozilishi: ـب (o'ng tomonga bog'lanadi)\n"
                "Harakatlar bilan: بَ (Ba), بِ (Bi), بُ (Bu)",
                "'Ba' harfining so'z boshida yozilishi qaysi variantda to'g'ri ko'rsatilgan?", 
                "بـ", "ـبـ", "ـب", "A"
            ),
            (
                3, 
                "3-Dars: Ta (ت) va Sa (ث) harflari (Maxraj qoidalari)", 
                "3. 'Ta' (ت) harfi - ustida ikkita nuqtasi bor. Oddiy o'zbekcha 'T' tovushini beradi.\n"
                "4. 'Sa' (ث) harfi - ustida uchta nuqtasi bor. Diqqat qiling, bu harf maxraji (talaffuzi) tishlar orasidan chiqadigan yumshoq, chuchuk 'S' tovushidir. Til uchi oldingi tishlar orasiga bir oz tegib turadi.\n"
                "Harakatlar bilan: تَ (Ta), تِ (Ti), تُ (Tu) | ثَ (Sa), ثِ (Si), ثُ (Su)",
                "Qaysi harf maxraji tishlar orasidan chiqadigan chuchuk 'S' tovushini ifodalaydi?", 
                "ت (Ta)", "ب (Ba)", "ث (Sa)", "C"
            ),
            (
                4, 
                "4-Dars: Tanvin qoidasi (An, In, Un belgilari)", 
                "Harakatlar ikki barobar ko'paytirilsa (ikki fatha, ikki kasra, ikki damma), bu qoida 'Tanvin' deyiladi va so'z oxirida 'N' tovushini o'qishni talab qiladi:\n"
                "1. Tanvin fatha (ً ) - 'AN' deb o'qiladi.\n"
                "2. Tanvin kasra (ٍ ) - 'IN' deb o'qiladi.\n"
                "3. Tanvin damma (ٌ ) - 'UN' deb o'qiladi.\n"
                "Masalan: بً (Ban), بٍ (Bin), بٌ (Bun).",
                "Harf ustidagi ikkita chiziqcha (Tanvin fatha) qanday tovushni beradi?", 
                "AN tovushini", "IN tovushini", "UN tovushini", "A"
            ),
            (
                5, 
                "5-Dars: Sukun (ْ) va Tashdid (ّ) belgilari", 
                "Arab tilida unlilarsiz harflarni va harfni ikkilantirishni ko'rsatuvchi muhim belgilar bor:\n"
                "1. Sukun (ْ ) - Harf ustiga qo'yiladi va uni unli tovushsiz, shunchaki o'zini to'xtatib o'qishni bildiradi (Masalan: اَبْ - Ab).\n"
                "2. Tashdid (ّ ) - Harf ustiga qo'yiladi va o'sha harfni ikkita qilib, urg'u bilan ikkilantirib o'qishni talab qiladi (Masalan: اَبَّ - Abba).",
                "Harfni ikkita qilib, kuchli urg'u bilan ikkilantirib o'qishni ta'minlaydigan belgi qaysi?", 
                "Sukun (ْ)", "Tashdid (ّ)", "Fatha (َ)", "B"
            ),
            (
                6, 
                "6-Dars: Boshlang'ich Arabcha So'zlashuv (Salomlashish)", 
                "Arab tilida harflar va qoidalarni o'rganganimizdan so'ng, kundalik so'zlashuv iboralariga o'tamiz:\n"
                "- Assalomu alaykum (Sizga tinchlik bo'lsin) iborasiga javoban 'Va alaykum assalom' deyiladi.\n"
                "- Suhbatdoshning hol-ahvolini so'rash uchun: 'Kayfa haluk?' (Ahvollaring qanday?) iborasi ishlatiladi.\n"
                "Javob berishda: 'Ana bixayr, shukran!' (Men yaxshiman, rahmat!) deb aytiladi.",
                "Arab tilida 'Ahvollaring qanday?' deb hol-ahvol so'rash uchun qaysi ibora ishlatiladi?", 
                "Masmuka?", "Kayfa haluk?", "Min ayna anta?", "B"
            )
        ]
        cursor.executemany("""
        INSERT INTO questions (lesson_number, lesson_title, lesson_text, question_text, variant_a, variant_b, variant_c, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, arabic_course)
    conn.commit()
    conn.close()

init_db()

# 3. Render ulanishi uchun HTTP Web Server (Port xatoligini oldini oladi)
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"MuallimBot (Arab tili mukammal ta'lim tizimi) faol holatda!")

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), WebServerHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# 4. Foydalanuvchiga joriy darsni yuborish funksiyasi
def send_current_lesson(chat_id):
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Foydalanuvchining hozirgi dars darajasini tekshirish
    cursor.execute("SELECT current_lesson FROM user_progress WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO user_progress (chat_id, current_lesson) VALUES (?, 1)", (chat_id,))
        conn.commit()
        lesson_num = 1
    else:
        lesson_num = row[0]
        
    # Ma'lumotlarni bazadan olish
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
        bot.send_message(chat_id, "🎉 *MASHALLOH!* Siz Arab alifbosi, harflarning yozilishi, tajvid qoidalari va boshlang'ich so'zlashuv bo'yicha barcha bosqichli darslarni 100% muvaffaqiyatli tugatdingiz! 🕋\n\nSiz endi Arab tilida ilk mustaqil savodxonlik darajasiga erishdingiz. Barakalloh!")

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
