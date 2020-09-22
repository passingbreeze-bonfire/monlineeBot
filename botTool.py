from youtube_dl import utils
import json, io, discord, asyncio, youtube_dl, time, logging
import app

# class ytLogger(object):
#     def __init__(self):
#         self.log = logging.getLogger("ytlog")
bot = app.bot
ydl_opt = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'ignoreerrors': True,
    'cookiefile': 'ytcookies.txt',
    'default_search': 'ytsearch',
    'sleep_interval': 10,
    'max_sleep_interval': 60,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }],
}

# def aftercoro(error):
#     try:
#         coro = asyncio.run_coroutine_threadsafe(playYTlist, bot.loop)
#         coro.result()
#     except Exception as e:
#         print("Error is", e)

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

async def getSonglist(ctx, songlist:dict, url):
    await ctx.send("재생 목록 받아오는 중...")
    try :
        with youtube_dl.YoutubeDL(ydl_opt) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                result = info['entries']
                for i, item in enumerate(result):
                    songlist[info['entries'][i]['title']] = info['entries'][i]['webpage_url']
            else:
                songlist[info['title']] = info['webpage_url']
    except Exception as e:
        await ctx.send("음원을 받는 과정에서 다음의 오류가 발생하였습니다.\n ➡️ ", e)

async def playYTlist(ctx, uservoice, vc, songlist:dict):
    await ctx.send("🎧 음악 재생 시작 🎧")

    # def hookdl(d):
    #     if d['status'] == 'finished':
    #         bot.loop.create_task()
    #     pass

    # ydl_opt['progress_hooks'] = [hookdl]

    try:
        titles = list(songlist.keys())
        with youtube_dl.YoutubeDL(ydl_opt) as ydl:
            firstTitle = titles[0]
            info = ydl.extract_info(songlist[firstTitle], download=False)
            if vc and vc.is_connected():
                await vc.move_to(uservoice)
            else:
                vc = await uservoice.connect()
            vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn"))
            vc.volume = 80
            if vc.is_playing():
                await asyncio.sleep(info['duration']+20)
            songlist.pop(firstTitle)

        if len(songlist) == 0:
            await vc.disconnect()
            await asyncio.sleep(20)
            await ctx.send("추가된 재생목록이 없으므로 음성채널에서 나갑니다.")

    except Exception as e:
        await vc.disconnect()
        await asyncio.sleep(20)
        await ctx.send("음원을 받는 과정에서 다음의 오류가 발생하였습니다.\n ➡️ ", e)
