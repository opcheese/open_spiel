# File name: serve_with_fastapi.py
from cgitb import reset
import ray
from ray import serve
from fastapi import FastAPI
from open_spiel.python.algorithms import cfr
from open_spiel.python.algorithms import exploitability
import pyspiel
import open_spiel.python.games.ma_autobattler_poker
import pickle
import random

app = FastAPI()

ray.init(address="auto", namespace="serve")
serve.start(detached=True)


@serve.deployment
@serve.ingress(app)
class Summarizer:
    def __init__(self):
        game = open_spiel.python.games.ma_autobattler_poker.MaAutobattlerGame({"rules":1})
        self.summarize = "123"
        base_pickle_path = "/home/wurk/w/spiel"
        file_name = base_pickle_path+"/"+"external_sampling_mccfr_solver_autobattler_7power_fixed_1_7000.pickle"
        with open(file_name, 'rb') as fp:
            solver = pickle.load(fp)
        self.solver = solver
        self.max_chance_outcomes = game.max_chance_outcomes()  
        self.game = game              

    @app.get("/")
    def get_summary(self, txt: str):
        summary_list = self.summarize
        summary = summary_list
        return summary

    @app.get("/hands")
    def get_summary_min10(self):
        hnd = random.randint(0,self.max_chance_outcomes)
        res1 = self.game.get_hands(hnd)
        res1["num"] = hnd      
        return str(res1)

    @app.get("/max10")
    def get_summary_max10(self, txt: str):
        summary_list = self.summarize
        summary = summary_list
        return summary

#a = Summarizer()
Summarizer.deploy()