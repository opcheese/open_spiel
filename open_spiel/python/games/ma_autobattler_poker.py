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


logger = logging.getLogger("somelogger")

Cache = {}
### initiate deals
TOTAL_CARDS = 14
HAND_SIZE = 3
SUIT_NUMBER=2

CARDS_PER_SUIT = int(TOTAL_CARDS/SUIT_NUMBER)
cards = list(np.arange(TOTAL_CARDS))
c85 = math.comb(TOTAL_CARDS,HAND_SIZE)
c53 = math.comb(TOTAL_CARDS - HAND_SIZE,HAND_SIZE)
total_combinations = c85*c53
first_hands = itertools.combinations(cards,3)
list_first_hand = list(first_hands)

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
card_types = list(np.arange(TOTAL_CARDS/SUIT_NUMBER, dtype=int))
powered_cards_list = list(itertools.permutations(card_types,4))
def genStats(ability_order):
    one_stats = {}
    for i in range(int(TOTAL_CARDS/SUIT_NUMBER)):
        for j in range(SUIT_NUMBER):
            one_stats[i*SUIT_NUMBER +j ] = [i%CARDS_PER_SUIT+1,ability_order[i],j]
    return one_stats

all_stats = {}
one_suit = int(TOTAL_CARDS/SUIT_NUMBER)

for main_ind,power_list in enumerate(powered_cards_list):
    ability_orders = [0] * one_suit
    
    for ind,power in enumerate(power_list):
        ability_orders[power] = ind+1
    all_stats[main_ind] = genStats(ability_orders)

    

class Card():
    def __init__(self, stat, ability,suit,side_num):
        #self.priority = priority
        self.stat = stat
        self.is_dead = False
        self.ability = ability
        self.initial_stat = stat
        self.suit = suit
        self.swang_called = False
        self.side_num = side_num

    def take_damage(self,damage):
        self.stat -= damage
        if self.stat <= 0:
            self.is_dead = True
    
    def debut(self,state,side_num):
         self.ability.debut(state,side_num,self)

    def performance(self,state):
         self.ability.performance(state,self)


    def swangsong(self,state,side_num):
         if not self.swang_called:
            self.swang_called = True
            self.ability.swangsong(state,side_num,self)
    
    def __str__(self):
        res = "intial {}| current {}|suit {}| ability {}".format(self.initial_stat,self.stat,self.suit, str(self.ability))
        return res
    
    def __repr__(self):
        return self.__str__()



class BasicAbility():
    def __init__(self):
        pass
    
    def debut(self,state,side_num,card):
        side =  state.left_side if side_num ==0 else state.right_side
        while len(side) > 0:
            for card in side:
                state.kill_card(card)
        state.clean_up()
        
    def swangsong(self,state,side_num,card):
        pass

    def performance(self,state,card):
        pass

    def __str__(self):
        res =  type(self).__name__
        return res

class EaterAbility(BasicAbility):
    def __init__(self):
        pass
    
    def debut(self,state,side_num,card):
        side =  state.left_side if side_num ==0 else state.right_side
        while len(side) > 0:
            for old_card in side:
                if card.suit == old_card.suit:
                    card.stat+=old_card.stat
                state.kill_card(old_card)
        state.clean_up()
        


    def __str__(self):
        res =  type(self).__name__
        return res


class FighterAbility(BasicAbility):
    def __init__(self):
        pass

    def performance(self,state,card):
        side =  state.left_side if card.side_num ==1 else state.right_side
        enemy = side[0]
        if not enemy.suit==card.suit:
            card.stat+=2  
        
class MartyrdomAbility(BasicAbility):
    def __init__(self):
        super().__init__()

    def swangsong(self,state,side_num,card):
        side =  state.left_side if side_num ==1 else state.right_side
        for card in side:
           state.kill_card(card)
        state.clean_up()

    # def __str__(self):
    #     return super().__str__()

class TokenAbility(BasicAbility):
    def __init__(self):
        pass
        
    def swangsong(self,state,side_num,card):
        side =  state.left_side if side_num ==0 else state.right_side
        token = state.create_card(1,0,card.suit)
        state.add_card(token,side_num)


