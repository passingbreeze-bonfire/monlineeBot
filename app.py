from flask import *
from multiprocessing import *
import discord, asyncio, json, io, time

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
        print(strbuf.getvalue())
    return token

app = Flask(__name__)
client = discord.Client()
isBot = "봇 대기중"
botToken = getToken("config.json")  # string

@client.event
async def on_ready():
    print("{0.user} 로그인 성공!".format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("ㄹㅇㅋㅋ"):
        await message.channel.send("ㄹㅇㅋㅋ만 치셈")

botTh = Process(target=client.run, args=(botToken,))

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

    1. !랜덤 요소1, 요소2, 요소3... | !random ele1, ele2, ele3...
    - 임의로 하나를 선택해줍니다.
    * Choose one among what you enter elements
'''