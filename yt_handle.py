from discord.ext import commands
from collections import deque
import io, discord, asyncio, random
import youtube_dl


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
        if error is not None:
            await ctx.send("알 수 없는 오류로 계속 재생할 수 없습니다.")
            return
        if not self.__now:
            if self.__bot_voice and self.__bot_voice.is_connected():
                fincoro = asyncio.gather(asyncio.sleep(60),
                                         ctx.send("더이상 재생할 음악이 없으므로 음성채널에서 나갑니다."),
                                         self.__bot_voice.disconnect)
                finish = asyncio.run_coroutine_threadsafe(fincoro, self.__bot.loop)
                try:
                    finish.result()
                except Exception as e:
                    await ctx.send(f"Error from finishing playing : {e}")
                return
        while self.__now:
            try:
                title = self.__now.popleft()
                self.__prev.append(title)
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
                        await ctx.send(f"Error with not connect : {e}")
            except Exception as e:
                err_msg = ctx.send("재생도중 오류가 발생하여 재생을 중단합니다.")
                if self.__bot_voice.is_connected():
                    err = asyncio.run_coroutine_threadsafe(err_msg, self.__bot.loop)
                    try:
                        err.result()
                        asyncio.run_coroutine_threadsafe(self.__bot_voice.disconnect, self.__bot.loop)
                    except Exception as e:
                        await ctx.send(f"Error while playing : {e}")

    async def __playYTlist(self, ctx, url : str):
        await ctx.send("Loading...")
        get_yt_chk = await self.__set_song_list(ctx, url)
        if get_yt_chk < 0:
            return
        else:
            await ctx.send("🎧 음악 재생 시작 🎧")
            title = self.__now.popleft()
            self.__prev.append(title)
            self.__ytDownload(self.__songs[title])
            if self.__bot_voice and self.__bot_voice.is_connected():
                await ctx.send(f"streaming...{title}")
                self.__bot_voice.play(discord.FFmpegPCMAudio(self.__ytinfo['formats'][0]['url'],
                                                   before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                                   options="-vn"),
                            after=self.__continue)
            else:
                await ctx.send("봇이 음성채널에 없습니다.")

    async def __replayList(self, ctx):
        await ctx.send("Loading...")
        await ctx.send("🎧 다시 재생 시작 🎧")
        title = self.__now.popleft()
        self.__prev.append(title)
        self.__ytDownload(self.__songs[title])
        if self.__bot_voice and self.__bot_voice.is_connected():
            await ctx.send(f"streaming...{title}")
            self.__bot_voice.play(discord.FFmpegPCMAudio(self.__ytinfo['formats'][0]['url'],
                                               before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                               options="-vn"),
                        after=self.__continue)
        else:
            await ctx.send("봇이 음성채널에 없습니다. 🙅")

    @commands.command()
    async def play(self, ctx, *args):
        args_list = list(args)
        args_len = len(args_list)
        if ctx.author.voice and ctx.author.voice.channel:
            user_voice = ctx.author.voice.channel
            self.__bot_voice = await user_voice.connect()
        else:
            await ctx.send("음성 채널에 없습니다. 🙅")
            return
        await ctx.message.delete()

        if args_len == 1:
            await self.__playYTlist(ctx, args_list[0])

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
            await ctx.send("음성채널에 없습니다. 🙅")

    @commands.command(name="그만")
    async def stopkor(self, ctx):
        await self.stop.invoke(ctx)

    @commands.command()
    async def prev(self, ctx):
        if self.__prev:
            if self.__bot_voice and self.__bot_voice .is_playing():
                self.__bot_voice.stop()
                await ctx.send(f"이전 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__prev[-1]}*\n")
                self.__now.appendleft(self.__prev.pop())
                await self.__replayList(ctx)
            else:
                await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")
                return
        else:
            await ctx.send("이전에 들었던 음악이 없습니다. ️🙅")

    @commands.command(name="이전")
    async def korprev(self,ctx):
        await self.prev.invoke(ctx)

    @commands.command()
    async def next(self, ctx):
        if len(self.__now) > 2:
            if self.__bot_voice and self.__bot_voice.is_playing():
                self.__bot_voice.stop()
                await ctx.send(f"다음 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__now[1]}*\n")
                self.__now.popleft()
                await self.__replayList(ctx)
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
            self.__bot_voice.stop()
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다.")
            return
        if len(self.__now) > 2:
            await ctx.send("🎶 플레이리스트가 흔들립니다!! 🎶")
            random.shuffle(self.__now)
            await self.__replayList(ctx)
        else:
            await ctx.send("흔들릴 플레이리스트가 없습니다.")

    @commands.command(name="셔플")
    async def korshuffle(self, ctx):
        await self.shuffle.invoke(ctx)

    @commands.command()
    async def repeat(self, ctx, arg="0"):
        temp = self.__prev[:] + self.__now[:]
        if arg == "0" or arg == "1":
            await ctx.send("플레이리스트를 반복합니다.")
            self.__now += temp * 10
        else:
            if isinstance(int(arg), int):
                await ctx.send(f"플레이리스트를 {arg}번 반복합니다.")
                self.__now += temp * int(arg)
            else:
                await ctx.send("반복횟수를 잘못 입력하셨습니다")

    @commands.command(name="반복")
    async def korrepeat(self, ctx, arg):
        await self.repeat.invoke(ctx, arg)



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


'''
