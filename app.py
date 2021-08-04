# ==================================== Outer Space ==========================================
import discord
from discord.ext import commands
from dotenv import load_dotenv

import asyncio, json, random, os, datetime as dt
import yt_handle, bot_lotto

load_dotenv(verbose=True)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix = commands.when_mentioned_or("!"), intents=intents)
# ====================================== Bot part ===========================================

@bot.event
async def on_command_error(ctx, error):
    return await ctx.send("😱 없는 명령어입니다. 😱")\
        if isinstance(error, commands.CommandNotFound)\
        else print(f"{dt.datetime.now()} : {ctx.content}") # Bot Command Time Log

@bot.event
async def on_ready(ctx):
    print(f"{dt.datetime.now()} : {bot.user} => Log in Successfully!")
    return await ctx.send("Bot Online!")

@bot.event
async def on_disconnect():
    if bot.is_closed():
        bot.clear()
        await asyncio.sleep(10)
        return await bot.start(os.getenv('BOT_TOKEN'))

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    with open("bot_msg.json") as msg_json:
        msg_table = json.load(msg_json)
    check = lambda m: m.channel == channel and m.content in msg_table
    if message.author == bot.user:
        return
    channel = message.channel
    for trigger in msg_table.keys():
        if message.content.startswith(trigger):
            msg = await bot.wait_for('message', check=check)
            return await channel.send(f"{msg_table[msg]}")
    return await channel.send("등록된 말이 없습니다.")
# bot event와 command를 같이 쓰기위해 필수로 넣어야

@bot.command()
async def help(ctx):
    return await ctx.send('''```
    1. [ !틀어줘 | !play ] __유튜브 링크(youtube link)__
        - 유튜브 링크가 아니면 동작하지 않습니다
            * Only available youtube link
       
        - 유튜브에서 듣고싶은 음악 혹은 플레이리스트를 찾아서 틀어줍니다. 라디오 모드로 링크가 재생됩니다.
            * Find music or playlist what you wanna hear in Youtube, playing it only radio mode        

        1-1. [ !지금 | !nowplay ]
            - 봇이 재생중이라면 현재 재생중인 음악을 보여줍니다. 플레이리스트라면 플레이리스트까지 보여줍니다.
                * Show what bot plays now. If bot plays playlist, show all list. 

        1-2. [ !이전 | !prev ]
            - 재생중인 플레이리스트가 있다면 이전 재생했던 음악을 재생합니다.
                * Play previous one if your playlist is playing on. 
    
        1-3. [ !다음 | !next ]   
            - 재생중인 플레이리스트가 있다면 다음 곡을 재생합니다.
                * Play next one if playlist is playing on.
        
        1-4. [ !음량 | !volume ] __0 ~ 100 사이의 숫자__
            - 재생중인 음악의 볼륨을 조절합니다.
                * Control music volume.
        
        1-5. [ !잠깐 | !pause ] 
            - 재생중인 음악을 일시정지합니다.
                * Pause music if it is playing.    
        
        1-6. [ !다시 | !resume ] 
            - 일시정지중인 음악을 다시 재생합니다.
                * Resume playing music if it is paused.    
            
        1-7. [ !정지 | !stop ] 
            - 재생중인 음악 모두를 정지합니다.
                * Let bot stop all musics.
                
    2. [ !로또 | !lotto ]
        - 이번주 예상 1등 로또번호를 알려줍니다.
            * Bot expects 1st Win Korean Lottery number this week.

    3. [ !룰렛 | !roll ] __요소1, 요소2, 요소3...__
        - 임의로 하나를 선택해줍니다.
            * Choose one among what you input.
    
    4. 개발자 이메일 | Developer E-mail
        - jeongmin1237@gmail.com
    
    ```''')

@bot.command(name = "도움")
async def korhelp(ctx):
    return await help.invoke(ctx)

@bot.command(name = "roll")
async def roll(ctx, *args):
    strlist = list(args)
    return await ctx.send("돌릴게 없는데요?") if not strlist \
        else await ctx.send("🎊 {} 🎉".format(strlist[random.randint(0, len(strlist)-1)]))

@bot.command(name = "룰렛")
async def korroll(ctx):
    return await roll.invoke(ctx)

# ================================================================================================
if __name__ == '__main__':
    bot.add_cog(yt_handle.ytMusic(bot))
    bot.add_cog(bot_lotto.bot_lottery(bot))
    bot.run(os.getenv('BOT_TOKEN'))