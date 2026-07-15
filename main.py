# -*- coding: utf-8 -*-
import os
import sys
import threading
import sqlite3
import requests
import time
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Telegram bot tokeni
TOKEN = "8404509030:AAHknnOHP2p5KYHHUJKqk3NxuKcnq1dl6vY"
bot = telebot.TeleBot(TOKEN)

# 2. Ma'lumotlar bazasini va 3 ta alohida yo'nalishli darslarni yaratish
def init_db():
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Darslar va testlar jadvali
    cursor.execute("DROP TABLE IF EXISTS questions")
    cursor.execute("""
    CREATE TABLE questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level_name TEXT NOT NULL,       -- 'alifbo', 'tajvid' yoki 'sozlashuv'
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
    
    # Foydalanuvchi darajalarini saqlash (Har bir menyu uchun alohida daraja ustuni)
    cursor.execute("DROP TABLE IF EXISTS user_progress")
    cursor.execute("""
    CREATE TABLE user_progress (
        chat_id INTEGER PRIMARY KEY,
        alifbo_level INTEGER DEFAULT 1,
        tajvid_level INTEGER DEFAULT 1,
        sozlashuv_level INTEGER DEFAULT 1
    )
    """)
    
    # Barcha darslar va oltin qoidalarni o'z ichiga olgan mukammal baza
    arabic_course = [
        # === 1-MENYU: ARAB ALIFBOSI (0 DAN BOSHLASH) ===
        (
            "alifbo", 1, 
            "Alifbo: 1-Dars - Alif (A) harfi va O'ngdan Chapga qoidasi", 
            "Arab tili mutlaqo teskari — o'ngdan chapga qarab o'qiladi va yoziladi! Kitob va daftarlar ham orqa tomondan ochiladi.\n\nBirinchi harf - Alif (ا) harfidir. U o'zi mustaqil tovushga ega emas, unga unli tovushni berish uchun Harakatlar (belgilar) ishlatiladi:\n1. Fatha (ustidagi chiziq) - A tovushini beradi. (اَ)\n2. Kasra (ostidagi chiziq) - I tovushini beradi. (اِ)\n3. Damma (ustidagi kichik belgi) - U tovushini beradi. (اُ)",
            "Arab tili qaysi tomondan boshlab o'qiladi va yoziladi?", 
            "Chapdan o'ngga qarab", "O'ngdan chapga qarab", "Tepadan pastga qarab", "B"
        ),
        (
            "alifbo", 2, 
            "Alifbo: 2-Dars - Ba (B) harfi va Harflarning ulanishi", 
            "Arab harflari so'z ichidagi o'rniga qarab (boshida, o'rtasida, oxirida) shaklini o'zgartiradi.\n\nIkkinchi harf - Ba (ب) harfi bo'lib, pastida bitta nuqtasi bo'ladi. U o'zidan keyingi harfga ulanadi:\n- So'z boshida yozilishi: بـ (chapga bog'lanadi)\n- So'z o'rtasida yozilishi: ـبـ (ikki tomonga bog'lanadi)\n- So'z oxirida yozilishi: ـب (o'ngga bog'lanadi)\n\nDiqqat! Alifbodagi 6 ta harf (ا, د, ذ, ر, z, و) o'zidan keyingi harfga mutlaqo ulanmaydi!",
            "Alifbodagi nechta harf o'zidan keyingi harfga mutlaqo ulanmaydi?", 
            "28 ta harf", "22 ta harf", "6 ta harf", "C"
        ),
        (
            "alifbo", 3, 
            "Alifbo: 3-Dars - Ta (T) va Sa (S) harflari (Maxraj)", 
            "3. Ta (ت) harfi - ustida ikkita nuqtasi bor. Oddiy o'zbekcha T tovushini beradi.\n4. Sa (ث) harfi - ustida uchta nuqtasi bor.\n\n⚠️ Maxraj qoidasi: Sa harfi talaffuzi tishlar orasidan chiqadigan yumshoq, chuchuk S tovushidir. Til uchi oldingi tishlar orasiga bir oz tegib turadi. Agar buni oddiy S desangiz, so'z ma'nosi butunlay buziladi!",
            "Qaysi harf maxraji tishlar orasidan chiqadigan chuchuk S tovushini ifodalaydi?", 
            "Ta (ت) harfi", "Ba (ب) harfi", "Sa (ث) harfi", "C"
        ),

        # === 2-MENYU: TAJVID QOIDALARI (TO'G'RI O'QISH) ===
        (
            "tajvid", 1, 
            "Tajvid: 1-Dars - Unli belgilari va Tanvin qoidasi", 
            "Arab tilida unli harflar yo'q, ularning o'rniga Harakatlar ishlatiladi. Agar bu harakatlar ikki barobar ko'paytirilsa (ikki fatha, ikki kasra, ikki damma), bu qoida Tanvin deyiladi va so'z oxirida N tovushini qo'shib o'qishni talab qiladi:\n\n1. Tanvin fatha ( ً ) - AN deb o'qiladi.\n2. Tanvin kasra ( ٍ ) - IN deb o'qiladi.\n3. Tanvin damma ( ٌ ) - UN deb o'qiladi.\n\nMasalan: Ban, Bin, Bun.",
            "Harf ustidagi ikkita chiziqcha (Tanvin fatha) qanday tovushni beradi?", 
            "AN tovushini", "IN tovushini", "UN tovushini", "A"
        ),
        (
            "tajvid", 2, 
            "Tajvid: 2-Dars - Sukun va Tashdid belgilari", 
            "Arab matnlarida so'zlarni to'g'ri o'qish uchun quyidagi ikki belgi juda muhim:\n\n1. Sukun ( ْ ) - Harf ustiga qo'yiladi va uni unli tovushsiz, shunchaki o'zini to'xtatib o'qishni bildiradi (Masalan: Ab).\n2. Tashdid ( ّ ) - Harf ustiga qo'yiladi va o'sha harfni ikkita qilib, urg'u bilan ikkilantirib o'qishni talab qiladi (Masalan: Abba).",
            "Harfni ikkita qilib, kuchli urg'u bilan ikkilantirib o'qishni ta'minlaydigan belgi qaysi?", 
            "Sukun belgisi", "Tashdid belgisi", "Fatha belgisi", "B"
        ),

        # === 3-MENYU: ARABCHA SO'ZLASHUV (GAPLASHISH) ===
        (
            "sozlashuv", 1, 
            "So'zlashuv: 1-Dars - O'zak harflar va Tanishish (Ism so'rash)", 
            "O'tish qoidasi: Arab tilidagi deyarli barcha so'zlar 3 ta asosiy undosh o'zak harfdan tarqaladi!\n\nKundalik so'zlashuvda ism so'rash jinsga qarab ajraladi:\n- Masmuka? (Sening isming nima? - o'g'il bolaga)\n- Masmuki? (Sening isming nima? - qiz bolaga)\n\nJavob berishda esa: Ismiy Navruzbek (Mening ismim Navruzbek) deb aytiladi.",
            "Arab tilida o'g'il boladan 'Sening isming nima?' deb so'rash uchun qaysi ibora ishlatiladi?", 
            "Masmuka?", "Masmuki?", "Kayfa haluk?", "A"
        ),
        (
            "sozlashuv", 2, 
            "So'zlashuv: 2-Dars - Jins qoidasi va Hol-ahvol so'rash", 
            "Arab tilida har bir narsa va buyum jinsga (erkak va ayol) bo'linadi. Ayol jinsidagi so'zlar oxirida dumaloq T (ة - Tamarbuta) harfi bo'ladi.\n\nSuhbatdoshning hol-ahvolini so'rash uchun:\n- 'Kayfa haluk?' (Ahvollaring qanday?) iborasi ishlatiladi.\nJavob berishda esa: 'Ana bixayr, shukran!' (Men yaxshiman, rahmat!) deb aytiladi.",
            "Arab tilida 'Men yaxshiman, rahmat!' deb javob berish uchun qaysi variant to'g'ri?", 
            "Ahlan va sahlan", "Ana bixayr, shukran!", "Masmuka?", "B"
        )
    ]
    cursor.executemany("""
    INSERT INTO questions (level_name, lesson_number, lesson_title, lesson_text, question_text, variant_a, variant_b, variant_c, correct_answer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        self.wfile.write(b"MuallimBot (3-Menyuli Tizim) faol holatda!")

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

# 🗂 BOSH MENU KLAVIATURASI
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(text="📖 Arab Alifbosi (0 dan)", callback_data="menu_alifbo")
    btn2 = types.InlineKeyboardButton(text="✍️ Tajvid Qoidalari", callback_data="menu_tajvid")
    btn3 = types.InlineKeyboardButton(text="🗣 Arabcha So'zlashuv", callback_data="menu_sozlashuv")
    markup.add(btn1, btn2, btn3)
    return markup

# 4. Joriy darsni INLINE TUGMALAR bilan yuborish
def send_lesson_by_category(chat_id, category):
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
    
    # Foydalanuvchining darajasini olish
    cursor.execute(f"SELECT {category}_level FROM user_progress WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(f"INSERT INTO user_progress (chat_id, {category}_level) VALUES (?, 1)", (chat_id,))
        conn.commit()
        lesson_num = 1
    else:
        lesson_num = row[0]
        
    cursor.execute("SELECT lesson_title, lesson_text, question_text, variant_a, variant_b, variant_c FROM questions WHERE level_name = ? AND lesson_number = ?", (category, lesson_num))
    lesson = cursor.fetchone()
    conn.close()
    
    if lesson:
        matn = f"📖 *{lesson[0]}*\n\n{lesson[1]}\n\n"
        matn += f"❓ *Savol:* {lesson[2]}"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_a = types.InlineKeyboardButton(text=f"A) {lesson[3]}", callback_data=f"ans_{category}_{lesson_num}_A")
        btn_b = types.InlineKeyboardButton(text=f"B) {lesson[4]}", callback_data=f"ans_{category}_{lesson_num}_B")
        btn_c = types.InlineKeyboardButton(text=f"C) {lesson[5]}", callback_data=f"ans_{category}_{lesson_num}_C")
        markup.add(btn_a, btn_b, btn_c)
        
        bot.send_message(chat_id, matn, parse_mode="Markdown", reply_markup=markup)
    else:
        cat_names = {"alifbo": "Arab alifbosi", "tajvid": "Tajvid qoidalari", "sozlashuv": "Arabcha so'zlashuv"}
        msg = f"🎉 *MASHALLOH!* Siz *{cat_names[category]}* yo'nalishidagi barcha darslarni va testlarni tugatdingiz! \n\nBoshqa yo'nalishlarni o'rganish uchun /menu buyrug'ini yuboring."
        bot.send_message(chat_id, msg, parse_mode="Markdown")

# 5. Bot buyruqlari
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    chat_id = message.chat.id
    conn = sqlite3.connect('radar_base.db')
    cursor = conn.cursor()
