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

"""Python implementation for Monte Carlo Counterfactual Regret Minimization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import enum
import numpy as np
import open_spiel.python.algorithms.mccfr as mccfr
import open_spiel.python.games.ma_autobattler_tree_meta as matm
import pyspiel


class AverageType(enum.Enum):
  SIMPLE = 0
  FULL = 1


class ExternalSamplingSolverNoMeta(mccfr.MCCFRSolverBase):
  """An implementation of external sampling MCCFR."""

  def __init__(self, game,meta_range, average_type=AverageType.SIMPLE):
    super().__init__(game)
    # How to average the strategy. The 'simple' type does the averaging for
    # player i + 1 mod num_players on player i's regret update pass; in two
    # players this corresponds to the standard implementation (updating the
    # average policy at opponent nodes). In n>2 players, this can be a problem
    # for several reasons: first, it does not compute the estimate as described
    # by the (unbiased) stochastically-weighted averaging in chapter 4 of
    # Lanctot 2013  commonly used in MCCFR because the denominator (important
    # sampling correction) should include all the other sampled players as well
    # so the sample reach no longer cancels with reach of the player updating
    # their average policy. Second, if one player assigns zero probability to an
    # action (leading to a subtree), the average policy of a different player in
    # that subtree is no longer updated. Hence, the full averaging does not
    # update the average policy in the regret passes but does a separate pass to
    # update the average policy. Nevertheless, we set the simple type as the
    # default because it is faster, seems to work better empirically, and it
    # matches what was done in Pluribus (Brown and Sandholm. Superhuman AI for
    # multiplayer poker. Science, 11, 2019).
    self._average_type = average_type
    self.meta_range = meta_range

    assert game.get_type().dynamics == pyspiel.GameType.Dynamics.SEQUENTIAL, (
        "MCCFR requires sequential games. If you're trying to run it " +
        'on a simultaneous (or normal-form) game, please first transform it ' +
        'using turn_based_simultaneous_game.')

  def iteration(self):
    """Performs one iteration of external sampling.

    An iteration consists of one episode for each player as the update
    player.
    """
    for m in self.meta_range:
      meta = matm.all_stats_by_ind[m]
      for player in range(self._num_players-1):
        self._update_regrets(self._game.new_initial_state(), player,meta)
      # if self._average_type == AverageType.FULL:
    #   reach_probs = np.ones(self._num_players, dtype=np.float64)
    #   self._full_update_average(self._game.new_initial_state(), reach_probs)

 
 

  def _update_regrets(self, state, player, meta ):
    """Runs an episode of external sampling.

    Args:
      state: the open spiel state to run from
      player: the player to update regrets for

    Returns:
      value: is the value of the state in the game
      obtained as the weighted average of the values
      of the children
    """
    
    if state.is_terminal():
      return state.player_return(player)

    if state.is_chance_node():
      outcomes, probs = zip(*state.chance_outcomes())
      outcome = np.random.choice(outcomes, p=probs)
      return self._update_regrets(state.child(outcome), player,meta)

    cur_player = state.current_player()
    info_state_key = state.information_state_string(cur_player)
    legal_actions = state.legal_actions()
    num_legal_actions = len(legal_actions)

    infostate_info = self._lookup_infostate_info(info_state_key,
                                                 num_legal_actions)
    policy = self._regret_matching(infostate_info[mccfr.REGRET_INDEX],
                                   num_legal_actions)

    value = 0
    child_values = np.zeros(num_legal_actions, dtype=np.float64)
    if cur_player != player:
      if cur_player!=2:
        # Sample at opponent node
        action_idx = np.random.choice(np.arange(num_legal_actions), p=policy)
        value = self._update_regrets(
            state.child(legal_actions[action_idx]), player,meta)
      else:
        a = meta[0]
        meta = meta[1:]

        value = self._update_regrets(
            state.child(a), player,meta)
    else:
      # Walk over all actions at my node
      for action_idx in range(num_legal_actions):
        child_values[action_idx] = self._update_regrets(
            state.child(legal_actions[action_idx]), player, meta)
        value += policy[action_idx] * child_values[action_idx]

    if cur_player == player:
      # Update regrets.
      for action_idx in range(num_legal_actions):
        self._add_regret(info_state_key, action_idx,
                         child_values[action_idx] - value)
    # Simple average does averaging on the opponent node. To do this in a game
    # with more than two players, we only update the player + 1 mod num_players,
    # which reduces to the standard rule in 2 players.
    if self._average_type == AverageType.SIMPLE and cur_player == (
        player + 1) % self._num_players:
      for action_idx in range(num_legal_actions):
        self._add_avstrat(info_state_key, action_idx, policy[action_idx])
        self._add_avvisit(info_state_key, action_idx, 1)

    return value
