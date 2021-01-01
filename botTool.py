from discord.ext import commands
from discord.utils import get
from passlib.hash import pbkdf2_sha512
from functools import partial
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
    errmsg = None

    class ytLogger(object):
        def debug(self,msg):
            pass
        def warning(self,msg):
            pass
        def error(self, msg):
            print(msg)
            nonlocal errmsg
            errmsg = "음원을 가져올 수 없는 링크가 있습니다. ️🙅"

    ydl_opt['logger'] = ytLogger()
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        info = ydl.extract_info(url, download=False)
        if errmsg is not None:
            return errmsg
    return info

async def getSonglist(ctx, songlist:dict, url):
    await ctx.send("재생 목록 받아오는 중...")
    info = ytDownload(url)
    if info is not None:
        if isinstance(info, str):
            await ctx.send(info)
            return
        elif isinstance(info, dict):
            if 'entries' in info:
                result = info['entries']
                for i, item in enumerate(result):
                    songlist[info['entries'][i]['title']] = info['entries'][i]['webpage_url']
            else:
                songlist[info['title']] = info['webpage_url']
        else:
            await ctx.send("재생할 수 있는게 없습니다.️ 🙅")
    else:
        await ctx.send("유튜브에서 아무것도 받아올 수 없었습니다. ️🙅")


async def playYTlist(bot, ctx, uservoice, vc, playlist:dict, prevone:dict, titles:list):
    title = titles[0]
    prevone[title] = playlist[title]
    info = ytDownload(playlist[title])
    if info is not None:
        if isinstance(info, str):
            await ctx.send(info)
            return
        elif isinstance(info, dict):
            await ctx.send("🎧 음악 재생 시작 🎧")
            if vc and vc.is_connected():
                await vc.move_to(uservoice)
            else:
                vc = await uservoice.connect()

            def continuePlay(error):
                nonlocal title
                if len(playlist) > 0:
                    try:
                        titles.remove(title)
                        playlist.pop(title)
                        title = titles[0]
                        info = ytDownload(playlist[title])
                        if vc.is_connected():
                            vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url'],
                                               before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                               options="-vn"),
                                               after=continuePlay)
                        else:
                            notconnectmsg = ctx.send("음성채널에 연결되어있지 않아 재생을 중단합니다.")
                            try:
                                notconnected = asyncio.run_coroutine_threadsafe(notconnectmsg, bot.loop)
                                notconnected.result()
                            except Exception as e:
                                print("Error from not connected voice channel : ", e)
                    except Exception as e:
                        errormsg = ctx.send("재생도중 오류가 발생하여 재생을 중단합니다.")
                        if vc.is_connected():
                            err = asyncio.run_coroutine_threadsafe(errormsg, bot.loop)
                            try:
                                err.result()
                                asyncio.run_coroutine_threadsafe(vc.disconnect, bot.loop)
                            except Exception as e:
                                print("Error from playlist error : ", e)
                else:
                    if vc.is_connected():
                        fincoro = asyncio.gather(asyncio.sleep(60),
                                                 ctx.send("더이상 재생할 음악이 없으므로 음성채널에서 나갑니다."),
                                                 vc.disconnect)
                        finish = asyncio.run_coroutine_threadsafe(fincoro, bot.loop)
                        try:
                            finish.result()
                        except Exception as e:
                            print("Error from finishing playing :", e)

            vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url'],
                                           before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                           options="-vn"),
                                           after=continuePlay)

        else:
            await ctx.send("유튜브 음원이 아닙니다.")
    else:
        await ctx.send("유튜브에서 아무것도 받아올 수 없었습니다. ️🙅")