class BoardState():
    def __init__(self):
         self.left_side = []
         self.right_side = []

    def left_count(self):
        return len(self.left_side)
    
    def right_count(self):
        return len(self.right_side)
         
    @staticmethod
    def create_card(stat, ability_num,suit):
        #side =  self.left_side if side_num ==0 else self.right_side
        card = Card(stat, Ability_List[ability_num],suit,0)
        return card

        
    def add_card(self,card,side_num):
        side =  self.left_side if side_num ==0 else self.right_side
        card.side_num = side_num
        card.debut(self,side_num)
        side.append(card)

    def clean_side(self, side_num):
        side =  self.left_side if side_num ==0 else self.right_side
        self.clean_up()
         


    def kill_card(self, card):
        side = None
        side_num=-1
        not_found= False
        if card in self.left_side:
            side = self.left_side
            side_num = 0
        elif card in self.right_side:
            side = self.right_side
            side_num = 1
        else:
            not_found = True
        if not not_found:
            card.swangsong(self,side_num)
            if card in side:
                side.remove(card)

    def clean_up(self):
        for card in self.left_side:
            if card.is_dead and card.swang_called:
                self.left_side.remove(card)
        for card in self.right_side:
            if card.is_dead and card.swang_called:
                self.right_side.remove(card)



    def perfomance(self):
        left_card = self.left_side[0]
        right_card = self.right_side[0]
        left_card.performance(self)
        right_card.performance(self)

        right_attack = right_card.stat
        left_attack = left_card.stat
        left_card.take_damage(right_attack)
        right_card.take_damage(left_attack)
        if left_card.is_dead:
            self.kill_card(left_card)
        #right card might have died as a result of swangsong    
        if right_card.is_dead and right_card in self.right_side:
            self.kill_card(right_card)
        self.clean_up()

    def __str__(self):
        lc ='EMPTY' if len(self.left_side) == 0 else  str(self.left_side[0])
        rc ='EMPTY' if len(self.right_side) == 0 else  str(self.right_side[0])

        res = lc + '|||' + rc
        return res

class GameEngine():
    def __init__(self, first_hand,second_hand,stats):
        self.board_state = BoardState()
        self.left_cards = []
        self.right_cards = []
        for card_num in first_hand:
            card = BoardState.create_card(stats[card_num][0],stats[card_num][1],stats[card_num][2])
            self.left_cards.append(card)
        
        for card_num in second_hand:
            card = BoardState.create_card(stats[card_num][0],stats[card_num][1],stats[card_num][2])
            self.right_cards.append(card)
        
        self.current_phaze = 0

    def return_winner(self):
        if len(self.board_state.left_side) > len(self.board_state.right_side):
            return -1 #left winner 
        elif len(self.board_state.left_side) < len(self.board_state.right_side):
            return 1 #right winner
        else:
            return 0 #draw
    
    def main_loop(self):

        game_over = False
        logger.debug("---new game---")
        while not game_over:
            logger.debug("---new round---")
            logger.debug("--initial ---" + str(self.board_state))
            logger.debug("left hand:"+str(self.left_cards))
            logger.debug("right hand:"+str(self.right_cards))
            
            fight_worthy = self.board_state.left_count() > 0 and self.board_state.right_count() > 0
            enough_draw = len(self.left_cards)>0 and len(self.right_cards)>0
            if not enough_draw and not fight_worthy:
                game_over = True
                break
            if self.current_phaze == 0:
                logger.debug("---phaze 0---")
            
                if  enough_draw:
                    cardL = self.left_cards.pop()
                    self.board_state.add_card(cardL,0)

                    cardR = self.right_cards.pop()
                    self.board_state.add_card(cardR,1)

                self.current_phaze=1
            
            logger.debug("--play ---" + str(self.board_state))

            fight_worthy = self.board_state.left_count() > 0 and self.board_state.right_count() > 0


            if self.current_phaze==1 and fight_worthy:
                self.board_state.perfomance()
                self.current_phaze = 0
            
            logger.debug("--after ---" + str(self.board_state))

  

Ability_List = []
Ability_List.append(BasicAbility())
Ability_List.append(MartyrdomAbility())
Ability_List.append(TokenAbility())
Ability_List.append(EaterAbility())
Ability_List.append(FighterAbility())

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
  def new_initial_state(self):
    """Returns a state corresponding to the start of a game."""
    return MaAutobattlerState(self,self.rules)

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
    if key in Cache:
      res = Cache[key]
      if res ==-1:
        self.game_res = [1,-1]
      else:
        self.game_res = [-1,1]  
    else:
      ge = GameEngine(self.left_cards,self.right_cards,self.stats)
      ge.main_loop()
      res = ge.return_winner()
      Cache[key] = res
      if res ==-1:
        self.game_res = [1,-1]
      else:
        self.game_res = [-1,1]  
    
    self._game_over = True

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
