import os
import re
import discord
import requests

# Intents設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Steam URL正規表現
steam_url_pattern = re.compile(r"https://store\.steampowered\.com/app/(\d+)")

# チャンネルID
URL_TEXT_CHANNEL_ID = 1390656363394502715
FORUM_CHANNEL_ID = 1390371450103398583

# Bot起動時
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

# メッセージ受信時
@client.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.bot:
        return

    # 対象のテキストチャンネルだけ反応
    if message.channel.id != URL_TEXT_CHANNEL_ID:
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
        price_text = "無料または価格情報なし"

    # フォーラムチャンネルを取得
    forum_channel = message.guild.get_channel(FORUM_CHANNEL_ID)
    if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
        await message.channel.send("フォーラムチャンネルが見つからないか、フォーラムではありません。")
        return

    # スレッド作成
    try:
        await forum_channel.create_thread(
            name=name,
            content=f"価格: {price_text}\n🔗 {message.content}"
        )
        await message.channel.send(f"スレッドを作成しました: **{name}**")
    except discord.Forbidden:
        await message.channel.send("スレッド作成に必要な権限がありません。")
    except Exception as e:
        await message.channel.send(f"スレッド作成中にエラーが発生しました: {e}")

# 環境変数からトークン取得
client.run(os.environ["DISCORD_TOKEN"])
