from discord.ext import commands
from discord.utils import get
from passlib.hash import pbkdf2_sha512
import discord, io, asyncio, time, random, json, youtube_dl

ydl_opt = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'ignoreerrors': True,
    'cookiefile': 'ytcookie.txt',
    'default_search': 'ytsearch',
    'sleep_interval': 10,
    'max_sleep_interval': 60,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }],
}

def getToken(tokenFname):
    token = None
    with io.StringIO() as strbuf:
        if not isinstance(tokenFname, str):
            strbuf.write("올바른 문자열이 아닙니다")
        else :
            try:
                with open(tokenFname, "r") as twrap:
                    tokenWrap = json.load(twrap)
                    token = tokenWrap["token"]
            except FileNotFoundError :
                strbuf.write("토큰을 불러오지 못했습니다.")
    return token

def ytDownload(url):
    try :
        with youtube_dl.YoutubeDL(ydl_opt) as ydl:
            info = ydl.extract_info(url, download=False)
        return info
    except Exception as e:
        print("음원을 받는 과정에서 다음의 오류가 발생하였습니다.\n ➡️ ", e)

async def getSonglist(ctx, songlist:dict, url):
    await ctx.send("재생 목록 받아오는 중...")
    info = ytDownload(url)
    if 'entries' in info:
        result = info['entries']
        for i, item in enumerate(result):
            songlist[info['entries'][i]['title']] = info['entries'][i]['webpage_url']
    else:
        songlist[info['title']] = info['webpage_url']

async def playYTlist(bot, ctx, uservoice, vc, songlist:dict, titles:list, index):
    await ctx.send("🎧 음악 재생 시작 🎧")
    info = ytDownload(songlist[titles[index]])
    if vc and vc.is_connected():
        await vc.move_to(uservoice)
    else:
        vc = await uservoice.connect()

    def playingContinue(error):
        nonlocal index, vc
        index += 1
        nextTitle = ""
        try:
            if index == len(songlist)-1 :
                subcoro = asyncio.gather(bot.loop.run_in_executor(None, songlist.clear),
                                         bot.loop.run_in_executor(None, titles.clear),
                                         asyncio.sleep(90),
                                         ctx.send("더이상 재생할 음악이 없으므로 음성채널에서 나갑니다."),
                                         vc.disconnect())
                finish = asyncio.run_coroutine_threadsafe(subcoro, bot.loop)
                finish.result()
            else:
                nextTitle = titles[index]
            info = ytDownload(songlist[nextTitle])
            vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url'],
                                           before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                           options="-vn"), after=playingContinue)
        except Exception as e:
            print("Error occurred after play callback called : ", e)

    vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url'],
                                   before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                   options="-vn"),
                                   after=playingContinue)

