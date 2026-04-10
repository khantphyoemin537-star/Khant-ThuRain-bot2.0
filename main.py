import os
import asyncio
import re
from datetime import datetime
import pytz
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
from html import escape as escape_html
from pymongo import MongoClient

# --- CONFIGURATION ---
API_ID = 30765851
API_HASH = '235b0bc6f03767302dc75763508f7b75'
BOT_TOKEN = "8575371720:AAEWWV42CGrwooM_joiJXdo2iEw2_7atyXU"
OWNER_ID = 6015356597
TARGET_CHAT_ID = -1003806830045 

# MongoDB Setup
MONGO_URI = "mongodb+srv://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0.w6tgi8j.mongodb.net/?appName=Cluster0&tlsAllowInvalidCertificates=true"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
admin_tasks_col = db["admin_tasks"] # /done command အတွက်

# Timezone & Helpers
TZ = pytz.timezone("Asia/Yangon")
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

def bq(text): 
    return f"<blockquote><b>{text}</b></blockquote>"

# Admin စစ်ဆေးသည့် Function
async def check_admin(chat_id, user_id):
    if user_id == OWNER_ID: 
        return True
    try:
        admins = await bot_client.get_participants(chat_id, filter=ChannelParticipantsAdmins)
        return any(admin.id == user_id for admin in admins)
    except:
        return False

# --- 1. BIO & LINK FILTER LOGIC ---
@bot_client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def filter_logic(event):
    if not event.text: return
    
    sender = await event.get_sender()
    sender_id = event.sender_id
    text = event.text.strip()
    
    # Bio Filter
    if text in ["Bio", "ဘိုင်အို", "ဘိုင်-အို"]:
        if not await check_admin(event.chat_id, sender_id):
            await event.delete()
            return await event.respond(
                bq("Bruhh bruhh bioမှာဘာဖြစ်တာလဲ မသိချင်ပါဘူး စာကိုဖျက်လိုက်ပြီ။နောက်တစ်ခါ bioရင် ဒီလိုဖြစ်မယ် 🤰🫃"),
                parse_mode='html'
            )

    # Link Filter
    urls = re.findall(r'(https?://\S+|www\.\S+)', text)
    if urls:
        if await check_admin(event.chat_id, sender_id):
            full_name = f"{sender.first_name} {sender.last_name or ''}".strip()
            mention = f"<a href='tg://user?id={sender_id}'>{escape_html(full_name)}</a>"
            all_links = "\n".join(urls)
            reason = text
            for u in urls: reason = reason.replace(u, "")

            await event.delete()
            admin_msg = f"Linkပို့တဲ့သူ- {mention}\nသူပို့တဲ့Link- {all_links}\nReason - {escape_html(reason.strip() or 'No message')}"
            await event.respond(bq(admin_msg), parse_mode='html')
        else:
            await event.delete()
            await event.respond(bq("ဘာ link မှမပို့နဲ့ မရဘူး၊မင်းlinkကို ငါဖျက်လိုက်ပြီ🫵"), parse_mode='html')

# --- 2. ADM COMMAND (/adm) ---
@bot_client.on(events.NewMessage(pattern=r'^/adm(?:@\w+)?(?:\s+(.*))?'))
async def admin_mention(event):
    if event.is_private: return
    if not await check_admin(event.chat_id, event.sender_id): return

    input_text = event.pattern_match.group(1) if event.pattern_match.group(1) else "Attention Admins!"
    chat_title = escape_html(event.chat.title)
    mentions = f"<b>🛡️ {chat_title} ADMINS:</b>\n\n"
    
    try:
        admins = await bot_client.get_participants(event.chat_id, filter=ChannelParticipantsAdmins)
        for user in admins:
            if not user.bot:
                name = escape_html(user.first_name) if user.first_name else "Admin"
                mentions += f"• <a href='tg://user?id={user.id}'>{name}</a>\n"
        
        await event.respond(bq(f"{mentions}\n💬 <b>Message:</b> {escape_html(input_text)}"), parse_mode='html')
    except Exception as e:
        await event.respond(bq(f"Error: {str(e)}"), parse_mode='html')

# --- 3. DONE COMMAND (/done) ---
@bot_client.on(events.NewMessage(pattern=r'^/done(?:@\w+)?$'))
async def admin_done(event):
    if not await check_admin(event.chat_id, event.sender_id): return
    
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    admin_tasks_col.update_one({"chat_id": event.chat_id}, {"$set": {"last_done": today}}, upsert=True)
    
    u = await event.get_sender()
    name = escape_html(u.first_name) if u.first_name else "Chief"
    await event.respond(bq(f"<a href='tg://user?id={u.id}'>{name}</a> ဟုတ်ပြီ သတိပေးတာကို ဒီနေ့အတွက် ရပ်လိုက်ပြီ"), parse_mode='html')

# --- START BOT ---
if __name__ == '__main__':
    print("🚀 BoDx Sovereign Family Bot is Starting on GitHub...")
    bot_client.start(bot_token=BOT_TOKEN)
    bot_client.run_until_disconnected()
