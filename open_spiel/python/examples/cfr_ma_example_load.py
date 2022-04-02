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




def main(_):
  game = open_spiel.python.games.ma_meta_poker.MaMetaPokerGame()
  a = None
  with open('data4_08.pkl', 'rb') as fp:
     a = pickle.load(fp)

  

  state = game.new_initial_state()
  while not state.is_terminal():
    info_state_str = state.information_state_string(state.current_player())
    state_policy = a.policy_for_key(info_state_str)
    p = np.argmax(state_policy)
    print(state._action_to_string(state.current_player(),p))
    print(state_policy)
    print(state)
    if state.current_player() == 1:
        # print(state._legal_actions(state.current_player()))
        # a1 = int(input())
        # state._apply_action(a1)
      state._apply_action(p)

    else:
      state._apply_action(p)
    print(state)


if __name__ == "__main__":
  app.run(main)
