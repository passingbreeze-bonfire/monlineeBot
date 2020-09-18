from sanic import Sanic, response
from multiprocessing import *
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio, guild
from passlib.hash import pbkdf2_sha512
import discord, asyncio, time, random, json, os, youtube_dl

import botTool

app = Sanic(__name__)
bot = commands.Bot(command_prefix='!')
isBot = "봇 대기중"

@bot.event
async def on_ready():
    print("봇 : {} => 로그인!".format(bot.user))

@bot.event
async def on_disconnect():
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
    songlist = asyncio.Queue()
    try :
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
            'outtmpl': u'music/%(playlist_index)s-%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }
        if (len(args) == 3):
            print(args[0], args[1], ytidpw[args[0]])
            ydlID = args[0]
            ydlPW = ytidpw[args[0]]
            if pbkdf2_sha512.verify(args[1], ydlPW):
                ydlPW = args[1]
            else:
                await ctx.send("비밀번호가 맞지 않습니다. \n passwd not corrected!")
                return
            ydl_opt = {
                'username': ydlID,
                'password': ydlPW,
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': 'mp3',
                'outtmpl': u'music/%(playlist_index)s-%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }],
            }
            url = args[2]
        elif (len(args) == 2):
            await ctx.send("링크만 입력해주세요.")
        else:
            url = args[0]

        with youtube_dl.YoutubeDL(ydl_opt) as ydl:
            ydl.download([url])

        for file in os.listdir("./music"):
            if file.endswith(".mp3"):
                songlist.put_nowait("./music/" + file)

        if not songlist.empty():
            vc.play(discord.FFmpegPCMAudio(songlist.get()))
            vc.volume = 100
            print(vc.is_playing())
            time.sleep(10)

    except AttributeError:
        await ctx.message.delete()
        await ctx.send("음성채널에 있어야 실행됩니다.\n Only available when connected Voice Channel")
        return

@bot.command(name = "stop")
async def stop(ctx):
    uservoice = ctx.author.voice.channel
    vc = get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_connected():
        await vc.disconnect()
        await ctx.send("음악 재생을 멈춥니다.")
    else :
        await ctx.send("음성채널에 없습니다.")

    # song_there = os.path.isfile("song.mp3")
    # try :
    #     if song_there:
    #         os.remove("song.mp3")
    # except PermissionError:
    #     await ctx.send("잠시 기다리면 음악이 재생됩니다. !나감 || !stop을 입력하면 재생을 중단합니다.")
    #     return

''' bot이 개인 사용자에게 보내는 메시지 코드
@bot.command(name = "poke")
async def poke(ctx):
    await ctx.author.send("boop!")
'''


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
    1. !틀어줘 노래제목/유튜브 링크 | !music title/youtube link
    - 유튜브 링크가 아니면 동작하지 않습니다
    * Only available youtube link
    - 유튜브에서 듣고싶은 음악 혹은 플레이리스트를 찾아서 틀어줍니다. 라디오 모드로 링크가 재생됩니다.
    * Find music or playlist what you wanna hear in Youtube, playing it only radio mode
    
    1. !로또 | !lotto
    - 이번주 예상 1등 로또번호를 알려줍니다.
    * Tell expected 1st Win Korean Lottery number in Channel

'''