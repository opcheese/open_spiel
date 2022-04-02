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

from open_spiel.python.algorithms import cfr_ma
from open_spiel.python.algorithms import exploitability
import pyspiel
import open_spiel.python.games.ma_meta_poker
import numpy as np
import pickle

FLAGS = flags.FLAGS

flags.DEFINE_integer("iterations",50, "Number of iterations")
flags.DEFINE_string("game", "kuhn_poker", "Name of the game")
flags.DEFINE_integer("players", 3, "Number of players")
flags.DEFINE_integer("print_freq", 10, "How often to print the exploitability")


def main(_):
  game = open_spiel.python.games.ma_meta_poker.MaMetaPokerGame()
  cfr_solver = cfr_ma.CFRSolver(game,strategy_player=2, penalty=0.7 )

  for i in range(FLAGS.iterations):
    print(i)
    cfr_solver.evaluate_and_update_policy()
    if i % FLAGS.print_freq == 0:
      conv = exploitability.nash_conv(game, cfr_solver.average_policy())
      print("Iteration {} exploitability {}".format(i, conv))
  
  a = cfr_solver.average_policy()
  with open('data4_07.pkl', 'wb') as fp:
        pickle.dump(a, fp)

  with open('solver_04_07.pkl', 'wb') as fp:
        pickle.dump(cfr_solver, fp)
  

  state = game.new_initial_state()
  while not state.is_terminal():
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


if __name__ == "__main__":
  app.run(main)
