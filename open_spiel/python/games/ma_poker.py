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

import pyspiel


class Action_Raider(enum.IntEnum):
  PLUNDER = 0
  REST = 1

class Action_Peasant(enum.IntEnum):
  GROW = 2
  BUILD_TOWER = 3
  BUILD_KEEP = 4

_TOTAL_EPOCHS=6
_PRICES=[4,8]
_DEFENSE=[7,24]
_NUM_PLAYERS = 2
_START_MONEY=[2,2]
_DECK = frozenset([0, 1, 2])
_GAME_TYPE = pyspiel.GameType(
    short_name="python_ma_poker",
    long_name="Python Ma Poker",
    dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
    chance_mode=pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC,
    information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
    utility=pyspiel.GameType.Utility.CONSTANT_SUM,
    reward_model=pyspiel.GameType.RewardModel.TERMINAL,
    max_num_players=_NUM_PLAYERS,
    min_num_players=_NUM_PLAYERS,
    provides_information_state_string=True,
    provides_information_state_tensor=True,
    provides_observation_string=True,
    provides_observation_tensor=True,
    provides_factored_observation_string=True)
_GAME_INFO = pyspiel.GameInfo(
    num_distinct_actions=len(Action_Raider) + len(Action_Peasant),
    max_chance_outcomes=len(_DECK),
    num_players=_NUM_PLAYERS,
    min_utility=-2.0,
    max_utility=2.0,
    utility_sum=0.0,
    max_game_length=3)  # e.g. Pass, Bet, Bet


class MaPokerGame(pyspiel.Game):
  """A Python version of Kuhn poker."""

  def __init__(self, params=None):
    super().__init__(_GAME_TYPE, _GAME_INFO, params or dict())

  def new_initial_state(self):
    """Returns a state corresponding to the start of a game."""
    return MaPokerState(self)

  def make_py_observer(self, iig_obs_type=None, params=None):
    """Returns an object used for observing game state."""
    return MaPokerObserver(
        iig_obs_type or pyspiel.IIGObservationType(perfect_recall=False),
        params)


class MaPokerState(pyspiel.State):
  """A python version of the Ma poker state."""

  def __init__(self, game):
    """Constructor; should only be called by Game.new_initial_state."""
    super().__init__(game)
    self.resources = _START_MONEY
    self.hidden_action = -1
    self.buildings = [False,False]
    self.bets = []
    self._game_over = False
    self._current_player = 0
    self._round_counter = 0
    self.history_raider = []
    self.history_peasant = []
    self.all_history = []


  # OpenSpiel (PySpiel) API functions are below. This is the standard set that
  # should be implemented by every sequential-move game with chance.

  def current_player(self):
    """Returns id of the next player to move, or TERMINAL if game is over."""
    # if self._game_over:
    #   return pyspiel.PlayerId.TERMINAL
    # elif len(self.cards) < _NUM_PLAYERS:
    #   return pyspiel.PlayerId.CHANCE
    # else:
    #   return self._next_player
    return self._current_player

  def _legal_actions(self, player):
    """Returns a list of legal actions, sorted in ascending order."""
    assert player >= 0
    
    if player == 0:
      if self.resources[0]>=2: 
        return [Action_Raider.PLUNDER, Action_Raider.REST]
      else:
        return [Action_Raider.REST]

    else:
      res = [Action_Peasant.GROW]
      #player2

      if self.resources[1] >= _PRICES[0] and not self.buildings[0]:
        res.append(Action_Peasant.BUILD_TOWER)
      
      if self.resources[1] >= _PRICES[1] and not self.buildings[1]:
        res.append(Action_Peasant.BUILD_KEEP)

      return res


  # def chance_outcomes(self):
  #   """Returns the possible chance outcomes and their probabilities."""
  #   assert self.is_chance_node()
  #   outcomes = sorted(_DECK - set(self.cards))
  #   p = 1.0 / len(outcomes)
  #   return [(o, p) for o in outcomes]

  def _apply_action(self, action):
    """Applies the specified action to the state."""

    self.all_history.append(action) 
    self._current_player = (self._current_player+1)%2
    
    if action == Action_Raider.REST:


      self.hidden_action = Action_Raider.REST
      self.history_raider.append(action)

    if action == Action_Raider.PLUNDER:

      self.hidden_action = Action_Raider.PLUNDER
      self.history_raider.append(action)

    
    #peasant
    if action == Action_Peasant.GROW:
      if self.resources[1] == 0:
        self.resources[1] = 1
      else:
        self.resources[1]*=2
    
    if action == Action_Peasant.BUILD_TOWER:
      self.resources[1]-= _PRICES[0]
      self.buildings[0] = True
    
    if action == Action_Peasant.BUILD_KEEP:
      self.resources[1]-= _PRICES[1]
      self.buildings[1] = True
      #all
    if action > 1:
      self.history_peasant.append(action)
      self._round_counter+=1
      if self._round_counter>=_TOTAL_EPOCHS:
          self._game_over = True

      if self.hidden_action == Action_Raider.REST:
          self.resources[0]+=1
      else:
          self.resources[0]-=2

          if not self.buildings[0] and not self.buildings[1]:
            self.resources[0]+= self.resources[1]
            self.resources[1] = 0
          else:
            if self.buildings[1]:
              if self.resources[1] > _DEFENSE[1]:
                self.resources[0] += self.resources[1] - _DEFENSE[1]

                self.resources[1] = _DEFENSE[1]
              else:
                 if self.buildings[0]:
                  if self.resources[1] > _DEFENSE[0]:
                    self.resources[0] += self.resources[1] - _DEFENSE[0]

                    self.resources[1] = _DEFENSE[0]
            else:
                if self.buildings[0]:
                  if self.resources[1] > _DEFENSE[0]:
                    self.resources[0] += self.resources[1] - _DEFENSE[0]

                    self.resources[1] = _DEFENSE[0]

      self.hidden_action = -1




                  

      
  def _action_to_string(self, player, action):
    res = "???"
    if action == 0:
      res = "PLUNDER"
    elif action == 1:
      res = "REST"
    elif action == 2:
     res = "Grow"
    elif action == 3:
      res = "Tower"
    elif action == 4:
      res = "Keep"
   
    return res

  def is_terminal(self):
    """Returns True if the game is over."""
    return self._game_over

  def returns(self):
    """Total reward for each player over the course of the game so far."""
    resources = self.resources
    if not self._game_over:
      return [0, 0]
    else:
     return resources

  def __str__(self):
    """String for debug purposes. No particular semantics are required."""
    return str(self.all_history) +" " + str(self.resources[0]) + " " + str(self.resources[1])


