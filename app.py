from sanic import Sanic, response
from multiprocessing import *
from discord.ext import commands
from discord.utils import get
from passlib.hash import pbkdf2_sha512
import discord, io, asyncio, time, random, json

import botTool

app = Sanic(__name__)
bot = commands.Bot(command_prefix='!')
isBot = "봇 대기중"

def aftercoro(error):
    try:
        coro = asyncio.run_coroutine_threadsafe(botTool.playYTlist, bot.loop)
        coro.result()
    except Exception as e:
        print(e)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("😱 없는 명령어입니다. 😱")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("명령을 실행하던 중에 오류가 발생했습니다. 😭")
        print(error)

@bot.event
async def on_ready():
    print("봇 : {} => 로그인!".format(bot.user))

@bot.event
async def on_disconnect():
    if vc and vc.is_connected():
        await vc.disconnect()
    await bot.logout()
    await asyncio.sleep(20)
    await bot.login(botTool.getToken("config.json"))

@bot.event
async def on_message(message):
    await bot.process_commands(message) # bot event와 command를 같이 쓰기위해 필수로 넣어야
    if message.author == bot.user:
        return

    if message.content.startswith("ㄹㅇㅋㅋ"):
        await message.channel.send("ㄹㅇㅋㅋ만 치셈")

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
    global after
    after = aftercoro
    try :
        global uservoice, vc, ydl_opt, songlist, urllist
        songlist = []
        urllist = []
        uservoice = ctx.author.voice.channel
        vc = get(bot.voice_clients, guild=ctx.guild)
        if vc and vc.is_connected():
            await vc.move_to(uservoice)
        else:
            vc = await uservoice.connect()
        await ctx.message.delete()
        await ctx.send("음악 준비중입니다...")
        with open("youtube.json", "r", encoding='utf-8') as ytconf:
            data = ytconf.read()
        ytidpw = json.loads(data)
        url = ""
        ydl_opt = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'ignoreerrors' : False,
            'audioformat': 'mp3',
            'default_search':'ytsearch',
            'sleep_interval' : 10,
            'max_sleep_interval' : 60,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }
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
            ydl_opt['username'] = ydlID
            ydl_opt['password'] = ydlPW
            url = args[2]
        await botTool.getSonglist(ctx, songlist, urllist, ydl_opt, url)
        await botTool.playYTlist(bot, ctx, uservoice, vc, songlist, urllist, ydl_opt, after)

    except AttributeError:
        await ctx.message.delete()
        await ctx.send("음성채널에 있어야 실행됩니다.\n Only available when connected Voice Channel")

@bot.command(name = "nowplay")
async def showlist(ctx):
    plist = ""
    with io.StringIO() as strbuf:
        strbuf.write("> **🎙 Now Playing.. 🎙**\n")
        strbuf.write("> *{}*\n\n".format(songlist[0]))
        if len(songlist) > 0:
            strbuf.write("> **💿 Playlist 💿**\n")
            for i in range(1,len(songlist)+1):
                strbuf.write("> {}. {}\n".format(i, songlist[i-1]))
        plist = strbuf.getvalue()
    await ctx.send(plist)

@bot.command(name = "틀어줘")
async def playkor(ctx):
    await play.invoke(ctx)

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

@bot.command(name = "skip")
async def skip(ctx):
    if len(songlist)>0 and len(urllist)>0:
        if vc.is_playing():
            vc.pause()
        else:
            await ctx.send("현재 음악을 재생하고 있지 않습니다.")
            return
        await ctx.send("다음곡이 재생됩니다. ➡️ 🎵 🎶")
        songlist.pop(0)
        await botTool.playYTlist(bot, ctx, uservoice, vc, songlist, urllist, ydl_opt, after)
    else :
        await ctx.send("재생할 음악이 없습니다.️🙅 ")

@bot.command(name = "다음")
async def skipkor(ctx):
    await skip.invoke(ctx)

@app.route("/")
async def exe_bot(request):
    return response.text("{0} : 서버가 구동중입니다. // {1}".format(time.strftime("%c", time.localtime(time.time())), isBot))

if __name__ == '__main__':
    botToken = botTool.getToken("config.json")  # string
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


'''    
    1. !로또 | !lotto
    - 이번주 예상 1등 로또번호를 알려줍니다.
    * Tell expected 1st Win Korean Lottery number in Channel

'''