from sanic import Sanic, response
from multiprocessing import *
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio, guild
from passlib.hash import pbkdf2_sha512
import discord, io, asyncio, time, random, json, os

import botTool

app = Sanic(__name__)
bot = commands.Bot(command_prefix='!')
isBot = "봇 대기중"

@bot.event
async def on_ready():
    print("봇 : {} => 로그인!".format(bot.user))

@bot.event
async def on_disconnect():
    if vc and vc.is_connected():
        await vc.disconnect()
    print("봇 : {} => 로그아웃...".format(bot.user))

@bot.event
async def on_message(message):
    await bot.process_commands(message) # bot event와 command를 같이 쓰기위해 필수로 넣어야
    if message.author == bot.user:
        return

    if message.content.startswith("ㄹㅇㅋㅋ"):
        await message.channel.send("ㄹㅇㅋㅋ만 치셈")

@bot.event
async def getPM(ctx):
    print("{} from PM".format(ctx.content))

@bot.command(name = "roll")
async def roll(ctx, *args):
    strlist = list(args)
    await ctx.send("🎊 {} 🎉".format(strlist[random.randint(0, len(strlist)-1)]))

@bot.command(name = "룰렛")
async def 룰렛(ctx):
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
    downloadedfiles = os.listdir("./music")
    while len(downloadedfiles) != 0:
        os.remove("./music/{}".format(downloadedfiles.pop()))
    global songlist, urllist
    songlist = []
    urllist = []
    try :
        global uservoice, vc
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
            'audioformat': 'mp3',
            'outtmpl': u'music/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }
        if (len(args) == 0):
            await ctx.send("{유튜브 링크}나 봇에 등록된 {유튜브 아이디 비밀번호 유튜브 링크}를 입력해주세요")
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
        await botTool.getSonglist(songlist, urllist, ydl_opt, url)
        await botTool.playYTlist(songlist, urllist, uservoice, vc, ydl_opt)

    except AttributeError:
        await ctx.message.delete()
        await ctx.send("음성채널에 있어야 실행됩니다.\n Only available when connected Voice Channel")
        return

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

@bot.command(name = "stop")
async def stop(ctx):
    if vc and vc.is_connected():
        await vc.disconnect()
        await ctx.send("음악 재생을 멈춥니다.")
        downloadedfiles = os.listdir("./music")
        while len(downloadedfiles) != 0:
            if len(downloadedfiles) == 0:
                break
            os.remove(downloadedfiles.pop())
    else :
        await ctx.send("음성채널에 없습니다.")

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