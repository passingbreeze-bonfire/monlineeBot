from collections import deque
import io, asyncio, random, time, re

import discord, youtube_dl
from discord.ext import commands
from tqdm import tqdm

class ytMusic(commands.Cog):
    def __init__(self, bot):
        self.dur = 0
        self.chk_err = 0
        self.__bot = bot
        self.__bot_voice = None
        self.__songs = {}
        self.__now, self.__prev = deque(), deque()
        self.__now_title = ""
        self.__opt = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'ignoreerrors': True,
            'forceduration': False,
            'logger': ytLogger(self),
            'default_search': 'auto',
            'sleep_interval': 10,
            'max_sleep_interval': 60,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192'
            }],
        }
        self.__ytinfo = None

    def get_song_list(self):
        return self.__now

    async def stop_song(self):
        self.__songs.clear()
        self.__now.clear()
        self.__prev.clear()
        await self.__bot_voice.disconnect()

    async def __ytDownload(self, url):
        with youtube_dl.YoutubeDL(self.__opt) as ydl:
            self.__ytinfo = ydl.extract_info(url, download=False)
            if self.chk_err < 0:
                return "음원을 가져올 수 있는 링크가 없습니다. ️🙅"

    async def __set_song_list(self, ctx, url):
        await self.__ytDownload(url)
        if self.__ytinfo is not None:
            if isinstance(self.__ytinfo, str):
                print(self.__ytinfo)
                return -1
            elif isinstance(self.__ytinfo, dict):
                if 'entries' in self.__ytinfo:
                    await ctx.send("🎶 플레이리스트 준비 중... 🎶")
                    result = self.__ytinfo['entries']
                    for i, item in tqdm(enumerate(result)):
                        self.__now.append(self.__ytinfo['entries'][i]['title'])
                        self.__songs[self.__ytinfo['entries'][i]['title']] = self.__ytinfo['entries'][i]['url']
                else:
                    await ctx.send("준비 중...")
                    self.__now.append(self.__ytinfo['title'])
                    self.__songs[self.__ytinfo['title']] = self.__ytinfo['webpage_url']
                return 0
            else:
                await ctx.send("재생할 수 있는게 없습니다.️ 🙅")
                return -1
        else:
            await ctx.send("유튜브에서 아무것도 받아올 수 없었습니다. ️🙅")
            return -1

    async def __play_song(self, ctx):
        while self.__now:
            title = self.__now[0]
            self.__now_title = title
            self.__prev.append(title)
            await self.__ytDownload(self.__songs[title])
            print(f'duration : {self.dur}')
            if self.__bot_voice and self.__bot_voice.is_connected():
                await ctx.send(f"🎶 ~ {self.__now_title} ~ 🎶")
                self.__bot_voice.play(discord.FFmpegOpusAudio(self.__ytinfo['formats'][0]['url'],
                                                              before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                                              options="-vn"), after=lambda e: time.sleep(5))
                await asyncio.sleep(self.dur + 10)
                self.__prev.append(self.__now.popleft())
            else:
                return await ctx.send("봇이 음성채널에 없습니다. 🙅")

    @commands.command()
    async def play(self, ctx, *args):
        args_list = list(args)
        args_len = len(args_list)
        await ctx.send("Loading...")
        if args_len == 1 and re.search(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$', args[0]):
            if ctx.author.voice and ctx.author.voice.channel:
                user_voice = ctx.author.voice.channel
                self.__bot_voice = await user_voice.connect()
            else:
                await ctx.send("음성 채널에 없습니다. 🙅")
                return
            await self.__set_song_list(ctx, args_list[0])
            await ctx.send("🎧 음악 재생 시작 🎧")
            return await self.__play_song(ctx)
        else:
            return await ctx.send("\"!play | !틀어줘 [유튜브 링크]\"를 입력해주세요")


    @commands.command(name="틀어줘")
    async def playkor(self,ctx):
        return await self.play.invoke(ctx)

    @commands.command()
    async def volume(self, ctx, volume: int): # from discord.py example
        if self.__bot_voice is None:
            return await ctx.send("봇이 음성채널에 없습니다. 🙅")

        self.__bot_voice.source.volume = volume / 100
        return await ctx.send(f"현재 음량 : {volume}%")

    @commands.command(name = "크기")
    async def korvol(self, ctx):
        return await self.korvol.invoke(ctx)

    @commands.command()
    async def nowplay(self,ctx):
        plist = ""
        with io.StringIO() as strbuf:
            strbuf.write("> **🎙 Now Playing.. 🎙**\n")
            strbuf.write(f"> *{self.__now_title}*\n\n")
            if self.__now :
                strbuf.write("> **💿 Playlist 💿**\n")
                for idx in range(1, len(self.__now)):
                    strbuf.write("> {}.\t{}\n".format(idx, self.__now[idx]))
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

    @commands.command()
    async def prev(self, ctx):
        if self.__prev:
            if self.__bot_voice and self.__bot_voice.is_playing():
                self.__bot_voice.stop()
                await ctx.send(f"이전 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__prev[-1]}*\n")
                self.__now.appendleft(self.__prev.pop())
                await self.__play_song(ctx)
            else:
                await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")
                return
        else:
            await ctx.send("이전에 들었던 음악이 없습니다. ️🙅")

    @commands.command(name="이전")
    async def korprev(self, ctx):
        await self.prev.invoke(ctx)

    @commands.command()
    async def next(self, ctx):
        if self.__now:
            if self.__bot_voice and self.__bot_voice.is_playing():
                self.__bot_voice.stop()
                await ctx.send(f"다음 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__now[1]}*\n")
                self.__prev.append(self.__now.popleft())
                await self.__play_song(ctx)
            else:
                await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")
                return
        else:
            await ctx.send("다음 음악이 없습니다. ️🙅")

    @commands.command(name="다음")
    async def nextkor(self, ctx):
        await self.next.invoke(ctx)

    @commands.command()
    async def shuffle(self, ctx):
        if self.__bot_voice and self.__bot_voice.is_playing():
            if len(self.__now) > 2:
                await ctx.send("🎶 플레이리스트가 흔들립니다!! 🎶")
                random.shuffle(self.__now[1:])
            else:
                await ctx.send("흔들릴 플레이리스트가 없습니다. 🙅")
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")
            return

    @commands.command(name="셔플")
    async def korshuffle(self, ctx):
        await self.shuffle.invoke(ctx)

    @commands.command()
    async def repeat(self, ctx, arg="0"):
        total_songs = list(self.__songs.keys())
        if arg == "0" or arg == "1":
            await ctx.send("플레이리스트를 반복합니다.")
            self.__now +=  total_songs * 10
        else:
            if isinstance(int(arg), int):
                await ctx.send(f"플레이리스트를 {arg}번 반복합니다.")
                self.__now += total_songs * int(arg)
            else:
                await ctx.send("반복횟수를 잘못 입력하셨습니다. 🙅")

    @commands.command(name="반복")
    async def korrepeat(self, ctx, arg):
        await self.repeat.invoke(ctx, arg)

class ytLogger:
    def __init__(self, ytm: ytMusic):
        self.ytm = ytm

    def debug(self, msg):
        print("debug from yt:",msg)
        if "[generic] videoplayback" in msg:
            dur = int(msg.split('&')[-1].split(':')[0].replace("dur=",""))
            self.ytm.dur = dur
            print('chk duration :', self.ytm.dur)
        self.ytm.chk_err = 1

    def warning(self, msg):
        print("warning from yt:", msg)
        self.ytm.__chk_err = 2

    def error(self, msg):
        print("error from yt:", msg)
        self.ytm.__chk_err = -1
