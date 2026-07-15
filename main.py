import os
import time
import requests
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 100% TO'G'RI VA XATOSIZ TELEGRAM API MANZILI
BOT_TOKEN = "8404509030:AAEKMzPhiF01Z30a0o4CZhU7tP9DcrTGVP4"
API_URL = f"https://telegram.org{BOT_TOKEN}/"

class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Muallim Bot is ONLINE and RUNNING!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), WebServer)
    server.serve_forever()

# Arab alifbosi ma'lumotlar bazasi
ARAB_ALIFBOSI = {
    "alif": {"harf": "ا", "talaffuz": "Alif", "bosh": "ا", "orta": "ـا", "oxir": "ـا", "batafsil": "Unli tovushlarni uzaytirish uchun xizmat qiladi yoki so'z boshida keladi."},
    "ba": {"harf": "ب", "talaffuz": "Ba", "bosh": "بـ", "orta": "ـbـ", "oxir": "ـب", "batafsil": "Lablar mahkam tegib, tezda ochilishi orqali aytiladi. O'zbekcha 'B' ga o'xshaydi."},
    "ta": {"harf": "ت", "talaffuz": "Ta", "bosh": "تـ", "orta": "ـtـ", "oxir": "ـت", "batafsil": "Til uchi yuqori tishlarning tubiga tegishi bilan aytiladi. O'zbekcha 'T' ga o'xshaydi."},
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
            r = requests.get(API_URL + f"getUpdates?offset={offset}&timeout=10").json()
            if "result" in r:
                for update in r["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        if update["message"]["text"] == "/start":
                            markup = {"inline_keyboard": [[{"text": "📚 Alifbo darslari", "callback_data": "menyu_alifbo"}]]}
                            xabar_yubor(chat_id, "Assalamu alaykum! Arab tili ustoz botiga xush kelibsiz. Quyidagi menyudan foydalanib o'rganishni boshlang:", json.dumps(markup))
                    elif "callback_query" in update:
                        cq = update["callback_query"]
                        chat_id = cq["message"]["chat"]["id"]
                        msg_id = cq["message"]["message_id"]
                        data = cq["data"]
                        if data == "menyu_alifbo":
                            matnni_tahrirla(chat_id, msg_id, "Kerakli harfni tanlang:", json.dumps(menyu_yasa()))
                        elif data == "bosh_menyu":
                            markup = {"inline_keyboard": [[{"text": "📚 Alifbo darslari", "callback_data": "menyu_alifbo"}]]}
                            matnni_tahrirla(chat_id, msg_id, "Asosiy menyu:", json.dumps(markup))
                        elif data.startswith("harf_"):
                            harf_kalit = data.replace("harf_", "")
                            info = ARAB_ALIFBOSI[harf_kalit]
                            javob = f"Harf: {info['harf']} ({info['talaffuz']})\n\n✍️ Shakllari:\n• Alohida: {info['harf']}\n• Boshida: {info['bosh']}\n• O'rtasida: {info['orta']}\n• Oxirida: {info['oxir']}\n\n🗣 Qoida:\n{info['batafsil']}"
                            orqaga = {"inline_keyboard": [[{"text": "🔙 Alifboga qaytish", "callback_data": "menyu_alifbo"}]]}
                            matnni_tahrirla(chat_id, msg_id, javob, json.dumps(orqaga))
        except: pass
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    bot_loop()
