# File name: serve_with_fastapi.py
from cgitb import reset
import ray
from ray import serve
from fastapi import FastAPI
from open_spiel.python.algorithms import cfr
from open_spiel.python.algorithms import exploitability
import pyspiel
import open_spiel.python.games.ma_autobattler_poker
import open_spiel.python.games.ma_autobattler_engine

import pickle
import random
from dotenv import dotenv_values

config = dotenv_values(".env") 
app = FastAPI()

ray.init(address="auto", namespace="serve")
serve.start(detached=True)


@serve.deployment
@serve.ingress(app)
class GameEngineServer:
    def __init__(self, rules: int = 1):
        game = open_spiel.python.games.ma_autobattler_poker.MaAutobattlerGame({"rules":rules})
        
        self.summarize = "123"
        base_pickle_path = config["ROOTPATH"]
        template_name = config["TEMPLATENAME"]
        file_name = base_pickle_path+"/"+template_name.format(rules)
        with open(file_name, 'rb') as fp:
            solver = pickle.load(fp)
        self.solver = solver
        self.max_chance_outcomes = game.max_chance_outcomes()  
        self.game = game              

    @app.get("/battle")
    def get_result(self, hands:str):
        two_hands = hands.split("|")
        left_hand = [int(x) for x in two_hands[0].split(",")]
        right_hand = [int(x) for x in two_hands[1].split(",")]
        ge = open_spiel.python.games.ma_autobattler_engine.GameEngine(left_hand,right_hand,self.game.stats)
        res = ge.main_loop()
        return res

    @app.get("/battleind")
    def get_result_from(self, hind:int):
        hands = self.game.get_hands(hind)
        left_hand = hands["left"]
        right_hand = hands["right"]
        ge = open_spiel.python.games.ma_autobattler_engine.GameEngine(left_hand,right_hand,self.game.stats)
        res = ge.main_loop()
        return res

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

#a = GameEngineServer()
GameEngineServer.deploy()