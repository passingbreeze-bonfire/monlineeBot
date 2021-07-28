import time

from discord.ext import commands
from discord.utils import get
from passlib.hash import pbkdf2_sha512
from collections import deque
import io, discord, asyncio, re
import pprint, youtube_dl

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
        self.__yturl = ""
        self.__opt = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'ignoreerrors': True,
            'forceduration': False,
            'logger': ytLogger(self),
            'default_search': 'ytsearch',
            'sleep_interval': 10,
            'max_sleep_interval': 60,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }
        self.__ytinfo = None

    def stop_song(self):
        self.__songs.clear()
        self.__now.clear()
        self.__prev.clear()

    def get_song_list(self):
        return self.__now

    def __ytDownload(self, url):
        print("downloading...")
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
                    result = self.__ytinfo['entries']
                    for i, item in enumerate(result):
                        self.__now.append(self.__ytinfo['entries'][i]['title'])
                        self.__songs[self.__ytinfo['entries'][i]['title']] = self.__ytinfo['entries'][i]['url']
                else:
                    self.__now.append(self.__ytinfo['title'])
                    self.__songs[self.__ytinfo['title']] = self.__ytinfo['webpage_url']
                return 0
            else:
                await ctx.send("재생할 수 있는게 없습니다.️ 🙅")
                return -1
        else:
            await ctx.send("유튜브에서 아무것도 받아올 수 없었습니다. ️🙅")
            return -1

    async def __continue(self, ctx, error):
        if not self.__now:
            if self.__bot_voice and self.__bot_voice.is_connected():
                fincoro = asyncio.gather(asyncio.sleep(60),
                                         ctx.send("더이상 재생할 음악이 없으므로 음성채널에서 나갑니다."),
                                         self.__bot_voice.disconnect)
                finish = asyncio.run_coroutine_threadsafe(fincoro, self.__bot.loop)
                try:
                    finish.result()
                except Exception as e:
                    print("Error from finishing playing :", e)
                return
        while self.__now:
            try:
                title = self.__now.popleft()
                self.__ytDownload(self.__songs[title])
                if self.__bot_voice and self.__bot_voice.is_connected():
                    self.__bot_voice.play(discord.FFmpegPCMAudio(self.__ytinfo['formats'][0]['url'],
                                                                 before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                                                 options="-vn"),
                                          after=self.__continue)
                else:
                    not_connect_msg = ctx.send("음성채널에 연결되어있지 않아 재생을 중단합니다.")
                    try:
                        not_connect_msg = asyncio.run_coroutine_threadsafe(not_connect_msg, self.__bot.loop)
                        not_connect_msg.result()
                    except Exception as e:
                        print("Error from not connected voice channel : ", e)
            except Exception as e:
                err_msg = ctx.send("재생도중 오류가 발생하여 재생을 중단합니다.")
                if self.__bot_voice.is_connected():
                    err = asyncio.run_coroutine_threadsafe(err_msg, self.__bot.loop)
                    try:
                        err.result()
                        asyncio.run_coroutine_threadsafe(self.__bot_voice.disconnect, self.__bot.loop)
                    except Exception as e:
                        print("Error from playlist error : ", e)

    async def playYTlist(self, ctx, url : str):
        await ctx.send("음악 준비중입니다...")
        bot_scheduler = AsyncIOScheduler(loop=self.__bot.loop)
        get_yt_chk = await self.__set_song_list(ctx, url)
        if get_yt_chk < 0:
            return
        else:
            await ctx.send("🎧 음악 재생 시작 🎧")
            # print(self.__now)
            # title = self.__now.popleft()
            async def play_song(title):
                self.__ytDownload(self.__songs[title])
                await ctx.send(f"streaming...{title}")
                if self.__bot_voice and self.__bot_voice.is_connected():
                    self.__bot_voice.play(discord.FFmpegPCMAudio(self.__ytinfo['formats'][0]['url'],
                                                       before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                                       options="-vn"),
                                after=None)

                time.sleep(self.__ytinfo['duration'])

            rx.from_iterable(self.__now, bot_scheduler).pipe(
                ops.debounce(self.__ytinfo['duration']+10, bot_scheduler),
            ).subscribe(
                on_next = lambda t : await play_song(t),
                on_error = lambda e: print(f"Error on Observer: {e}")
            )
            # def play_song(title : str):
            #     if self.__bot_voice and self.__bot_voice.is_connected():
            #         source = self.__ytDownload(self.__songs[title])
            #         self.__bot_voice.play(discord.FFmpegPCMAudio(source['formats'][0]['url'],
            #                               before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            #                               options="-vn"),
            #                               after = play_song)
            #     else:
            #         not_con_msg = ctx.send("음성채널에 연결되어있지 않아 재생을 중단합니다.")
            #         try:
            #             not_connected = asyncio.run_coroutine_threadsafe(not_con_msg, self.__bot)
            #             not_connected.result()
            #         except Exception as e:
            #             print("Error from not connected voice channel : ", e)
            #             err_msg = ctx.send("재생도중 오류가 발생하여 재생을 중단합니다.")
            #             err = asyncio.run_coroutine_threadsafe(err_msg, self.__bot)
            #             err.result()
            #             asyncio.run_coroutine_threadsafe(self.__bot_voice.disconnect, self.__bot)
            #
            # def fin_song():
            #     if self.__bot_voice and self.__bot_voice.is_connected():
            #         fincoro = asyncio.gather(asyncio.sleep(60),
            #                                  ctx.send("더이상 재생할 음악이 없으므로 음성채널에서 나갑니다."),
            #                                  self.__bot_voice.disconnect)
            #         finish = asyncio.run_coroutine_threadsafe(fincoro, self.__bot)
            #         try:
            #             finish.result()
            #         except Exception as e:
            #             print("Error from finishing playing :", e)



    @commands.command()
    async def play(self, ctx, *args):
        args_list = list(args)
        args_len = len(args_list)
        if args_len == 1:
            if ctx.author.voice and ctx.author.voice.channel:
                user_voice = ctx.author.voice.channel
                self.__bot_voice = await user_voice.connect()
            else:
                await ctx.send("음성 채널에 없음!")
                return
            await ctx.message.delete()
            await self.playYTlist(ctx, args_list[0])
        else:
            await ctx.send("\"!play | !틀어줘 [유튜브 링크]\"를 입력해주세요")
            return

    @commands.command(name="틀어줘")
    async def playkor(self,ctx):
        await self.play.invoke(ctx)

    @commands.command()
    async def nowplay(self,ctx):
        titles = self.get_song_list()
        titles_len = len(titles)
        plist = ""
        with io.StringIO() as strbuf:
            strbuf.write("> **🎙 Now Playing.. 🎙**\n")
            strbuf.write("> *{}*\n\n".format(titles[0]))
            if titles_len > 0:
                strbuf.write("> **💿 Playlist 💿**\n")
                for idx in range(1, titles_len):
                    strbuf.write("> {}. {}\n".format(idx, titles[idx]))
            plist = strbuf.getvalue()
        await ctx.send(plist)

    @commands.command()
    async def stop(self, ctx):
        if self.__bot_voice and self.__bot_voice.is_connected():
            await self.__bot_voice.disconnect()
            await ctx.send("음악 재생을 멈춥니다.")
            self.stop_song()
        else:
            await ctx.send("음성채널에 없습니다.")

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
'''

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

'''