class MaPokerObserver:
  """Observer, conforming to the PyObserver interface (see observation.py)."""

  def __init__(self, iig_obs_type, params):
    """Initializes an empty observation tensor."""
    if params:
      raise ValueError(f"Observation parameters not supported; passed {params}")

    # Determine which observation pieces we want to include.
    pieces = [("player", 2, (2,))]
    # if iig_obs_type.private_info == pyspiel.PrivateInfoType.SINGLE_PLAYER:
    #   pieces.append(("private_action", 5, (5,)))
    if iig_obs_type.public_info:
      if iig_obs_type.perfect_recall:
        pieces.append(("actions", _TOTAL_EPOCHS*2*5, (_TOTAL_EPOCHS*2, 5)))
      else:
        pieces.append(("resources", 4, (4,)))

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
    # if "private_action" in self.dict:
    #   if player == 0:        
    #     self.dict["private_action"][state.history_raider] = 1
    #   else:
    #     self.dict["private_action"][state.history_peasant] = 1

    if "resources" in self.dict:
      self.dict["resources"][:2] = state.resources
      self.dict["resources"][2] = 1 if state.buildings[0] else 0
      self.dict["resources"][3] = 1 if state.buildings[1] else 1
      

    #print(state)

    if "actions" in self.dict:
      for turn, action in enumerate(state.all_history):
        self.dict["actions"][turn, action] = 1
    #print(self.dict)

  def string_from(self, state, player):
    """Observation of `state` from the PoV of `player`, as a string."""
    return str(state)
    # pieces = []
    # if "player" in self.dict:
    #   pieces.append(f"p{player}")
    # if "private_card" in self.dict and len(state.cards) > player:
    #   pieces.append(f"card:{state.cards[player]}")
    # if "pot_contribution" in self.dict:
    #   pieces.append(f"pot[{int(state.pot[0])} {int(state.pot[1])}]")
    # if "betting" in self.dict and state.bets:
    #   pieces.append("".join("pb"[b] for b in state.bets))
    # return " ".join(str(p) for p in pieces)


# Register the game with the OpenSpiel library

pyspiel.register_game(_GAME_TYPE, MaPokerGame)
