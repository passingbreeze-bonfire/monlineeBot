from discord.ext import commands
from collections import deque
import io, discord, asyncio, random, time
import youtube_dl

import rx
import rx.operators as ops
from rx.scheduler.eventloop import AsyncIOScheduler

class ytMusic(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__bot_voice = None
        self.__songs = {}
        self.__now, self.__prev = deque(), deque()
        self.__chk_err = 0
        self.__now_title = ""
        self.__opt = {
            'format': 'bestaudio/best',
            'nocheckcertificate': True,
            'extractaudio': True,
            'ignoreerrors': True,
            'forceduration': False,
            'logger': ytLogger(self),
            'default_search': 'auto',
            'sleep_interval': 10,
            'max_sleep_interval': 60,
            'postprocessors': [{
                'key': 'FFmpegExtractAudioPP',
                'preferredcodec': 'opus',
                'preferredquality': '192'
            }],
        }
        self.__ytinfo = None
        self.__bot_token = "NzU0OTAyNzcwNTA2NzkzMDIx.X17f_Q.NWy2xds0lHO5NnFGQOJn_lN1H8s"

    def __bot_msg_wrapper(self, ctx, msg):
        async def bot_msg(ctx, msg):
            await ctx.send(msg)

    async def stop_song(self):
        self.__songs.clear()
        self.__now.clear()
        self.__prev.clear()
        await self.__bot_voice.disconnect()

    def get_song_list(self):
        return self.__now

    def __ytDownload(self, url):
        with youtube_dl.YoutubeDL(self.__opt) as ydl:
            self.__ytinfo = ydl.extract_info(url, download=False)
            if self.__chk_err < 0:
                return "음원을 가져올 수 있는 링크가 없습니다. ️🙅"

    async def __set_song_list(self, ctx, url):
        self.__ytDownload(url)
        if self.__ytinfo is not None:
            if isinstance(self.__ytinfo, str):
                await ctx.send(self.__ytinfo)
                return -1
            elif isinstance(self.__ytinfo, dict):
                if 'entries' in self.__ytinfo:
                    await ctx.send("🎶 플레이리스트 준비 중... 🎶")
                    result = self.__ytinfo['entries']
                    for i, item in enumerate(result):
                        self.__now.append(self.__ytinfo['entries'][i]['title'])
                        self.__songs[self.__ytinfo['entries'][i]['title']] = self.__ytinfo['entries'][i]['url']
                else:
                    await ctx.send("🎶 준비 중... 🎶")
                    self.__now.append(self.__ytinfo['title'])
                    self.__songs[self.__ytinfo['title']] = self.__ytinfo['webpage_url']
                return 0
            else:
                await ctx.send("재생할 수 있는게 없습니다.️ 🙅")
                return -1
        else:
            await ctx.send("유튜브에서 아무것도 받아올 수 없었습니다. ️🙅")
            return -1

    def __play_song(self, ctx):
        def _play_song(title_list):
            def subscribe(observer, scheduler=None):
                def on_next(title):
                    self.__now_title = title
                    self.__prev.append(title)
                    self.__ytDownload(self.__songs[title])
                    if self.__bot_voice and self.__bot_voice.is_connected():
                        self.__bot_voice.play(discord.FFmpegOpusAudio(self.__ytinfo['formats'][0]['url'], options="-vn"),
                                              after=None)
                        time.sleep(self.__ytinfo['duration'] + 10)
                    else:
                        observer.on_error("봇이 음성채널에 없습니다. 🙅")

                return title_list.subscribe(
                    on_next,
                    observer.on_error,
                    observer.on_completed,
                    scheduler)
            return rx.create(subscribe)
        return _play_song

    @commands.command()
    async def play(self, ctx, *args):
        sched = AsyncIOScheduler(loop = self.__bot.loop)
        args_list = list(args)
        args_len = len(args_list)
        await ctx.send("Loading...")
        if args_len == 1:
            if ctx.author.voice and ctx.author.voice.channel:
                user_voice = ctx.author.voice.channel
                self.__bot_voice = await user_voice.connect()
            else:
                await ctx.send("음성 채널에 없습니다. 🙅")
                return
            await self.__set_song_list(ctx, args_list[0])
            await ctx.send("🎧 음악 재생 시작 🎧")
            rx.from_iterable(self.__now, sched).pipe(
                self.__play_song(ctx)
            ).subscribe(on_error = lambda e : print(e))
        else:
            await ctx.send("\"!play | !틀어줘 [유튜브 링크]\"를 입력해주세요")
            return

    @commands.command(name="틀어줘")
    async def playkor(self,ctx):
        await self.play.invoke(ctx)

    @commands.command()
    async def nowplay(self,ctx):
        plist = ""
        with io.StringIO() as strbuf:
            strbuf.write("> **🎙 Now Playing.. 🎙**\n")
            strbuf.write(f"> *{self.__now_title}*\n\n")
            if self.__now :
                strbuf.write("> **💿 Playlist 💿**\n")
                for idx in range(1, len(self.__now)):
                    strbuf.write("> {}. {}\n".format(idx, self.__now[idx]))
            plist = strbuf.getvalue()
        await ctx.send(plist)

    @commands.command()
    async def stop(self, ctx):
        if self.__bot_voice and self.__bot_voice.is_connected():
            await ctx.send("재생을 멈춥니다.")
            await self.stop_song()
        else:
            await ctx.send("음성채널에 없습니다. 🙅")

    @commands.command(name="그만")
    async def stopkor(self, ctx):
        await self.stop.invoke(ctx)


class ytLogger:
    def __init__(self, ytm: ytMusic):
        self.ytm = ytm

    def debug(self, msg):
        self.ytm.__chk_err = 1

    def warning(self, msg):
        self.ytm.__chk_err = 2

    def error(self, msg):
        self.ytm.__chk_err = -1
