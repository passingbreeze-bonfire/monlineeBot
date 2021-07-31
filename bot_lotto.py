import json, datetime as dt, heapq as pq, os

import pandas as pd, numpy as np, discord, requests
from discord.ext import commands

class bot_lottery(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__latest = pd.read_csv('latest_data.csv')
        self.__seed = dt.datetime.fromisoformat(self.__latest['date'][0]).timestamp()

    def __get_latest(self, now_date):
        lotto_url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
        last_round = self.__latest['round'][0]
        last_date = self.__seed
        if abs(now_date - last_date) > 691_200:
            get_latest = requests.get(lotto_url.format(last_round + 1))
            parsed_get = get_latest.json()
            if parsed_get['returnValue'] == "success":
                self.__seed = dt.datetime.fromtimestamp(last_date + 604_800.0)  # 3600 * 24 * 7
                self.__latest['date'][0] = parsed_get['drwNoDate']
                self.__latest['round'][0] = parsed_get['drwNo']
                return True
        return False

        # if last_round < new_round and abs(last_date - dt.datetime.now().timestamp()) > due_8:
    @commands.command()
    async def lotto(self, ctx):
        win_q = []
        msg, msgs = [], []
        now_date = dt.datetime.now().timestamp()
        pq.heapify(win_q)
        if self.__get_latest(now_date):
            await ctx.send("새로운 당첨 번호가 나왔습니다. 결과 반영중...")
        else:
            await ctx.send("새로운 당첨 번호가 나오지 않았습니다.")
            await ctx.send(f"{self.__latest['round'][0]}회차 당첨 번호까지 봤을 때...")
            if not os.path.exists('last_result.npy'):
                max_n = np.int64(10_0000_0000)
                np.random.seed(int(self.__seed))
                rand_num = np.random.binomial(max_n, 1/8_145_060, size = (5, 45))
                for arr in rand_num:
                    for i, cnt in enumerate(arr, 1):
                        pq.heappush(win_q, (-cnt, i))
                    while win_q:
                        if len(msg) == 6:
                            msg = "\t> **{}**".format("\t".join(msg))
                            msgs.append(msg)
                            msg = []
                            break
                        msg.append(str(pq.heappop(win_q)[1]))
                np.save('last_result.npy', np.array(msgs, dtype=np.str))
            else:
                msgs = np.load('last_resslut.npy')
            await ctx.send('\n'.join(msgs))


if __name__ == '__main__':
    import app
    exp = bot_lottery(app.bot)
    exp.get_latest()