import datetime as dt, heapq as pq, os, asyncio

import pandas as pd, numpy as np, requests
from discord.ext import commands

class bot_lottery(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__lotto_url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"
        self.__latest = None

    def __chk_latest(self, latest_round : int) -> bool:
        self.__latest = requests.get(self.__lotto_url.format(latest_round)).json()
        return self.__latest['returnValue'] == 'success'

    def __predict(self, time_seed : int):
        msgs = []
        max_n = np.int64(10_0000_0000)
        np.random.seed(time_seed)
        rand_num = np.random.binomial(max_n, 1 / 8_145_060, size=(5, 45))
        for arr in rand_num:
            win_q, msg = [], ['>']
            pq.heapify(win_q)
            for i, cnt in enumerate(arr, 1):
                pq.heappush(win_q, (-cnt, i))
            while len(msg) <= 6:
                msg.append(pq.heappop(win_q)[1])
            msgs.append(np.array(map(str, sorted(msg)), dtype=np.str))
        return np.array(msgs)

    @commands.command()
    async def lotto(self, ctx):
        npy_name, csv_name = 'last_predict.npy', 'last_data.csv'
        now_date = int(dt.datetime.now().timestamp())
        if os.path.exists(npy_name) and os.path.exists(csv_name):
            last_predict = np.load(npy_name)
            last_result = pd.read_csv(csv_name)
            last_round = last_result['drwNo'][0]
            last_date = int(dt.datetime.fromisoformat(last_result['drwNoDate'][0]).timestamp())
            if self.__chk_latest(last_round + 1):
                predict_correct_result = []
                await ctx.send(
                    "새로운 당첨 번호가 나왔습니다.\n\n{} : {}회차 추첨 번호는 \n> **{: >2}   {: >2}   {: >2}   {: >2}   {: >2}   {: >2}   bonus : {: >2}**\n"\
                    .format(self.__latest['drwNoDate'], self.__latest['drwNo'],
                            self.__latest['drwtNo1'], self.__latest['drwtNo2'], self.__latest['drwtNo3'],
                            self.__latest['drwtNo4'], self.__latest['drwtNo5'], self.__latest['drwtNo6'],
                            self.__latest['bnusNo']))
                await ctx.send("과연... 얼마나 맞췄을지...")
                await asyncio.sleep(5)
                latest_result = set(list(self.__latest.values())[2:])
                for game in last_predict:
                    chk, correct = ['>'], 0
                    for num in game:
                        if num in latest_result:
                            chk.append('__**{: >2}**__'.format(num))
                            correct += 1
                        else:
                            chk.append(num)
                    chk.append('ratio : {:.2f}%'.format(100.0 * (correct/len(game))))
                    predict_correct_result.append('   '.join(chk))
                await ctx.send('\n'.join(predict_correct_result))
                await ctx.send('다음 {}회차 당첨번호를 새로 예측합니다.'.format(int(self.__latest['drwNo']) + 1))
                predict_new_result = self.__predict(now_date + last_date)
                new = { k : [self.__latest[k]] for k in self.__latest }
                np.save(npy_name, predict_new_result) # update npy
                pd.DataFrame(new, columns=list(new.keys())).to_csv(csv_name, index = False) # update csv
                return await ctx.send('\n'.join(['   '.join(result) for result in predict_new_result]))
            else:
                await ctx.send("새로운 당첨 번호가 나오지 않았습니다.\n회차 갱신되지 않았으므로 이전에 예측한 번호를 보여드립니다.")
                return await ctx.send('\n'.join(['   '.join(result) for result in last_predict]))
        else:
            await ctx.send("처음으로 추첨합니다.")
            first_date = int(dt.datetime.fromisoformat('2002-12-07').timestamp())
            latest_round : int = (now_date - first_date) // (3600 * 24 * 7) + 1
            if self.__chk_latest(latest_round):
                await ctx.send('다음 {}회차 당첨번호를 새로 예측합니다.'.format(int(self.__latest['drwNo']) + 1))
                predict_new_result = self.__predict(now_date)
                new = { k : [self.__latest[k]] for k in self.__latest }
                np.save(npy_name, predict_new_result)  # update npy
                pd.DataFrame(new, columns=list(new.keys())).to_csv(csv_name, index=False)  # update csv
                return await ctx.send('\n'.join(['   '.join(result) for result in predict_new_result]))
            else:
                return await ctx.send('최근 회차 데이터를 불러오지 못했습니다.')

    @commands.command(name="로또")
    async def kor_play(self, ctx):
        return await self.lotto.invoke(ctx)
# Test code
if __name__ == '__main__':
    import app
    exp = bot_lottery(app.bot)
    exp.get_latest(dt.datetime.now().timestamp())