'''

@bot.command(name = "prev")
async def go_prev(ctx):
    global prevone,titles
    if len(prevone) > 0:
        prevTitle = list(prevone.keys())[0]
        if bot_voice.is_playing():
            bot_voice.stop()
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다.")
            return
        await ctx.send("이전 음악을 재생합니다. ➡️ 🎵 🎶 *{}*\n".format(prevTitle))
        titles.insert(0, prevTitle)
        await yt_handler.playYTlist(ctx, user_voice, bot_voice)
        # info = ytDownload(prevone[prevTitle])
        # vc.source = discord.FFmpegPCMAudio(info['formats'][0]['url'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        # vc.resume()
    else :
        await ctx.send("더이상 재생할 음악이 없습니다.️🙅 ")

@bot.command(name = "이전")
async def korprev(ctx):
    await go_prev.invoke(ctx)

@bot.command(name = "next")
async def play_next(ctx):
    global playlist, titles
    if len(playlist) > 0:
        if bot_voice.is_playing():
            bot_voice.stop()
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다.")
            return
        nowTitle = titles[0]
        titles.pop(0)
        playlist.pop(nowTitle)
        await ctx.send("다음 음악을 재생합니다. ➡️ 🎵 🎶 *{}*\n".format(titles[0]))
        await playYTlist(bot, ctx, uservoice, bot_voice, playlist, prevone, titles)
    else :
        await ctx.send("더이상 재생할 음악이 없습니다.️🙅 ")

@bot.command(name = "다음")
async def nextkor(ctx):
    await play_next.invoke(ctx)

@bot.command(name = "shuffle")
async def shufflelist(ctx):
    global playlist, titles, prevone
    if bot_voice.is_playing():
        bot_voice.stop()
    else:
        await ctx.send("현재 음악을 재생하고 있지 않습니다.")
        return
    if len(playlist) > 0:
        await ctx.send("🎶 플레이리스트가 흔들립니다!! 🎶")
        temp = list(playlist.items())
        random.shuffle(temp)
        playlist = dict(temp)
        titles = list(playlist.keys())
        prevone.clear()
        await playYTlist(bot, ctx, uservoice, bot_voice, playlist, prevone, titles)
        # info = ytDownload(playlist[titles[0]])
        # vc.source = discord.FFmpegPCMAudio(info['formats'][0]['url'],
        #                                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        #                                    options="-vn")
        # vc.resume()
    else :
        await ctx.send("흔들릴 플레이리스트가 없습니다.")

@bot.command(name = "셔플")
async def korshuffle(ctx):
    await shufflelist.invoke(ctx)

@bot.command(name = "repeat")
async def repeatlist(ctx, arg="0"):
    global songlist
    if arg == "0" or arg == "1":
        await ctx.send("플레이리스트를 반복합니다.")

    else :
        if isinstance(int(arg), int):
            await ctx.send("플레이리스트를 {}번 반복합니다.".format(arg))
            num = int(arg)
        else:
            await ctx.send("반복횟수를 잘못 입력하셨습니다")

@bot.command(name = "반복")
async def korrepeat(ctx, arg):
    await repeatlist.invoke(ctx, arg)

'''
