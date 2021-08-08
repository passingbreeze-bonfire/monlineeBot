import datetime as dt, heapq as pq, os

import pandas as pd, numpy as np, requests
from discord.ext import commands

class bot_lottery(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__gen = False
        self.__latest = pd.read_csv('latest_data.csv')
        self.__seed = dt.datetime.fromisoformat(self.__latest['date'][0]).timestamp()

    def __get_latest(self, now_date):
        lotto_url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
        last_round = self.__latest['round'][0]
        last_date = self.__seed
        if abs(now_date - last_date) > 691_200: # 3600 * 24 * 8
            self.__gen = False
            get_latest = requests.get(lotto_url.format(last_round + 1))
            parsed_get = get_latest.json()
            if parsed_get['returnValue'] == "success":
                self.__seed = last_date + 604_800.0  # 3600 * 24 * 7
                self.__latest['date'] = parsed_get['drwNoDate']
                self.__latest['round'] = parsed_get['drwNo']
                self.__latest['1st'] = parsed_get['drwtNo1']
                self.__latest['2nd'] = parsed_get['drwtNo2']
                self.__latest['3rd'] = parsed_get['drwtNo3']
                self.__latest['4th'] = parsed_get['drwtNo4']
                self.__latest['5th'] = parsed_get['drwtNo5']
                self.__latest['6th'] = parsed_get['drwtNo6']
                self.__latest['bonus'] = parsed_get['bnusNo']
                self.__latest.to_csv('latest_data.csv', index=False)
                return True
        return False

    @commands.command()
    async def lotto(self, ctx):
        msgs = []
        now_date = dt.datetime.now().timestamp()
        if self.__get_latest(now_date):
            await ctx.send("새로운 당첨 번호가 나왔습니다. 결과 반영중...")
        else:
            await ctx.send("새로운 당첨 번호가 나오지 않았습니다.")
        await ctx.send("{} : {}회차 추첨 번호는 \n> **{: >2}   {: >2}   {: >2}   {: >2}   {: >2}   {: >2}**\n"\
                       .format(self.__latest['date'], self.__latest['round'][0],
                               self.__latest['1st'], self.__latest['2nd'], self.__latest['3rd'],
                               self.__latest['4th'], self.__latest['5th'], self.__latest['6th']))
        await ctx.send(f"{self.__latest['round'][0] + 1}회차 추첨 예상 번호를 뽑습니다...")
        if not (os.path.exists('last_result.npy') and self.__gen):
            await ctx.send("회차 갱신으로 새로 뽑습니다")
            max_n = np.int64(10_0000_0000)
            np.random.seed(int(self.__seed))
            rand_num = np.random.binomial(max_n, 1/8_145_060, size = (5, 45))
            for arr in rand_num:
                win_q, msg = [], []
                pq.heapify(win_q)
                for i, cnt in enumerate(arr, 1):
                    pq.heappush(win_q, (-cnt, i))
                while len(msg) < 6:
                    msg.append(str(pq.heappop(win_q)[1]))
                msgs.append('\t> **{: >2}   {: >2}   {: >2}   {: >2}   {: >2}   {: >2}**' \
                            .format(msg[0], msg[1], msg[2], msg[3], msg[4], msg[5]))
            np.save('last_result.npy', np.array(msgs, dtype=np.str))
            self.__gen = True
        else:
            await ctx.send("회차 갱신되지 않았으므로 갱신된 번호를 보여드립니다.")
            msgs = np.load('last_result.npy')
        return await ctx.send('\n'.join(msgs))

    @commands.command(name="로또")
    async def kor_play(self, ctx):
        return await self.lotto.invoke(ctx)
# Test code
if __name__ == '__main__':
    import app
    exp = bot_lottery(app.bot)
    exp.get_latest(dt.datetime.now().timestamp())