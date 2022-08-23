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

# Lint as python3
"""Kuhn Poker implemented in Python.

This is a simple demonstration of implementing a game in Python, featuring
chance and imperfect information.

Python games are significantly slower than C++, but it may still be suitable
for prototyping or for small games.

It is possible to run C++ algorithms on Python implemented games, This is likely
to have good performance if the algorithm simply extracts a game tree and then
works with that. It is likely to be poor if the algorithm relies on processing
and updating states as it goes, e.g. MCTS.
"""

import enum

import numpy as np
import itertools
import math
import random
import pyspiel
import logging
import open_spiel.python.games.ma_autobattler_engine as engine
import json

logger = logging.getLogger("somelogger")

Cache = {}
### initiate deals
TOTAL_CARDS = 12
HAND_SIZE = 3
SUIT_NUMBER=2

CARDS_PER_SUIT = int(TOTAL_CARDS/SUIT_NUMBER)
cards = list(np.arange(TOTAL_CARDS))
c85 = math.comb(TOTAL_CARDS,HAND_SIZE)
c53 = math.comb(TOTAL_CARDS - HAND_SIZE,HAND_SIZE)
total_combinations = c85*c53
first_hands = itertools.combinations(cards,3)
list_first_hand = list(first_hands)

#print(list(itertools.permutations(range(3),2)))

def get_second_hands(one_first_hand):
    cards_left = [item for item in cards if item not in one_first_hand]
    second_hands = itertools.combinations(cards_left,3)
    return second_hands

all_deals = []
for i in range(c85):
    f1 = list_first_hand[i]
    second_hands = list(get_second_hands(f1))
    for j in range(c53):
        s1 = second_hands[j]
        tupl = (f1,s1)
        all_deals.append(tupl)
        #print(tupl)

all_deals_ind = np.arange(len(all_deals)) 
card_types = list(np.arange(TOTAL_CARDS/SUIT_NUMBER+1, dtype=int))
powered_cards_list = list(itertools.permutations(card_types,7))
def genStats(ability_order):
    one_stats = {}
    for i in range(int(TOTAL_CARDS/SUIT_NUMBER)):
        for j in range(SUIT_NUMBER):
            one_stats[i*SUIT_NUMBER +j ] = [i%CARDS_PER_SUIT+1,ability_order[i],j]
    return one_stats

all_stats = {}
one_suit = int(TOTAL_CARDS/SUIT_NUMBER)

for main_ind,power_list in enumerate(powered_cards_list):
    ability_orders = [0] * (one_suit+1)
    
    for ind,power in enumerate(power_list):
        ability_orders[power] = ind+1
    all_stats[main_ind] = genStats(ability_orders)

    





_DEFAULT_PARAMS = {
    "rules": 0
}

_NUM_PLAYERS = 2
_GAME_TYPE = pyspiel.GameType(
    short_name="python_autobattler",
    long_name="Python Autobattler",
    dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
    chance_mode=pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC,
    information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
    utility=pyspiel.GameType.Utility.ZERO_SUM,
    reward_model=pyspiel.GameType.RewardModel.TERMINAL,
    max_num_players=_NUM_PLAYERS,
    min_num_players=_NUM_PLAYERS,
    provides_information_state_string=True,
    provides_information_state_tensor=True,
    provides_observation_string=True,
    provides_observation_tensor=True,
    provides_factored_observation_string=True,
    parameter_specification=_DEFAULT_PARAMS)
_GAME_INFO = pyspiel.GameInfo(
    num_distinct_actions=3,
    max_chance_outcomes=len(all_deals),
    num_players=_NUM_PLAYERS,
    min_utility=-1.0,
    max_utility=1.0,
    utility_sum=0.0,
    max_game_length=1)  # e.g. Pass, Bet, Bet


