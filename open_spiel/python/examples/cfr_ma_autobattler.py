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

from open_spiel.python.algorithms import cfr
from open_spiel.python.algorithms import exploitability
import pyspiel
import open_spiel.python.games.ma_autobattler_poker

import numpy as np
import pickle
import random

FLAGS = flags.FLAGS

flags.DEFINE_integer("iterations",5, "Number of iterations")
flags.DEFINE_string("game", "kuhn_poker", "Name of the game")
flags.DEFINE_integer("players", 2, "Number of players")
flags.DEFINE_integer("print_freq", 1, "How often to print the exploitability")
import logging

# create logger
logger = logging.getLogger("somelogger")
# set log level for all handlers to debug
logger.setLevel(logging.ERROR)

# create console handler and set level to debug
# best for development or debugging
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
consoleHandler.setFormatter(formatter)

# add ch to logger
#logger.addHandler(consoleHandler)

def main(_):
  game = open_spiel.python.games.ma_autobattler_poker.MaAutobattlerGame({"rules":1})
  cfr_solver = cfr.CFRPlusSolver(game)
  
  with open('autobattler_solver_pre_16_1.pkl', 'wb') as fp:
        pickle.dump(cfr_solver, fp)
  for i in range(FLAGS.iterations):
    print(i)
    cfr_solver.evaluate_and_update_policy()
    if i % FLAGS.print_freq == 0:
      conv = exploitability.nash_conv(game, cfr_solver.average_policy())
      print("Iteration {} exploitability {}".format(i, conv))
  
  a = cfr_solver.average_policy()
  with open('autobattler_16_1.pkl', 'wb') as fp:
        pickle.dump(a, fp)

  with open('autobattler_solver_16_1.pkl', 'wb') as fp:
        pickle.dump(cfr_solver, fp)

  a1 = 0
  a2 = 0  
  logger.setLevel(logging.DEBUG)

  for i in range(10):
    state = game.new_initial_state()
    while not state.is_terminal():
      if state.current_player() == pyspiel.PlayerId.CHANCE:
        act = state.chance_outcomes()
        actions = list(map(lambda x:x[0],act))
        action = random.choice(actions)
        print(state._action_to_string(state.current_player(),action))
        state._apply_action(action)

      else :
        info_state_str = state.information_state_string(state.current_player())
        state_policy = a.policy_for_key(info_state_str)
        p = np.argmax(state_policy)
        print(state._action_to_string(state.current_player(),p))
        print(state)
        if state.current_player() == 1:
          # a1 = int(input())
          # state._apply_action(a1)
          state._apply_action(p)

        else:
          state._apply_action(p)
      print(state)
      a1+= state.game_res[0]
      a2+= state.game_res[1]
  print(a1,a2)

  


if __name__ == "__main__":
  app.run(main)
