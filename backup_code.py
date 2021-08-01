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