import json, io, discord, asyncio, youtube_dl

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

async def getSonglist(songlist:list, urllist:list, ydl_opt, url):
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            result = info['entries']
            for i, item in enumerate(result):
                songlist.append(info['entries'][i]['title'])
                urllist.append(info['entries'][i]['webpage_url'])
        else:
            songlist.append(info['title'])
            urllist.append(info['webpage_url'])

async def playYTlist(ctx,songlist:list, urllist:list, uservoice, vc, ydl_opt):
    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
        while len(urllist) > 0 and len(songlist) > 0:
            info = ydl.extract_info(urllist.pop(0), download=False)
            if vc and vc.is_connected():
                await vc.move_to(uservoice)
            else:
                vc = await uservoice.connect()
            await ctx.send("음악 재생 시작!")
            vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url']))
            vc.volume = 80
            if vc.is_playing():
                await asyncio.sleep(info['duration']+5)
            songlist.pop(0)

# async def playYTlist(songlist:list, urllist:list, uservoice, vc, ydl_opt):
#     with youtube_dl.YoutubeDL(ydl_opt) as ydl:
#         while len(urllist) > 0 and len(songlist) > 0:
#             info = ydl.extract_info(urllist.pop(0), download=True)
#             if vc and vc.is_connected():
#                 await vc.move_to(uservoice)
#             else:
#                 vc = await uservoice.connect()
#             playfile = "./music/{}".format(os.listdir("./music").pop())
#             vc.play(discord.FFmpegPCMAudio(playfile))
#             vc.volume = 80
#             if vc.is_playing():
#                 await asyncio.sleep(info['duration']+5)
#             songlist.pop(0)
#             if os.path.isfile(playfile):
#                 os.remove(playfile)

