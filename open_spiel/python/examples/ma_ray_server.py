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
import json
import numpy as np
import pickle
import random
from dotenv import dotenv_values
from fastapi import Response
import itertools
from fastapi.middleware.cors import CORSMiddleware
origins = ["*"]

config = dotenv_values(".env") 
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ray.init(address="auto", namespace="serve")
serve.start(detached=True, http_options= {"host":"0.0.0.0"})


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

@serve.deployment
@serve.ingress(app)
class GameEngineServer:
    def __init__(self, rules: int = 2134):
        game = open_spiel.python.games.ma_autobattler_poker.MaAutobattlerGame({"rules":rules})
        
        self.summarize = "123"
        base_pickle_path = config["ROOTPATH"]
        template_name = config["TEMPLATENAME"]
        file_name = base_pickle_path+"/"+template_name.format(rules)+".done"
        with open(file_name, 'rb') as fp:
            solver = pickle.load(fp)
        self.solver = solver
        self.max_chance_outcomes = game.max_chance_outcomes()  
        self.game = game
        self.original_policy = solver.average_policy()   
        aaa = 444           

    @app.get("/battle")
    def get_result(self, hands:str):
        two_hands = hands.split("|")
        left_hand = [int(x) for x in two_hands[0].split(",")]
        right_hand = [int(x) for x in two_hands[1].split(",")]
        ge = open_spiel.python.games.ma_autobattler_engine.GameEngine(left_hand,right_hand,self.game.stats)
        res_doc = ge.main_loop()
        ret_win = ge.return_winner()
        res = {"winner":ret_win,"logs": res_doc}
        return res

    # @app.get("/battleind")
    # def get_result_from(self, hind:int):
    #     hands = self.game.get_hands(hind)
    #     left_hand = hands["left"]
    #     right_hand = hands["right"]
    #     ge = open_spiel.python.games.ma_autobattler_engine.GameEngine(left_hand,right_hand,self.game.stats)
    #     res_doc = ge.main_loop()
    #     ret_win = ge.return_winner()
    #     res = {"winner":ret_win,"logs": res_doc}
    #     return res

    @app.get("/hands")
    def get_hands(self):
        hnd = random.randint(0,self.max_chance_outcomes)
        res1 = self.game.get_hands(hnd) 
        res1["num"] = hnd
        all_matchers = list(itertools.product(range(3),repeat = 2))
        winners = {}
        winner_stat0 = [0,0,0]
        winner_stat1 = [0,0,0]

        for match in all_matchers:
            ress= []
            for chance in range(4):
                lh = res1["left"].copy()
                lres =  match[0]
                del lh[match[0]]
                rh = res1["right"].copy() 
                rres = match[1]
                del rh[match[1]]

                if chance == 0:
                    pass
                elif chance == 1:
                    lh = lh[::-1]
                elif chance == 2:
                    rh = rh[::-1]
                elif chance == 3:
                    lh = lh[::-1]
                    rh = rh[::-1]

                ge = open_spiel.python.games.ma_autobattler_engine.GameEngine(lh,rh,self.game.stats)
                ge.main_loop()
                ret_win = ge.return_winner()
                winner_stat0[lres] += -1*ret_win
                winner_stat1[rres] += ret_win
                
                ress.append(ret_win)
            winners[str(match)] = ress            
        res1["winners"] = winners

        lh = res1["left"].copy()         
        rh = res1["right"].copy()        

        for p in range(2):
            hand = lh
            if p == 1:
                hand = rh
            key = "p{} hand:{} hand:-1".format(p,tuple(hand))

            arr = self.original_policy._infostates.get(key)
            res1["strat"+str(p)] = arr[1].tolist()
            res1["regret"+str(p)] = arr[0].tolist()
        res1["winner_stat0"] = winner_stat0
        res1["winner_stat1"] = winner_stat1   

        
        return res1

    @app.get("/rules")
    def get_rules(self):
        rules = list(filter(None,self.game.rules_to_str().split("||"))) 
        dic = {}
        cou = -1
        
        for rul in rules:
            for suit in ["♠","♦"]:
                cou+=1
                valab = rul.split(":")[1].split(" ")
                dic[cou] = "{}{} {}".format(valab[0],suit,valab[1])
        
        return dic

    @app.get("/max10")
    def get_summary_max10(self, txt: str):
        summary_list = self.summarize
        summary = summary_list
        return summary

#a = GameEngineServer()
#a.get_result("11,8|10,6")
GameEngineServer.deploy()