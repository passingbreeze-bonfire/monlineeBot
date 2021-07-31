import os, datetime as dt

import pandas as pd, numpy as np, discord
from discord.ext import commands

class bot_lottery(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.__latest = pd.read_csv('latest_data.csv')
        self.__tot_cnt = np.array(self.__latest.iloc[0][2:])

    def get_latest(self):
        due_8 = 691_200.0 # 3600 * 24 * 8
        new_round = 0
        last_round = self.__latest['round'][0]
        last_date = dt.datetime.fromisoformat(self.__latest['date'][0]).timestamp()
        if last_round < new_round and abs(last_date - dt.datetime.now().timestamp()) > due_8:
            renew_date = dt.datetime.fromtimestamp(last_date + 604_800.0) # 3600 * 24 * 7
            self.__latest['date'][0] = renew_date
            self.__latest['round'][0] = new_round

        pass

    def get_avg_stddev(self):
        LOT_NUM = 45
        pos_arr = np.array([1 / LOT_NUM] * LOT_NUM, dtype=np.float64)


if __name__ == '__main__':
    import app
    exp = bot_lottery(app.bot)
    exp.get_latest()