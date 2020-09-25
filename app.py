# ==================================== Outer Space ==========================================
from sanic import Sanic,response
from multiprocessing import *

from botTool import *

app = Sanic(__name__)
bot = commands.Bot(command_prefix='!')
isBot = "봇 대기중"

# ====================================== Bot part ===========================================
songlist = {}
titles = []
songidx = 0
repeatsong = False

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("😱 없는 명령어입니다. 😱")
    # if isinstance(error, commands.CommandInvokeError):
    #     await ctx.send("명령을 실행하던 중에 오류가 발생했습니다. 😭")
    #     print(error)

@bot.event
async def on_ready():
    print("봇 : {} => 로그인!".format(bot.user))

@bot.event
async def on_disconnect():
    if bot.is_closed():
        bot.clear()
        await asyncio.sleep(10)
        await bot.start(token = getToken("config.json"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith("ㄹㅇㅋㅋ"):
        channel = message.channel
        def check(m):
            return m.content == "ㄹㅇㅋㅋ" and m.channel == channel
        msg = await bot.wait_for('message', check=check)
        await channel.send("{.content}만 치셈 ㅋㅋ".format(msg))

    await bot.process_commands(message)  # bot event와 command를 같이 쓰기위해 필수로 넣어야

@bot.command(name = "roll")
async def roll(ctx, *args):
    strlist = list(args)
    await ctx.send("🎊 {} 🎉".format(strlist[random.randint(0, len(strlist)-1)]))

@bot.command(name = "룰렛")
async def korroll(ctx):
    await roll.invoke(ctx)

@bot.command(name = "ytidpw")
async def getidpw(ctx, *args):
    if ctx.channel.type is not discord.ChannelType.private :
        await ctx.message.delete()
        await ctx.author.send("봇 DM으로 보내주세요! // Send yours bot DM!")
    else :
        with open("youtube.json", "r", encoding='utf-8') as ytconf:
            data = ytconf.read()
        if data is not None:
            ytidpw = json.loads(data)
        else :
            ytidpw = {}
        ytidpw[args[0]] = pbkdf2_sha512.hash(args[1])
        with open("youtube.json", "w", encoding='utf-8') as ytconf:
            ytconf.write(json.dumps(ytidpw))
        await ctx.author.send("ID와 비밀번호 저장 성공\nSave success!")

@bot.command(name = "play")
async def play(ctx, *args):
    try :
        global uservoice, vc, songlist, titles, songidx, repeatsong
        uservoice = ctx.author.voice.channel
        vc = get(bot.voice_clients, guild=ctx.guild)

        if vc and vc.is_connected():
            await vc.move_to(uservoice)
        else:
            vc = await uservoice.connect()

        await ctx.message.delete()
        with open("youtube.json", "r", encoding='utf-8') as ytconf:
            data = ytconf.read()
        ytidpw = json.loads(data)
        url = ""
        if (len(args) == 0):
            await ctx.send("{유튜브 링크}나 봇에 등록된 {유튜브 아이디 비밀번호 유튜브 링크}를 입력해주세요")
            return
        elif (len(args) == 1):
            url = args[0]
        elif (len(args) == 2):
            await ctx.send("링크만 입력해주세요.")
        else:
            ydlID = args[0]
            ydlPW = ytidpw[args[0]]
            if pbkdf2_sha512.verify(args[1], ydlPW):
                ydlPW = args[1]
            else:
                await ctx.send("비밀번호가 맞지 않습니다. \n passwd not corrected!")
                return
            ydl_opt['username'] = ydlID # ydl_opt from botTool
            ydl_opt['password'] = ydlPW # ydl_opt from botTool
            url = args[2]
        await ctx.send("음악 준비중입니다...")
        await getSonglist(ctx, songlist, url)
        titles = list(songlist.keys())
        await playYTlist(bot, ctx, uservoice, vc, songlist, titles, songidx)

    except AttributeError:
        await ctx.message.delete()
        await ctx.send("음성채널에 있어야 실행됩니다.\n Only available when connected Voice Channel")

@bot.command(name = "틀어줘")
async def playkor(ctx):
    await play.invoke(ctx)

@bot.command(name = "nowplay")
async def showlist(ctx):
    global titles,songidx
    plist = ""
    with io.StringIO() as strbuf:
        strbuf.write("> **🎙 Now Playing.. 🎙**\n")
        strbuf.write("> *{}*\n\n".format(titles[songidx]))
        if len(songlist) > 0:
            strbuf.write("> **💿 Playlist 💿**\n")
            i = 1
            for idx in range(songidx+1, len(titles)):
                if i > len(songlist)-1:
                    break
                nowidx = idx % len(titles)
                strbuf.write("> {}. {}\n".format(i, titles[nowidx]))
                i+=1
        plist = strbuf.getvalue()
    await ctx.send(plist)

@bot.command(name = "prev")
async def goprev(ctx):
    global titles, songidx
    if 0 < songidx < len(titles):
        if vc.is_playing():
            vc.pause()
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다.")
            return
        songidx -= 1
        await ctx.send("이전 음악을 재생합니다. ➡️ 🎵 🎶 *{}*\n".format(titles[songidx]))
        info = ytDownload(songlist[titles[songidx]])
        vc.source = discord.FFmpegPCMAudio(info['formats'][0]['url'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        vc.resume()
    else :
        await ctx.send("더이상 재생할 음악이 없습니다.️🙅 ")

@bot.command(name = "이전")
async def korprev(ctx):
    await goprev.invoke(ctx)

@bot.command(name = "next")
async def gonext(ctx):
    global titles, songidx
    if songidx < len(titles):
        if vc.is_playing():
            vc.pause()
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다.")
            return
        songidx+=1
        await ctx.send("다 음악을 재생합니다. ➡️ 🎵 🎶 *{}*\n".format(titles[songidx]))
        info = ytDownload(songlist[titles[songidx]])
        vc.source = discord.FFmpegPCMAudio(info['formats'][0]['url'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        vc.resume()
    else :
        await ctx.send("더이상 재생할 음악이 없습니다.️🙅 ")

@bot.command(name = "다음")
async def nextkor(ctx):
    await gonext.invoke(ctx)

@bot.command(name = "stop")
async def stop(ctx):
    if vc and vc.is_connected():
        await vc.disconnect()
        await ctx.send("음악 재생을 멈춥니다.")
    else :
        await ctx.send("음성채널에 없습니다.")

@bot.command(name = "그만")
async def stopkor(ctx):
    await stop.invoke(ctx)

@bot.command(name = "shuffle")
async def shufflelist(ctx):
    global songlist,titles
    if len(songlist) > 0:
        await ctx.send("🎶 플레이리스트가 흔들립니다!! 🎶")
        if vc.is_playing():
            vc.pause()
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다.")
            return
        temp = list(songlist.items())
        random.shuffle(temp)
        songlist = dict(temp)
        titles = list(songlist.keys())
        info = ytDownload(songlist[titles[songidx]])
        vc.source = discord.FFmpegPCMAudio(info['formats'][0]['url'],
                                           before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                           options="-vn")
        vc.resume()
    else :
        await ctx.send("흔들릴 플레이리스트가 없습니다.")

@bot.command(name = "셔플")
async def korshuffel(ctx):
    await shufflelist.invoke(ctx)

@bot.command(name = "repeat")
async def repeatlist(ctx, arg="0"):
    global songidx, titles
    if arg == "0" or arg == "1":
        await ctx.send("플레이리스트를 반복합니다.")
        titles += titles
    else :
        if isinstance(int(arg), int):
            await ctx.send("플레이리스트를 {}번 반복합니다.".format(arg))
            num = int(arg)
            temp = titles*num
            titles += temp
        else:
            await ctx.send("반복횟수를 잘못입력하셨습니다")

@bot.command(name = "반복")
async def korrepeat(ctx, arg):
    await repeatlist.invoke(ctx, arg)

# ==================================== Web application Part ======================================

@app.route("/")
async def exe_bot(request):
    return response.text("{0} : 서버가 구동중입니다. // {1}".format(time.strftime("%c", time.localtime(time.time())), isBot))

# ================================================================================================

if __name__ == '__main__':
    botToken = getToken("config.json")  # string
    botTh = Process(target=bot.run, args=(botToken,))

    if botToken is not None:
        botTh.start()
        isBot = "봇이 실행중입니다."
    else:
        isBot = "봇이 실행되고 있지 않습니다."

    serverTh = Process(target=app.run)
    serverTh.start()
    botTh.join()
    serverTh.join()