class MaAutobattlerGame(pyspiel.Game):
  """A Python version of Kuhn poker."""

  def __init__(self, params=None):
    super().__init__(_GAME_TYPE, _GAME_INFO, params or dict())
    self.rules = params["rules"]
    self.total_cards = TOTAL_CARDS
    self.stats = all_stats[self.rules]
  
  def new_initial_state(self):
    """Returns a state corresponding to the start of a game."""
    return MaAutobattlerState(self,self.rules)
  
  def rules_to_str(self):
    res = ""
    tmp = all_stats[self.rules]
    for k in tmp:
      val = tmp[k]
      if val[2] == 0: 
        ability = str(engine.Ability_List[val[1]])
        st = str(val[0])
        res_str = "||{}:{} {}||".format(k//2,st,ability)
        res+=res_str
    #res = str(all_stats[self.rules])
    return res

  def get_hands(self,action):
      deal = all_deals[action]
      left_cards = list(map(lambda x:x.item(),deal[0]))
      right_cards = list(map(lambda x:x.item(),deal[1]))
      return {"deal":[left_cards,right_cards], "left":left_cards,"right":right_cards}

  def make_py_observer(self, iig_obs_type=None, params=None):
    """Returns an object used for observing game state."""
    return MaAutobattlerObserver(
        iig_obs_type or pyspiel.IIGObservationType(perfect_recall=True),
        params)


class MaAutobattlerState(pyspiel.State):
  """A python version of the Kuhn poker state."""

  def __init__(self, game, rules):
    """Constructor; should only be called by Game.new_initial_state."""
    super().__init__(game)
    self.left_cards = []
    self.right_cards = []
    self._game_over = False
    self.stage = 0
    self.game_res = [0,0]
    self.stats = all_stats[rules]
    self.left_discard = -1
    self.right_discard = -1
    self.winner_stat = 0

  # OpenSpiel (PySpiel) API functions are below. This is the standard set that
  # should be implemented by every sequential-move game with chance.

  def current_player(self):
    """Returns id of the next player to move, or TERMINAL if game is over."""
    if self._game_over:
      return pyspiel.PlayerId.TERMINAL
    elif self.stage == 0:
      return pyspiel.PlayerId.CHANCE
    elif self.stage==3:
      return pyspiel.PlayerId.CHANCE
    elif self.stage == 1:
      return 0
    elif self.stage == 2:
      return 1
    else:
      raise Exception('strange stage')

  def _legal_actions(self, player):
    """Returns a list of legal actions, sorted in ascending order."""
    assert player >= 0
    return [0,1,2]

  def chance_outcomes(self):
    """Returns the possible chance outcomes and their probabilities."""
    assert self.is_chance_node()
    if self.stage == 0:
      outcomes = all_deals_ind
    else:
      outcomes = [0,1,2,3]
    p = 1.0 / len(outcomes)
    return [(o, p) for o in outcomes]

  def _apply_action(self, action):
    """Applies the specified action to the state."""
    logger.debug("stage is {}, applying {}".format(self.stage,action))
    resLog = None
    if self.stage == 0:
      deal = all_deals[action]
      self.left_cards = deal[0]
      self.right_cards = deal[1]
      self.stage = 1
      return
    
    if self.stage == 1:
      # 1st player choosing
      self.left_discard =  self.left_cards[action]

      self.left_cards = [x for x in self.left_cards if x != self.left_discard]
      self.stage = 2
      return
    if self.stage == 2:
      self.right_discard = self.right_cards[action]
      self.right_cards = [x for x in self.right_cards if x !=  self.right_discard]
      self.stage = 3
      return

    if self.stage == 3:
      # shuffle. 
      if action == 0:
        pass
      elif action == 1:
        self.left_cards = self.left_cards[::-1]
      elif action == 2:
        self.right_cards = self.right_cards[::-1]
      elif action == 3:
        self.left_cards = self.left_cards[::-1]
        self.right_cards = self.right_cards[::-1]

    #the game
    key = str(self.left_cards) + " " + str(self.right_cards)
    logger.debug(str(self.left_cards) + " " + str(self.right_cards))
    if False and key in Cache:
      res = Cache[key]
      if res ==-1:
        self.game_res = [1,-1]
      else:
        self.game_res = [-1,1]  
    else:
      ge = engine.GameEngine(self.left_cards,self.right_cards,self.stats)
      resLog = ge.main_loop()
      res = ge.return_winner()
      self.winner_stat = ge.return_winner_stat()
      
      Cache[key] = res
      if res ==-1:
        self.game_res = [1,-1]
      elif res == 0:
        self.game_res= [0,0]
      else:
        self.game_res = [-1,1]  
    
    self._game_over = True
    return resLog

  def action_to_card(self,action,player):
    res = -1
    if player == 0:
      res = self.left_cards[action]
    elif player == 1:
      res = self.right_cards[action]
    return res

  
  def policy_to_cards(self,policy,player):
    res = np.zeros(TOTAL_CARDS)
    policy_list = []
    for key in policy:
      policy_list.append(policy[key])
    for ind,prob in enumerate(policy_list[0:3]):
      card = self.action_to_card(ind,player)
      res[card] = prob
    return res
  

  def _action_to_string(self, player, action):
    """Action -> string."""
    
    if self.stage == 0:
      return str(all_deals[action])
    elif self.stage==3:
      lc = str(self.left_cards)
      lr = str(self.right_cards)
      if action == 0:
        pass
      elif action == 2:
        lc = str(self.left_cards[::-1])
      elif action == 3:
        lr = str(self.right_cards[::-1])
      elif action == 4:
        lc = str(self.left_cards[::-1])
        lr = str(self.right_cards[::-1])

      return "Left cards {}, right cards {}".format(lc,lr)
      
    elif self.stage == 1:
      
      return "1st discards {}".format(str(action)) 
    elif self.stage == 2:
      return "2nd discard {}".format(str(action)) 


  def is_terminal(self):
    """Returns True if the game is over."""
    return self._game_over

  def returns(self):
    return self.game_res

  def __str__(self):
    """String for debug purposes. No particular semantics are required."""
    return "left cards {}, right cards {}, res {}".format(self.left_cards,self.right_cards,self.game_res)


class MaAutobattlerObserver:
  """Observer, conforming to the PyObserver interface (see observation.py)."""

  def __init__(self, iig_obs_type, params):
    """Initializes an empty observation tensor."""
    if params:
      raise ValueError(f"Observation parameters not supported; passed {params}")

    # Determine which observation pieces we want to include.
    pieces = [("player", 2, (2,))]
    if iig_obs_type.private_info == pyspiel.PrivateInfoType.SINGLE_PLAYER:
      pieces.append(("hand", TOTAL_CARDS, (TOTAL_CARDS,)))
      pieces.append(("discard", TOTAL_CARDS, (TOTAL_CARDS,)))

    # if iig_obs_type.public_info:
    #   if iig_obs_type.perfect_recall:
    #     pieces.append(("betting", 6, (3, 2)))
    #   else:
    #     pieces.append(("pot_contribution", 2, (2,)))

    # Build the single flat tensor.
    total_size = sum(size for name, size, shape in pieces)
    self.tensor = np.zeros(total_size, np.float32)

    # Build the named & reshaped views of the bits of the flat tensor.
    self.dict = {}
    index = 0
    for name, size, shape in pieces:
      self.dict[name] = self.tensor[index:index + size].reshape(shape)
      index += size

  def set_from(self, state, player):
    """Updates `tensor` and `dict` to reflect `state` from PoV of `player`."""
    self.tensor.fill(0)
    if "player" in self.dict:
      self.dict["player"][player] = 1
    if "hand" in self.dict:
      if player == 0:
        for card in state.left_cards:
          self.dict["hand"][card] = 1
      elif player == 1:
         for card in state.right_cards:
          self.dict["hand"][card] = 1
      else:
        raise Exception("Strange state")
    
    if "discard" in self.dict:
      if player == 0:
        self.dict["discard"][state.left_discard] = 1
      elif player == 1:
        self.dict["discard"][state.right_discard] = 1
      else:
        raise Exception("Strange state 2")

    
   

  def string_from(self, state, player):
    """Observation of `state` from the PoV of `player`, as a string."""
    pieces = []
    if "player" in self.dict:
      pieces.append(f"p{player}")
    if "hand" in self.dict:
      if player == 0:
        pieces.append(f"hand:{state.left_cards}")
      else:
        pieces.append(f"hand:{state.right_cards}")
    if "discard" in self.dict:
      if player == 0:
        pieces.append(f"hand:{state.left_discard}")
      else:
        pieces.append(f"hand:{state.right_discard}")
    #print(state)
    #print(self.dict)
    return " ".join(str(p) for p in pieces)


# Register the game with the OpenSpiel library

pyspiel.register_game(_GAME_TYPE, MaAutobattlerGame)


def printResLog(resLog):
  for stage in resLog:
    print(stage)
    for event in stage["events"]:
      print(event)
if __name__ == "__main__":
  print(len(all_deals))
  print(all_stats[1])
 
  game = MaAutobattlerGame({"rules":1})
  print(game.rules_to_str())
  state = game.new_initial_state()
  resLog = []
  while not state.is_terminal():
    if state.current_player() == pyspiel.PlayerId.CHANCE:
      lc = state.chance_outcomes()
      c = lc[0][0]
      resLog = state._apply_action(c)
      if resLog!=None and len(resLog) > 0:

        res = json.dumps(resLog,default=vars)
        print(res)
        #printResLog(resLog)
    else:
      la = state._legal_actions(state.current_player())
      a = la[0] 
      b = state._apply_action(a)
     
  print("done")
