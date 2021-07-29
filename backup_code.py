'''2021-07-29 - 1
    async def __playYTlist(self, ctx, url : str):
        await ctx.send("Loading...")
        get_yt_chk = await self.__set_song_list(ctx, url)
        if get_yt_chk < 0:
            return
        else:
            await ctx.send("🎧 음악 재생 시작 🎧")
            title = self.__now[0]
            self.__now_title = title
            self.__prev.append(title)
            self.__ytDownload(self.__songs[title])
            if self.__bot_voice and self.__bot_voice.is_connected():
                await ctx.send(f"streaming...{title}")
                self.__bot_voice.play(discord.FFmpegPCMAudio(self.__ytinfo['formats'][0]['url'],
                                               before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                               options="-vn"),
                                    after=lambda e : self._continue_wrapper(ctx, e))
            else:
                await ctx.send("봇이 음성채널에 없습니다. 🙅")

    async def _continue_wrapper(self, ctx, e):
        await self.__continue(ctx, e)

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
                    await ctx.send(f"Error from finishing playing : {e}")
                return
        while self.__now:
            try:
                self.__now.popleft()
                title = self.__now[0]
                self.__now_title = title
                self.__prev.append(title)
                self.__ytDownload(self.__songs[title])
                if self.__bot_voice and self.__bot_voice.is_connected():
                    self.__bot_voice.play(discord.FFmpegPCMAudio(self.__ytinfo['formats'][0]['url'],
                                                             before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                                             options="-vn"),
                                      after=lambda e :  self._continue_wrapper(ctx, e))
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


    async def __replayList(self, ctx, title:str = ""):
        await ctx.send("Loading...")
        await ctx.send("🎧 다시 재생 시작 🎧")
        self.__ytDownload(self.__songs[title])
        if self.__bot_voice and self.__bot_voice.is_connected():
            await ctx.send(f"streaming...{title}")
            self.__bot_voice.play(discord.FFmpegPCMAudio(self.__ytinfo['formats'][0]['url'],
                                           before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                           options="-vn"),
                    after= lambda e : self._continue_wrapper(ctx, e))
        else:
            await ctx.send("봇이 음성채널에 없습니다. 🙅")

    @commands.command()
    async def show_now(self, ctx):
        await ctx.send(self.__now)

    @commands.command()
    async def show_prev(self, ctx):
        await ctx.send(self.__prev)
'''
''' -2
 @commands.command()
 async def prev(self, ctx):
     if self.__prev:
         if self.__bot_voice and self.__bot_voice .is_playing():
             self.__bot_voice.stop()
             await ctx.send(f"이전 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__prev[-1]}*\n")
             self.__now.appendleft(self.__prev.pop())
             await self.__replayList(ctx, self.__now[0])
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
     if self.__now:
         if self.__bot_voice and self.__bot_voice.is_playing():
             self.__bot_voice.stop()
             await ctx.send(f"다음 음악을 재생합니다. ➡️ 🎵 🎶 *{self.__now[0]}*\n")
             self.__prev.append(self.__now.popleft())
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
         await ctx.send("현재 음악을 재생하고 있지 않습니다. 🙅")
         return
     if len(self.__now) > 2:
         await ctx.send("🎶 플레이리스트가 흔들립니다!! 🎶")
         random.shuffle(self.__now)
         await self.__replayList(ctx)
     else:
         await ctx.send("흔들릴 플레이리스트가 없습니다. 🙅")

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
             await ctx.send("반복횟수를 잘못 입력하셨습니다. 🙅")

 @commands.command(name="반복")
 async def korrepeat(self, ctx, arg):
     await self.repeat.invoke(ctx, arg)
'''
