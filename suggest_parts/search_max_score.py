import pandas as pd
from random import (randint, random, shuffle)
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import pickle
from tqdm import tqdm
import warnings
warnings.simplefilter('ignore')
sns.set()

class SearchMaxScore:
    def __init__(self, budget):
        self.ROOT_DIR = "/home/szbhitoshikiizaya/lab/flask_project/suggest_parts/"
        self.init_dataset()
        self.init_model()
        self.budget = budget
        self.GENE_NUM = 5000
        self.family = []
        self.max_score_list = []

    def search(self):
        self.add_random_combi_to_family()
        for g in tqdm(range(self.GENE_NUM)):
            if len(self.family) <= 1:
                self.add_random_combi_to_family()
            idx_p1, idx_p2 = self.select_random_pair_from_family()
            children = self.cross_over(self.family[idx_p1], self.family[idx_p2])
            children = self.mulation(children)
            self.select_elite(idx_p1, idx_p2, children)
            self.save_max_score()

    def plot_graph(self):
        x = [i for i in range(len(self.max_score_list))]
        plt.plot(x, [s[-1] for s in self.max_score_list])
        plt.savefig(self.ROOT_DIR + "../data/max_score.png")

    def print_max_combi(self, return_score=False, return_values=False):
        max_combi = sorted(self.max_score_list, key=lambda x:x[-1])[-1]
        combi = max_combi[0]
        price = max_combi[1]
        score = max_combi[2]
        name = [
            ["cpu", "gpu", "ram", "disk"],
            ["cpu_url", "gpu_url", "ram_url", "disk_url"],
            ["cpu_price", "gpu_price", "ram_price", "disk_price"]
        ]
        values = {}
        for i, df in enumerate([self.cpu_df, self.gpu_df, self.ram_df, self.disk_df]):
            values[name[0][i]] = df.iloc[combi[i]]["name"]
            values[name[1][i]] = df.iloc[combi[i]]["url"]
            values[name[2][i]] = df.iloc[combi[i]]["PRICE"]
        values["PRICE"] = price
        values["SCORE"] = score
        if return_score:
            return score
        if return_values:
            return values
        if score == 0:
            print("Not found ...")
            return 
        spec = pd.DataFrame(pd.concat([
            self.cpu_calc_df.iloc[combi[0], :-1],
            self.gpu_calc_df.iloc[combi[1], :-1],
            self.ram_calc_df.iloc[combi[2], :-1],
            self.disk_calc_df.iloc[combi[3], 1:-1]
        ])).T
        print(values)
        print("PRICE\t: ", price)
        print("SCORE\t: ", score)
        print(spec)

    def save_max_score(self):
        sl = []
        for f in self.family:
            score = self.eval(f)
            sl.append(score)
        score = max(sl)
        max_combi = self.family[sl.index(score)]
        cpu_i, gpu_i, ram_i, disk_i = max_combi
        price = sum([
            self.cpu_df.iloc[cpu_i]["PRICE"], 
            self.gpu_df.iloc[gpu_i]["PRICE"],
            self.ram_df.iloc[ram_i]["PRICE"],
            self.disk_df.iloc[disk_i]["PRICE"]
        ])
        self.max_score_list.append((max_combi, price, score))

    def select_elite(self, idx_p1, idx_p2, children):
        score_p1, score_p2 = (self.eval(self.family[idx_p1]), self.eval(self.family[idx_p2]))
        score_c1, score_c2 = (self.eval(children[0]), self.eval(children[1]))
        idx_lower_p = idx_p1 if score_p1 < score_p2 else idx_p2
        higher_p_score = score_p1 if score_p1 >= score_p2 else score_p2
        higher_c = children[0] if score_c1 >= score_c2 else children[1]
        if (score_c1 > score_p1 and score_c1 > score_p2
                and score_c2 > score_p1 and score_c2 > score_p2):
            self.family.pop(idx_lower_p)
            self.family.extend(children)
        elif (score_c1 < score_p1 and score_c1 < score_p2
                and score_c2 < score_p1 and score_c2 < score_p2):
            self.family.pop(idx_lower_p)
        elif higher_p_score > score_c1 and higher_p_score > score_c2:
            self.family.pop(idx_lower_p)
            self.family.append(higher_c)
        else:
            pop_list = sorted([idx_p1, idx_p2], reverse=True)
            for p in pop_list:
                self.family.pop(p)
            self.family.append(higher_c)
            self.add_random_combi_to_family()


    def mulation(self, children):
        idx_mulate_child = randint(0, len(children)-1)
        idx_mulate_parts = randint(0, 4-1)
        idx_new_parts = randint(0, len(self.df_list[idx_mulate_parts])-1)
        children[idx_mulate_child][idx_mulate_parts] = idx_new_parts
        return children

    def cross_over(self, parent_1, parent_2):
        children = []
        mask = [round(random()) for i in range(4)]
        for it in range(2):
            child = [parent_1[i] if mask[i] == it else parent_2[i] for i in range(4)]
            children.append(child)
        return children

    def select_random_pair_from_family(self):
        idx_1 = randint(0, len(self.family)-1)
        while True:
            idx_2 = randint(0, len(self.family)-1)
            if idx_1 != idx_2:
                break
        return (idx_1, idx_2)

    def add_random_combi_to_family(self):
        combi = []
        for df in self.df_list:
            select_index = randint(0, len(df)-1)
            combi.append(select_index)
        self.family.append(combi)

    def eval(self, combi):
        cpu_i, gpu_i, ram_i, disk_i = combi
        which_disk = self.disk_calc_df.iloc[disk_i, :]["hdd_ssd"]
        spec = pd.DataFrame(pd.concat([
            self.cpu_calc_df.iloc[cpu_i, :-1],
            self.gpu_calc_df.iloc[gpu_i, :-1],
            self.ram_calc_df.iloc[ram_i, :-1],
            self.disk_calc_df.iloc[disk_i, 1:-1]
        ])).T
        price = sum([
            self.cpu_calc_df.iloc[cpu_i]["PRICE"],
            self.gpu_calc_df.iloc[gpu_i]["PRICE"],
            self.ram_calc_df.iloc[ram_i]["PRICE"],
            self.disk_calc_df.iloc[disk_i]["PRICE"]
        ])
        return int(self.calc_score(spec, price, which_disk))

    def calc_score(self, spec_info, price, which_disk):
        if price > self.budget:
            return 0
        if which_disk == 0:
            score = self.reg_model_hdd.predict(spec_info)[0]
        else:
            score = self.reg_model_ssd.predict(spec_info)[0]
        return score


    def init_dataset(self):
        self.cpu_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/cpu_kakaku_grouped.csv", index_col=0)
        self.gpu_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/gpu_kakaku_grouped.csv", index_col=0)
        self.ram_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/ram_kakaku_grouped.csv", index_col=0)
        self.disk_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/disk_kakaku.csv", index_col=0)
        self.cpu_calc_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/cpu_kakaku_calc_grouped.csv", index_col=0)
        self.gpu_calc_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/gpu_kakaku_calc_grouped.csv", index_col=0)
        self.ram_calc_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/ram_kakaku_calc_grouped.csv", index_col=0)
        self.disk_calc_df = pd.read_csv(self.ROOT_DIR + "data/kakaku/disk_kakaku_calc.csv", index_col=0)
        self.df_list = [
            self.cpu_calc_df,
            self.gpu_calc_df,
            self.ram_calc_df,
            self.disk_calc_df
        ]

    def init_model(self):
        self.reg_model_hdd = pickle.load(open(self.ROOT_DIR + "data/model/regression_model_hdd.sav", "rb"))
        self.reg_model_ssd = pickle.load(open(self.ROOT_DIR + "data/model/regression_model_ssd.sav", "rb"))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        budget = int(sys.argv[-1]) * 10000
        sms = SearchMaxScore(budget)
        sms.search()
        sms.print_max_combi(return_score=False)
        sms.plot_graph()
    else:
        x = [i for i in range(2, 31)]
        x = [i*10000 for i in x]
        score_list = []
        diff = []
        for budget in x:
            print("budget : ", budget)
            sms = SearchMaxScore(budget)
            sms.search()
            score = sms.print_max_combi(return_score=True)
            score_list.append(score)
        plt.plot(x, score_list)
        plt.xlabel("budget")
        plt.ylabel("score")
        plt.show()
        for i in range(1, len(score_list)):
            d = score_list[i] - score_list[i-1]
            diff.append(d)
        x = [i for i in range(len(diff))]
        plt.plot(x, diff)
        plt.show()
