# ==================================== Outer Space ==========================================
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio, random, os
import yt_handle, bot_lotto

load_dotenv(verbose=True)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix = commands.when_mentioned_or("!"), intents=intents)
# ====================================== Bot part ===========================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("😱 없는 명령어입니다. 😱")
    # if isinstance(error, commands.CommandInvokeError):
    #     await ctx.send("명령을 실행하던 중에 오류가 발생했습니다. 😭")
@bot.event
async def on_ready():
    print("bot ID : {} => Log in Successfully!".format(bot.user))

@bot.event
async def on_disconnect():
    if bot.is_closed():
        bot.clear()
        await asyncio.sleep(10)
        await bot.start(os.getenv('BOT_TOKEN'))

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    if message.content.startswith("ㄹㅇㅋㅋ"):
        channel = message.channel
        def check(m):
            return m.content == "ㄹㅇㅋㅋ" and m.channel == channel
        msg = await bot.wait_for('message', check=check)
        await channel.send("{.content}만 치셈 ㅋㅋ".format(msg))
# bot event와 command를 같이 쓰기위해 필수로 넣어야

@bot.command(name = "roll")
async def roll(ctx, *args):
    strlist = list(args)
    if not strlist:
        await ctx.send("돌릴게 없는데요?")
        return
    await ctx.send("🎊 {} 🎉".format(strlist[random.randint(0, len(strlist)-1)]))

@bot.command(name = "룰렛")
async def korroll(ctx):
    await roll.invoke(ctx)

# ================================================================================================
if __name__ == '__main__':
    bot.add_cog(yt_handle.ytMusic(bot))
    bot.add_cog(bot_lotto.bot_lottery(bot))
    bot.run(os.getenv('BOT_TOKEN'))