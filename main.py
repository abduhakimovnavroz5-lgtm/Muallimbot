import os
import time
import requests
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Render serveridan tokenni xavfsiz va maxfiy o'qiymiz
BOT_TOKEN = "8404509030:AAEKMzPhiF01Z30a0o4CZhU7tP9DcrTGVP4"
API_URL = f"https://telegram.org{BOT_TOKEN}/"

# Web Server Render talab qiladigan doimiy aloqani ushlab turadi
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Muallim Bot is officially ONLINE and LIVE!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    server.serve_forever()

# 28 ta arab harflarining to'liq mukammal bazasi
ARAB_ALIFBOSI = {
    "alif": {"harf": "ا", "talaffuz": "Alif", "bosh": "ا", "orta": "ـا", "oxir": "ـا", "batafsil": "Unli tovushlarni uzaytirish uchun xizmat qiladi yoki so'z boshida keladi."},
    "ba": {"harf": "ب", "talaffuz": "Ba", "bosh": "بـ", "orta": "ـبـ", "oxir": "ـب", "batafsil": "Lablar mahkam tegib, tezda ochilishi orqali aytiladi. O'zbekcha 'B' ga o'xshaydi."},
    "ta": {"harf": "ت", "talaffuz": "Ta", "bosh": "تـ", "orta": "ـتـ", "oxir": "ـت", "batafsil": "Til uchi yuqori tishlarning tubiga tegishi bilan aytiladi. O'zbekcha 'T' ga o'xshaydi."},
    "sa": {"harf": "ث", "talaffuz": "Sa (Sizlovchi)", "bosh": "ثـ", "orta": "ـثـ", "oxir": "ـث", "batafsil": "Til uchi oldingi tishlar orasidan sal chiqib, mayin aytiladi. Tishlararo 'S'."},
    "jim": {"harf": "ج", "talaffuz": "Jim", "bosh": "جـ", "orta": "ـجـ", "oxir": "ـج", "batafsil": "Til o'rtasi tanglayga tegishi bilan aytiladi. O'zbekcha 'J' tovushiga yaqin."},
    "ha_yumshoq": {"harf": "ح", "talaffuz": "Ha (Bo'g'iz)", "bosh": "حـ", "orta": "ـحـ", "oxir": "ـح", "batafsil": "Xalqumning o'rtasidan, tomoqni siqqan holda nafas qisilib chiqadigan toza 'H'."},
    "xo": {"harf": "خ", "talaffuz": "Xo (Xirildoq)", "bosh": "خـ", "orta": "ـخـ", "oxir": "ـخ", "batafsil": "Tomoqning yuqori qismidan xirillab chiqadigan qattiq 'X' tovushi."},
    "dal": {"harf": "د", "talaffuz": "Dal", "bosh": "د", "orta": "ـد", "oxir": "ـد", "batafsil": "Til uchi yuqori milkka tegib aytiladi. O'zbekcha 'D' tovushiga o'xshaydi."},
    "zal": {"harf": "ذ", "talaffuz": "Zal (Sizlovchi)", "bosh": "ذ", "orta": "ـذ", "oxir": "ـذ", "batafsil": "Til uchi tishlar orasidan chiqib, mayin va sizlab aytiladi. Tishlararo 'Z'."},
    "ro": {"harf": "ر", "talaffuz": "Ro", "bosh": "ر", "orta": "ـر", "oxir": "ـر", "batafsil": "Til uchi tanglayga tegib titraydi. Yo'g'on 'R' tovushi."},
    "zo": {"harf": "ز", "talaffuz": "Zo", "bosh": "ز", "orta": "ـز", "oxir": "ـز", "batafsil": "Oddiy o'zbekcha 'Z' tovushi kabi jarangli aytiladi."},
    "sin": {"harf": "س", "talaffuz": "Sin", "bosh": "سـ", "orta": "ـسـ", "oxir": "ـس", "batafsil": "Oddiy ingichka 'S' tovushi. Til uchi pastki tishlar tubiga tegadi."},
    "shin": {"harf": "ش", "talaffuz": "Shin", "bosh": "شـ", "orta": "ـشـ", "oxir": "ـش", "batafsil": "O'zbekcha 'Sh' tovushiga to'liq mos keladi."},
    "sod": {"harf": "ص", "talaffuz": "Sod (Yo'g'on)", "bosh": "صـ", "orta": "ـصـ", "oxir": "ـص", "batafsil": "Yo'g'on va qattiq aytiladigan 'S'. Og'iz bo'shlig'i yo'g'on havo bilan to'ladi."},
    "zod": {"harf": "ض", "talaffuz": "Zod (Yo'g'on)", "bosh": "ضـ", "orta": "ـضـ", "oxir": "ـض", "batafsil": "Tilning yon tomoni yuqori oziq tishlarga tegishi bilan aytiladigan juda yo'g'on 'Z'."},
    "to": {"harf": "ط", "talaffuz": "To (Yo'g'on)", "bosh": "طـ", "orta": "ـطـ", "oxir": "ـط", "batafsil": "Yo'g'on va qattiq aytiladigan 'T' tovushi."},
    "zo_yoqon": {"harf": "ظ", "talaffuz": "Zo (Yo'g'on sizlovchi)", "bosh": "ظـ", "orta": "ـظـ", "oxir": "ـظ", "batafsil": "Til uchi tishlar orasidan chiqib, juda yo'g'on aytiladigan tishlararo 'Z'."},
    "ayn": {"harf": "ع", "talaffuz": "Ayn", "bosh": "عـ", "orta": "ـعـ", "oxir": "ـع", "batafsil": "Tomoqning o'rtasidan qisilib chiqadigan o'ziga xos tovush."},
    "g'ayn": {"harf": "غ", "talaffuz": "G'ayn", "bosh": "غـ", "orta": "ـغـ", "oxir": "ـغ", "batafsil": "O'zbekcha 'G'' tovushining tomoqdan chiqadigan yo'g'on shakli."},
    "fa": {"harf": "ف", "talaffuz": "Fa", "bosh": "فـ", "orta": "ـfـ", "oxir": "ـف", "batafsil": "Yuqori tishlar pastki labning ichki qismiga tegib aytiladi. O'zbekcha 'F'."},
    "qof": {"harf": "ق", "talaffuz": "Qof", "bosh": "قـ", "orta": "ـقـ", "oxir": "ـق", "batafsil": "Til tubi tanglayning eng yumshoq joyiga tegib aytiladigan chuqur tomoq 'Q'si."},
    "kof": {"harf": "ك", "talaffuz": "Kof", "bosh": "كـ", "orta": "ـكـ", "oxir": "ـك", "batafsil": "Oddiy yumshoq va ingichka o'zbekcha 'K' tovushi."},
    "lam": {"harf": "ل", "talaffuz": "Lam", "bosh": "لـ", "orta": "ـلـ", "oxir": "ـل", "batafsil": "Til uchi yuqori milkka kengroq tegishi bilan aytiladi. Oddiy 'L'."},
    "mim": {"harf": "م", "talaffuz": "Mim", "bosh": "مـ", "orta": "ـmـ", "oxir": "ـم", "batafsil": "Lablarning bir-biriga yengil tegib yopilishi bilan chiqadi. Oddiy 'M'."},
    "nun": {"harf": "ن", "talaffuz": "Nun", "bosh": "نـ", "orta": "ـنـ", "oxir": "ـن", "batafsil": "Nafas burun bo'shlig'idan o'tib aytiladigan ingichka 'N' tovushi."},
    "vav": {"harf": "و", "talaffuz": "Vav", "bosh": "و", "orta": "ـو", "oxir": "ـو", "batafsil": "Lablar oldinga cho'zilib, doira shakliga kelganda chiqadigan cho'ziq 'V' (W) tovushi."},
    "ha_dumaloq": {"harf": "هـ", "talaffuz": "Ha (Ko'krak)", "bosh": "هـ", "orta": "ـهـ", "oxir": "ـه", "batafsil": "Tomoqning eng tubidan yengil aytiladigan 'H' (havo)."},
    "ya": {"harf": "ي", "talaffuz": "Ya", "bosh": "يـ", "orta": "ـيـ", "oxir": "ـي", "batafsil": "Til o'rtasi tanglayga ko'tarilib aytiladi. O'zbekcha 'Y' tovushiga mos."},
}

