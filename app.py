from flask import *
from multiprocessing import *
from discord.ext import commands
import botTool, asyncio, time, random

app = Flask(__name__)
bot = commands.Bot(command_prefix='!')
isBot = "봇 대기중"
botToken = botTool.getToken("config.json")  # string

@bot.event
async def on_ready():
    print("{} => 로그인 성공!".format(bot.user))

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
async def roll(ctx, *args):
    strlist = list(args)
    await ctx.send("🎊 {} 🎉".format(strlist[random.randint(0, len(strlist)-1)]))

botTh = Process(target=bot.run, args=(botToken,))
if botToken is not None:
    botTh.start()
    isBot = "봇이 실행중입니다."
else:
    isBot = "봇이 실행되고 있지 않습니다."

@app.route('/')
def exe_bot():
    return "{0} : 서버가 구동중입니다. // {1}".format(time.strftime("%c", time.localtime(time.time())),isBot)

if __name__ == '__main__':
    flaskTh = Process(target=app.run)
    flaskTh.start()
    botTh.join()
    flaskTh.join()


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