from collections import deque, OrderedDict
import io, asyncio, random, time, re

import discord, youtube_dl
from discord.ext import commands

class ytMusic(commands.Cog):
    def __init__(self, bot):
        self.dur : int = 0
        self.chk_err : bool = True
        self.__bot = bot
        self.__bot_voice = None
        self.__songs = OrderedDict()
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

    def __ytDownload(self, url):
        with youtube_dl.YoutubeDL(self.__opt) as ydl:
            self.__ytinfo = ydl.extract_info(url, download=False)
            # print(self.__ytinfo)
            return self.chk_err

    async def stop_song(self):
        self.__songs.clear()
        self.__now.clear()
        self.__prev.clear()
        return await self.__bot_voice.disconnect()

    async def __set_song_list(self, ctx, url):
        if self.__ytDownload(url):
            if self.__ytinfo is not None:
                if isinstance(self.__ytinfo, dict):
                    if 'entries' in self.__ytinfo:
                        await ctx.send("🎶 플레이리스트 준비 중... 🎶")
                        result = self.__ytinfo['entries']
                        for i, item in enumerate(result):
                            self.__now.append(self.__ytinfo['entries'][i]['title'])
                            self.__songs[self.__ytinfo['entries'][i]['title']] = self.__ytinfo['entries'][i]['url']
                    else:
                        await ctx.send("🎶 한 곡 준비 중... 🎶")
                        self.dur = self.__ytinfo['duration']
                        self.__now.append(self.__ytinfo['title'])
                        self.__songs[self.__ytinfo['title']] = self.__ytinfo['webpage_url']
                    return True
        return False

    async def __play_song(self, ctx):
        while self.__now:
            title = self.__now[0]
            self.__now_title = title
            if self.__ytDownload(self.__songs[title]):
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
            else:
                return await ctx.send("플레이리스트 중에 재생할 수 없는 링크가 있습니다. ️🙅")
        else:
            await self.stop_song()
            return await ctx.send("모든 음악의 재생이 끝났습니다.")

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
                return await ctx.send("음성 채널에 없습니다. 🙅")
            if await self.__set_song_list(ctx, args_list[0]):
                await ctx.send("🎧 음악 재생 시작 🎧")
                return await self.__play_song(ctx)
            else:
                await ctx.send("재생할 수 있는게 없습니다.️ 🙅")
                return await self.stop_song()
        else:
            return await ctx.send("\"!play | !틀어줘 [유튜브 링크]\"를 입력해주세요")

    @commands.command()
    async def volume(self, ctx, volume: int): # from discord.py example
        if ctx.voice_client is None:
            return await ctx.send("음성채널에 없습니다. 🙅")
        elif volume < 0 or volume > 100:
            return await ctx.send("0 ~ 100 사이의 숫자를 입력하세요.")
        ctx.voice_client.source.volume = volume / 100
        return await ctx.send(f"현재 음량 : {volume}%")

    @commands.command()
    async def nowplay(self,ctx):
        plist = ""
        if self.__bot_voice and self.__bot_voice.is_connected():
            with io.StringIO() as strbuf:
                strbuf.write("> **🎙 Now Playing.. 🎙**\n")
                strbuf.write(f"> *{self.__now_title}*\n\n")
                if self.__now :
                    strbuf.write("> **💿 Playlist 💿**\n")
                    for idx in range(1, len(self.__now)):
                        strbuf.write("> {}.\t{}\n".format(idx, self.__now[idx]))
                plist = strbuf.getvalue()
            return await ctx.send(plist)
        else:
            return await ctx.send("재생중이지 않거나 음성채널에 없습니다. 🙅")

    @commands.command()
    async def stop(self, ctx):
        if self.__bot_voice and self.__bot_voice.is_connected():
            await self.stop_song()
            return await ctx.send("재생을 멈춥니다.")
        else:
            return await ctx.send("음성채널에 없습니다. 🙅")

    @commands.command()
    async def pause(self, ctx):
        if self.__bot_voice and self.__bot_voice.is_connected() and self.__bot_voice.is_playing():
            await ctx.send("재생을 잠시 멈춥니다.")
            return await self.__bot_voice.pause()
        else:
            return await ctx.send("재생중이지 않거나 음성채널에 없습니다. 🙅")

    @commands.command(name="resume")
    async def resume_bot(self, ctx):
        if self.__bot_voice and self.__bot_voice.is_connected() and self.__bot_voice.is_paused():
            await ctx.send("재생을 재개합니다.")
            return await self.__bot_voice.resume()
        else:
            return await ctx.send("재생중이지 않거나 음성채널에 없습니다. 🙅")

    @commands.command()
    async def prev(self, ctx):
        if self.__prev:
            if self.__bot_voice and self.__bot_voice.is_playing():
                self.__bot_voice.stop()
                await ctx.send(f"이전 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__prev[-1]}*\n")
                self.__now.appendleft(self.__prev.pop())
                return await self.__play_song(ctx)
            else:
                return await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")
        else:
            return await ctx.send("이전에 들었던 음악이 없습니다. ️🙅")

    @commands.command()
    async def next(self, ctx):
        if self.__now:
            if self.__bot_voice and self.__bot_voice.is_playing():
                self.__bot_voice.stop()
                await ctx.send(f"다음 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__now[1]}*\n")
                self.__prev.append(self.__now.popleft())
                return await self.__play_song(ctx)
            else:
                return await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")
        else:
            return await ctx.send("다음 음악이 없습니다. ️🙅")

    @commands.command()
    async def shuffle(self, ctx):
        if self.__bot_voice and self.__bot_voice.is_playing():
            if len(self.__now) > 2:
                random.shuffle(self.__now[1:])
                return await ctx.send("🎶 플레이리스트가 흔들립니다!! 🎶")
            else:
                return await ctx.send("흔들릴 플레이리스트가 없습니다. 🙅")
        else:
            return await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")

    @commands.command()
    async def repeat(self, ctx, arg="0"):
        total_songs = list(self.__songs.keys())
        if arg == "0" or arg == "1":
            self.__now +=  total_songs * 10
            return await ctx.send("플레이리스트를 반복합니다.")
        else:
            if isinstance(int(arg), int):
                self.__now += total_songs * int(arg)
                return await ctx.send(f"플레이리스트를 {arg}번 반복합니다.")
            else:
                return await ctx.send("반복횟수를 잘못 입력하셨습니다. 🙅")

    @commands.command(name="틀어줘")
    async def kor_play(self, ctx):
        return await self.play.invoke(ctx)

    @commands.command(name = "음량")
    async def kor_vol(self, ctx, volume: int):
        return await self.volume.invoke(ctx, volume)

    @commands.command(name="이전")
    async def kor_prev(self, ctx):
        return await self.prev.invoke(ctx)

    @commands.command(name="다음")
    async def kor_next(self, ctx):
        return await self.next.invoke(ctx)

    @commands.command(name="다시")
    async def kor_resume(self, ctx):
        return await self.resume_bot.invoke(ctx)

    @commands.command(name="셔플")
    async def kor_shuffle(self, ctx):
        await self.shuffle.invoke(ctx)

    @commands.command(name="반복")
    async def kor_repeat(self, ctx, arg):
        return await self.repeat.invoke(ctx, arg)

    @commands.command(name="잠깐")
    async def kor_pause(self, ctx):
        return await self.pause.invoke(ctx)

    @commands.command(name="멈춰")
    async def kor_stop(self, ctx):
        return await self.stop.invoke(ctx)


class ytLogger:
    def __init__(self, ytm: ytMusic):
        self.ytm = ytm

    def debug(self, msg):
        print("debug from yt:",msg)
        if "[generic] videoplayback" in msg:
            dur = int(msg.split('&')[-1].split(':')[0].replace("dur=",""))
            self.ytm.dur = dur
            # print('chk duration :', self.ytm.dur)
        self.ytm.chk_err = True

    def warning(self, msg):
        print("warning from yt:", msg)
        self.ytm.chk_err = True

    def error(self, msg):
        print("error from yt:", msg)
        self.ytm.chk_err = False