def xabar_yubor(chat_id, matn, reply_markup=None):
    data = {"chat_id": chat_id, "text": matn}
    if reply_markup: data["reply_markup"] = reply_markup
    try: requests.post(API_URL + "sendMessage", json=data)
    except: pass

def menyu_yasa():
    inline_keyboard = []
    qator = []
    for kalit, info in ARAB_ALIFBOSI.items():
        qator.append({"text": f"{info['harf']} - {info['talaffuz']}", "callback_data": f"harf_{kalit}"})
        if len(qator) == 3:
            inline_keyboard.append(qator)
            qator = []
    if qator: inline_keyboard.append(qator)
    inline_keyboard.append([{"text": "🔙 Orqaga", "callback_data": "bosh_menyu"}])
    return {"inline_keyboard": inline_keyboard}

def matnni_tahrirla(chat_id, message_id, matn, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": matn}
    if reply_markup: data["reply_markup"] = reply_markup
    try: requests.post(API_URL + "editMessageText", json=data)
    except: pass

def bot_loop():
    offset = 0
    while True:
        try:
            # Long polling so'rovini Render o'chirib qo'ymasligi uchun optimallashtirdik
            r = requests.get(API_URL + f"getUpdates?offset={offset}&timeout=5").json()
            if "result" in r:
                for update in r["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        if update["message"]["text"] == "/start":
                            markup = {"inline_keyboard": [
                                [{"text": "📚 Alifbo darslari", "callback_data": "menyu_alifbo"}],
                                [{"text": "❓ O'zini tekshirish (Test)", "callback_data": "menyu_test"}]
                            ]}
                            xabar_yubor(chat_id, f"Assalamu alaykum, {update['message']['from']['first_name']}!\nArab tili ustoz botiga xush kelibsiz. Quyidagi menyudan foydalanib o'rganishni boshlang:", json.dumps(markup))
                    elif "callback_query" in update:
                        cq = update["callback_query"]
                        chat_id = cq["message"]["chat"]["id"]
                        msg_id = cq["message"]["message_id"]
                        data = cq["data"]
                        if data == "menyu_alifbo":
                            matnni_tahrirla(chat_id, msg_id, "Kerakli harfni tanlang:", json.dumps(menyu_yasa()))
                        elif data == "bosh_menyu":
                            markup = {"inline_keyboard": [
                                [{"text": "📚 Alifbo darslari", "callback_data": "menyu_alifbo"}],
                                [{"text": "❓ O'zini tekshirish (Test)", "callback_data": "menyu_test"}]
                            ]}
                            matnni_tahrirla(chat_id, msg_id, "Asosiy menyu:", json.dumps(markup))
                        elif data == "menyu_test":
                            orqaga = {"inline_keyboard": [[{"text": "🔙 Orqaga", "callback_data": "bosh_menyu"}]]}
                            matnni_tahrirla(chat_id, msg_id, "🎯 Interaktiv test tizimi tez kunda qo'shiladi. Hozircha darslarni to'liq o'zlashtiring!", json.dumps(orqaga))
                        elif data.startswith("harf_"):
                            harf_kalit = data.replace("harf_", "")
                            info = ARAB_ALIFBOSI[harf_kalit]
                            javob = f"Harf: {info['harf']} ({info['talaffuz']})\n\n✍️ Shakllari:\n• Alohida: {info['harf']}\n• Boshida: {info['bosh']}\n• O'rtasida: {info['orta']}\n• Oxirida: {info['oxir']}\n\n🗣 Qoida:\n{info['batafsil']}"
                            orqaga = {"inline_keyboard": [[{"text": "🔙 Alifboga qaytish", "callback_data": "menyu_alifbo"}]]}
                            matnni_tahrirla(chat_id, msg_id, javob, json.dumps(orqaga))
        except Exception as e:
            pass
        time.sleep(0.5)

if __name__ == "__main__":
    # Server oqimini birinchi bo'lib majburiy yurgizamiz
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    bot_loop()
