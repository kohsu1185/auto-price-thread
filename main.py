import os
import re
import discord
import requests
from fastapi import FastAPI
from threading import Thread
import uvicorn

# Intents設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# FastAPIでヘルスチェックサーバ
app = FastAPI()

@app.get("/")
async def read_root():
    return {"status": "ok"}

# Steam URL正規表現
steam_url_pattern = re.compile(r"https://store\.steampowered\.com/app/(\d+)")

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != 1390656363394502715:
        return

    match = steam_url_pattern.search(message.content)
    if not match:
        return

    appid = match.group(1)
    api_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=JP&l=ja"
    r = requests.get(api_url)
    data = r.json()

    if not (data.get(appid) and data[appid]["success"]):
        await message.channel.send("ゲーム情報の取得に失敗しました。")
        return

    game_data = data[appid]["data"]
    name = game_data.get("name", "不明なゲーム")
    price_info = game_data.get("price_overview")

    if price_info:
        final_price = price_info["final"] // 100
        discount = price_info["discount_percent"]
        if discount > 0:
            price_text = f"{final_price}円 ({discount}%オフ)"
        else:
            price_text = f"{final_price}円"
    else:
        price_text = "無料"

    forum_channel = message.guild.get_channel(1390371450103398583)
    if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
        await message.channel.send("フォーラムチャンネルが見つからないか、フォーラムではありません。")
        return

    await forum_channel.create_thread(
        name=name,
        content=f"価格: {price_text}\n🔗 {message.content}",
        applied_tags=[]
    )

    await message.channel.send(f"スレッドを作成しました: **{name}**")

def start_discord():
    client.run(os.environ["DISCORD_TOKEN"])

if __name__ == "__main__":
    # Discord Bot を先にスレッドで動かす
    t = Thread(target=start_discord)
    t.start()

    # uvicorn は「メインプロセス」で実行
    uvicorn.run(app, host="0.0.0.0", port=8000)

