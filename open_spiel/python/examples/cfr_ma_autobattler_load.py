# Copyright 2019 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example use of the CFR algorithm on Kuhn Poker."""

from __future__ import absolute_import
from __future__ import division 
from __future__ import print_function

from absl import app
from absl import flags
from torch import rand

from open_spiel.python.algorithms import cfr
from open_spiel.python.algorithms import exploitability
import pyspiel
import open_spiel.python.games.ma_autobattler_poker
import numpy as np
import pickle
import random
import mlflow
import datetime
import os,glob
import pandas as pd
import logging
from tqdm import tqdm


logging.basicConfig(filename='example.log',level=logging.INFO)
# create logger
logger = logging.getLogger("somelogger")
# set log level for all handlers to debug
logger.setLevel(logging.DEBUG)
logger.propagate = False
# create console handler and set level to debug
# best for development or debugging
# consoleHandler = logging.StreamHandler()
# consoleHandler.setLevel(logging.INFO)

# # create formatter
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# # add formatter to ch
# consoleHandler.setFormatter(formatter)

# add ch to logger
#logger.addHandler(consoleHandler)


def read_resolv():
   res = ""
   with open("/etc/resolv.conf", 'r') as fp:
     lines = fp.readlines()
     for line in lines:
       if line.startswith("nameserver"):
         res = line.split(" ")[1].strip()
         break

   return res



def parse_filename(filename):
  res = {"ok":False} 
  parts = filename.split("_")
  if len(parts) == 8:
    res["ok"] =True
    res["rules"] = int(parts[-2])
    ends = parts[-1].split(".")
    res["iter"] = int(ends[0])
  return res  

def main(_):
  uri = "http://{}:5000".format(read_resolv()) 
  print(uri)
  remote_server_uri = uri # set to your server URI
  mlflow.set_tracking_uri(remote_server_uri)
  mlflow.set_experiment("AutoBattler")

  experiments_path = "/home/kirill/Experiments/"
  base_pickle_path = "/home/kirill/myspiel"
  for file in glob.glob(base_pickle_path+"/"+"external_sampling_mccfr_solver_autobattler_s_*.pickle"):
    parsed_name = parse_filename(file)
    if not parsed_name["ok"] or parsed_name["rules"] not in open_spiel.python.games.ma_autobattler_poker.all_stats or parsed_name["iter"]<10000:
      continue
    print(file)
    game = open_spiel.python.games.ma_autobattler_poker.MaAutobattlerGame({"rules":parsed_name["rules"]})
    max_chance_outcomes = game.max_chance_outcomes()
    total_cards = game.total_cards
    card_counter_discarded = np.zeros(total_cards).tolist()
    card_counter_kept = np.zeros(total_cards).tolist()

    one_useless = 0
    eps_useless = 0.001
    all_equal = 0
    all_eq_val = 0.333
    no_choice = False
    play_random = False
    play_worst  = False
    solver = None
    file_name = file
    with open(file_name, 'rb') as fp:
          solver = pickle.load(fp)
    original_policy = solver.average_policy()
    a1 = 0
    a2 = 0
    a0 = 0
    total_game_number = 500
    log_meta = True
    step = 0.05  

    basename = "mylogdir"
    suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")  
    dirname = experiments_path + "_".join([basename, suffix])
    os.makedirs(dirname)

    logger.handlers = []
    original_meta = []

    for j in range(1):
      logger.handlers = []
      log_path = dirname+"/experiment_{}.txt".format(j)
      fileHandler = logging.FileHandler(log_path)
      fileHandler.setLevel(logging.DEBUG)
      logger.addHandler(fileHandler)
      logger.debug("!23s")
      df = pd.DataFrame()

      alpha = j * step
      #a = original_policy.copy_with_noise(alpha)
      a = original_policy
      with mlflow.start_run():
        mlflow.log_param("total_game_number", total_game_number)
        mlflow.log_param("alpha", alpha)
        mlflow.log_param("log_path", log_path)
        mlflow.log_param("random", play_random)
        mlflow.log_param("rules", game.rules_to_str())
        logger.debug("game rules:{}".format(game.rules_to_str()))

        mlflow.log_param("filename", file_name)
        print("Max chance outcome:{}", max_chance_outcomes)
        for i in tqdm(range(max_chance_outcomes)):
          state = game.new_initial_state()
          while not state.is_terminal():
            #if state.current_player() == pyspiel.PlayerId.CHANCE:
            if state.stage == 0:
              state._apply_action(i)
            elif state.current_player() == pyspiel.PlayerId.CHANCE:
              outomes = state.chance_outcomes()
              l = random.choice(outomes)
              state._apply_action(l)

            else :
              info_state_str = state.information_state_string(state.current_player())
              #state_policy = a.policy_for_key(info_state_str)
              state_policy = a.action_probabilities(state)
              
              logger.debug(state_policy)

              p = np.argmax(state_policy)
              p_minus = np.argmin(state_policy)
              if log_meta:
                #meta_str =  str(state_policy)
              
                #mlflow.log_metric("meta_str",state_policy )
                log_meta = False  
              #print(state._action_to_string(state.current_player(),p))
              #print(state)
              if state.current_player() == 1 or state.current_player() == 0:
                # a1 = int(input())
                # state._apply_action(a1)

                min_p = min(state_policy)
                max_p = max(state_policy)
                if min_p < eps_useless:
                  one_useless+=1
                
                if max_p > 1.0-eps_useless:
                  no_choice+=1
                
                if abs(state_policy[0] - all_eq_val) < eps_useless:
                  all_equal+=1

                card = state.action_to_card(p,state.current_player())
                card_counter_discarded[card]+=1
                card_policy = state.policy_to_cards(state_policy,state.current_player())
                
                # if card_policy[0] >0 and card_policy[4]>0:
                #   print(card_policy)
                tf = pd.DataFrame([card_policy])
                df = df.append(tf)
                for ind in range(3):
                  if ind!=p:
                    card = state.action_to_card(ind,state.current_player())
                    card_counter_kept[card]+=1
                    if  card ==0 or  card == 4:
                      pass
                      #print(state)
                      #print(p)
                #af = len(el<eps_useless for el in state_policy)
                
                if not play_random or state.current_player() == 0:
                  state._apply_action(p)

                elif play_worst:
                  state._apply_action(p_minus)
                  
                else:
                  la = state._legal_actions( state.current_player() )
                  ra = random.choice(la)
                  state._apply_action(ra)

              else:
                state._apply_action(p)
            #print(state)
          game_res = state.game_res[0]
          logger.debug("Game result:{}".format(game_res))

          if game_res == 1:
            a1+= 1
          elif game_res == -1:
            a2+= 1
          elif game_res == 0:
            a0 +=1
          else:
            raise("value is {}".format(game_res)) 
        #print(a1,a2)
        mlflow.log_metric("a1", a1)
        mlflow.log_metric("a2", a2)
        mlflow.log_metric("a0", a0)
        mlflow.log_metric("one_useless", one_useless)
        mlflow.log_metric("all_equal", all_equal)
        mlflow.log_metric("no_choice", no_choice)


        #print(df)
        corr = df.corr()
        logger.debug(corr)
        for ind,card in enumerate(card_counter_discarded):
          mlflow.log_metric("card_discraded"+str(ind), card)
        for ind,card in enumerate(card_counter_kept):
          mlflow.log_metric("card_kept"+str(ind), card) 

      

if __name__ == "__main__":
  # print(123)
  # print(read_resolv())
  app.run(main)

