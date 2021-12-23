// Copyright 2019 DeepMind Technologies Ltd. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Copyright 2021 DeepMind Technologies Limited
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "open_spiel/algorithms/best_response.h"

#include <cmath>
#include <cstddef>
#include <functional>
#include <iostream>
#include <unordered_set>

#include "open_spiel/algorithms/minimax.h"
#include "open_spiel/game_parameters.h"
#include "open_spiel/games/efg_game.h"
#include "open_spiel/games/efg_game_data.h"
#include "open_spiel/games/goofspiel.h"
#include "open_spiel/games/kuhn_poker.h"
#include "open_spiel/games/leduc_poker.h"
#include "open_spiel/games/liars_dice.h"
#include "open_spiel/games/tic_tac_toe.h"
#include "open_spiel/policy.h"
#include "open_spiel/spiel.h"
#include "open_spiel/spiel_utils.h"

namespace open_spiel {
namespace algorithms {
namespace {

using InfostatesAndActions = std::vector<std::pair<std::string, Action>>;


// Correct values come from the existing Python implementation in
// open_spiel/python/algorithms/exploitability.py.
std::vector<std::pair<std::string, double>>
GetKuhnUniformBestResponseValuesPid0() {
  std::vector<std::pair<std::string, double>> history_and_probs = {
      {"2", 1.5},
      {"2, 1, 1, 1", 2.0},
      {"2, 1, 1, 0", 1.0},
      {"2, 1, 0, 1, 0", -1.0},
      {"2, 1, 0, 1", 2.0},
      {"2, 1, 0, 0", 1.0},
      {"2, 0, 1, 1", 2.0},
      {"2, 1, 0", 1.5},
      {"2, 0, 0, 0", 1.0},
      {"2, 0, 0, 1, 1", 2.0},
      {"2, 0, 0", 1.5},
      {"2, 1, 1", 1.5},
      {"2, 0, 1, 0", 1.0},
      {"2, 1, 0, 1, 1", 2.0},
      {"2, 0", 1.5},
      {"2, 1", 1.5},
      {"2, 0, 0, 1", 2.0},
      {"2, 0, 1", 1.5},
      {"2, 0, 0, 1, 0", -1.0},
      {"1, 0", 1.5},
      {"0", -0.5},
      {"1, 2", -0.5},
      {"0, 2, 0", -1.0},
      {"", 0.5},
      {"0, 1", -0.5},
      {"0, 2", -0.5},
      {"1, 2, 0, 0", -1.0},
      {"0, 1, 0", -1.0},
      {"1", 0.5},
      {"0, 2, 1", -0.5},
      {"1, 2, 0, 1", -2.0},
      {"0, 1, 1", -0.5},
      {"1, 2, 0, 1, 1", -2.0},
      {"0, 2, 1, 1", -2.0},
      {"1, 2, 1", -0.5},
      {"0, 1, 0, 1", -1.0},
      {"1, 0, 1, 0", 1.0},
      {"0, 2, 0, 0", -1.0},
      {"1, 2, 0", -1.5},
      {"0, 2, 1, 0", 1.0},
      {"0, 1, 0, 0", -1.0},
      {"1, 0, 1, 1", 2.0},
      {"1, 2, 1, 0", 1.0},
      {"1, 0, 0, 1, 0", -1.0},
      {"0, 1, 1, 0", 1.0},
      {"1, 0, 0", 1.5},
      {"1, 2, 0, 1, 0", -1.0},
      {"0, 1, 0, 1, 0", -1.0},
      {"1, 0, 0, 1, 1", 2.0},
      {"1, 2, 1, 1", -2.0},
      {"0, 1, 1, 1", -2.0},
      {"1, 0, 1", 1.5},
      {"0, 1, 0, 1, 1", -2.0},
      {"0, 2, 0, 1", -1.0},
      {"1, 0, 0, 0", 1.0},
      {"0, 2, 0, 1, 1", -2.0},
      {"1, 0, 0, 1", 2.0},
      {"0, 2, 0, 1, 0", -1.0}};
  return history_and_probs;
}

std::vector<std::pair<std::string, double>>
GetKuhnUniformBestResponseValuesPid1() {
  std::vector<std::pair<std::string, double>> history_and_probs = {
      {"", 0.416666666667},
      {"0", 1.75},
      {"0, 1", 1.75},
      {"0, 1, 1", 2.0},
      {"0, 1, 1, 1", 2.0},
      {"0, 1, 1, 0", -1.0},
      {"0, 1, 0", 1.5},
      {"0, 1, 0, 1", 1.5},
      {"0, 1, 0, 1, 1", 2.0},
      {"0, 1, 0, 1, 0", 1.0},
      {"0, 1, 0, 0", 1.0},
      {"0, 2", 1.75},
      {"0, 2, 1", 2.0},
      {"0, 2, 1, 1", 2.0},
      {"0, 2, 1, 0", -1.0},
      {"0, 2, 0", 1.5},
      {"0, 2, 0, 1", 1.5},
      {"0, 2, 0, 1, 1", 2.0},
      {"0, 2, 0, 1, 0", 1.0},
      {"0, 2, 0, 0", 1.0},
      {"1", 0.5},
      {"1, 0", -0.75},
      {"1, 0, 1", -1.0},
      {"1, 0, 1, 1", -2.0},
      {"1, 0, 1, 0", -1.0},
      {"1, 0, 0", -0.5},
      {"1, 0, 0, 1", -0.5},
      {"1, 0, 0, 1, 1", -2.0},
      {"1, 0, 0, 1, 0", 1.0},
      {"1, 0, 0, 0", -1.0},
      {"1, 2", 1.75},
      {"1, 2, 1", 2.0},
      {"1, 2, 1, 1", 2.0},
      {"1, 2, 1, 0", -1.0},
      {"1, 2, 0", 1.5},
      {"1, 2, 0, 1", 1.5},
      {"1, 2, 0, 1, 1", 2.0},
      {"1, 2, 0, 1, 0", 1.0},
      {"1, 2, 0, 0", 1.0},
      {"2", -1.0},
      {"2, 0", -0.75},
      {"2, 0, 1", -1.0},
      {"2, 0, 1, 1", -2.0},
      {"2, 0, 1, 0", -1.0},
      {"2, 0, 0", -0.5},
      {"2, 0, 0, 1", -0.5},
      {"2, 0, 0, 1, 1", -2.0},
      {"2, 0, 0, 1, 0", 1.0},
      {"2, 0, 0, 0", -1.0},
      {"2, 1", -1.25},
      {"2, 1, 1", -2.0},
      {"2, 1, 1, 1", -2.0},
      {"2, 1, 1, 0", -1.0},
      {"2, 1, 0", -0.5},
      {"2, 1, 0, 1", -0.5},
      {"2, 1, 0, 1, 1", -2.0},
      {"2, 1, 0, 1, 0", 1.0},
      {"2, 1, 0, 0", -1.0}};
  return history_and_probs;
}

std::vector<std::pair<std::string, double>>
GetKuhnOptimalBestResponseValuesPid0() {
  std::vector<std::pair<std::string, double>> history_and_probs = {
      {"", -0.05555555555555558},
      {"1, 2, 0, 1", -1.0},
      {"1, 2, 1", -2.0},
      {"0, 2, 0, 0", -1.0},
      {"0, 1, 1, 0", 1.0},
      {"2, 1, 1, 0", 1.0},
      {"2, 0, 0, 1", 2.0},
      {"1, 2, 0, 0", -1.0},
      {"2, 0, 1", 1.0},
      {"0, 1, 1, 1", -2.0},
      {"2, 0, 0, 0", 1.0},
      {"2, 0, 0", 1.3333333333333333},
      {"1, 0", 0.3333333333333333},
      {"1, 0, 1, 1", 2.0},
      {"1, 0, 0, 1, 0", -1.0},
      {"1, 2, 1, 0", 1.0},
      {"2, 0, 1, 0", 1.0},
      {"0, 1", -1.0},
      {"0, 2", -1.0},
      {"1, 0, 0, 1, 1", 2.0},
      {"1, 0, 1, 0", 1.0},
      {"2, 0, 1, 1", 2.0},
      {"1, 2, 1, 1", -2.0},
      {"2, 1", 1.0},
      {"2, 1, 1, 1", 2.0},
      {"2, 0, 0, 1, 0", -1.0},
      {"1, 2, 0", -1.0},
      {"0, 2, 1, 1", -2.0},
      {"1, 0, 0, 0", 1.0},
      {"0, 2, 1", -2.0},
      {"2, 1, 0, 1", 2.0},
      {"1, 2, 0, 1, 1", -2.0},
      {"1, 2", -1.0},
      {"0, 1, 0, 1", -1.0},
      {"0, 2, 0", -1.0},
      {"0, 2, 1, 0", 1.0},
      {"1, 0, 0, 1", -1.0},
      {"1, 2, 0, 1, 0", -1.0},
      {"2, 1, 0, 0", 1.0},
      {"0, 1, 0, 0", -1.0},
      {"2, 1, 0, 1, 1", 2.0},
      {"2, 0", 1.3333333333333333},
      {"1, 0, 1", 1.0},
      {"0, 2, 0, 1, 0", -1.0},
      {"2, 0, 0, 1, 1", 2.0},
      {"0, 1, 0, 1, 0", -1.0},
      {"0, 1, 1", 0.0},
      {"2, 1, 1", 1.3333333333333333},
      {"2, 1, 0, 1, 0", -1.0},
      {"2", 1.1666666666666665},
      {"1", -0.33333333333333337},
      {"0", -1.0},
      {"0, 1, 0", -1.0},
      {"1, 0, 0", 0.3333333333333333},
      {"0, 2, 0, 1, 1", -2.0},
      {"0, 1, 0, 1, 1", -2.0},
      {"2, 1, 0", 1.0},
      {"0, 2, 0, 1", -1.0}};
  return history_and_probs;
}

std::vector<std::pair<std::string, double>>
GetKuhnOptimalBestResponseValuesPid1() {
  std::vector<std::pair<std::string, double>> history_and_probs = {
      {"", 0.0555555555556},
      {"0", 0.9},
      {"0, 1", 0.6},
      {"0, 1, 1", -1.0},
      {"0, 1, 1, 1", 2.0},
      {"0, 1, 1, 0", -1.0},
      {"0, 1, 0", 1.0},
      {"0, 1, 0, 1", 1.0},
      {"0, 1, 0, 1, 1", 2.0},
      {"0, 1, 0, 1, 0", 1.0},
      {"0, 1, 0, 0", 1.0},
      {"0, 2", 1.2},
      {"0, 2, 1", 2.0},
      {"0, 2, 1, 1", 2.0},
      {"0, 2, 1, 0", -1.0},
      {"0, 2, 0", 1.0},
      {"0, 2, 0, 1", 1.0},
      {"0, 2, 0, 1, 1", 2.0},
      {"0, 2, 0, 1, 0", 1.0},
      {"0, 2, 0, 0", 1.0},
      {"1", 0.266666666667},
      {"1, 0", -1.0},
      {"1, 0, 1", -1.0},
      {"1, 0, 1, 1", -2.0},
      {"1, 0, 1, 0", -1.0},
      {"1, 0, 0", -1.0},
      {"1, 0, 0, 1", -0.6},
      {"1, 0, 0, 1, 1", -2.0},
      {"1, 0, 0, 1, 0", 1.0},
      {"1, 0, 0, 0", -1.0},
      {"1, 2", 1.53333333333},
      {"1, 2, 1", 2.0},
      {"1, 2, 1, 1", 2.0},
      {"1, 2, 1, 0", -1.0},
      {"1, 2, 0", 1.53333333333},
      {"1, 2, 0, 1", 1.53333333333},
      {"1, 2, 0, 1, 1", 2.0},
      {"1, 2, 0, 1, 0", 1.0},
      {"1, 2, 0, 0", 1.0},
      {"2", -1.0},
      {"2, 0", -1.0},
      {"2, 0, 1", -1.0},
      {"2, 0, 1, 1", -2.0},
      {"2, 0, 1, 0", -1.0},
      {"2, 0, 0", -1.0},
      {"2, 0, 0, 1", -2.0},
      {"2, 0, 0, 1, 1", -2.0},
      {"2, 0, 0, 1, 0", 1.0},
      {"2, 0, 0, 0", -1.0},
      {"2, 1", -1.0},
      {"2, 1, 1", -1.0},
      {"2, 1, 1, 1", -2.0},
      {"2, 1, 1, 0", -1.0},
      {"2, 1, 0", -1.0},
      {"2, 1, 0, 1", -2.0},
      {"2, 1, 0, 1, 1", -2.0},
      {"2, 1, 0, 1, 0", 1.0},
      {"2, 1, 0, 0", -1.0}};
  return history_and_probs;
}

// The "GetKuhnEdIterNPolicy" functions return the policy that is dumped out by
// the exploitability_descent_test when running exploitability descent for N
// iterations. They are included here as a regression test,
// as the C++ best response code has been unable to replicate the existing
// results due to erroneously included state. This is fixed as of cl/238531924.
TabularPolicy GetKuhnEdIter1Policy() {
  return TabularPolicy({{"0", {{0, 0.5}, {1, 0.5}}},
                        {"0b", {{0, 0.5}, {1, 0.5}}},
                        {"0p", {{0, 0.5}, {1, 0.5}}},
                        {"0pb", {{0, 0.5}, {1, 0.5}}},
                        {"1", {{0, 0.5}, {1, 0.5}}},
                        {"1b", {{0, 0.5}, {1, 0.5}}},
                        {"1p", {{0, 0.5}, {1, 0.5}}},
                        {"1pb", {{0, 0.5}, {1, 0.5}}},
                        {"2", {{0, 0.5}, {1, 0.5}}},
                        {"2b", {{0, 0.5}, {1, 0.5}}},
                        {"2p", {{0, 0.5}, {1, 0.5}}},
                        {"2pb", {{0, 0.5}, {1, 0.5}}}});
}

TabularPolicy GetKuhnEdIter4Policy() {
  return TabularPolicy({{"0", {{0, 0.567034158868}, {1, 0.432965841132}}},
                        {"0b", {{0, 0.602000197743}, {1, 0.397999802257}}},
                        {"0p", {{0, 0.520821285373}, {1, 0.479178714627}}},
                        {"0pb", {{0, 0.621126761233}, {1, 0.378873238767}}},
                        {"1", {{0, 0.505160629764}, {1, 0.494839370236}}},
                        {"1b", {{0, 0.360357968472}, {1, 0.639642031528}}},
                        {"1p", {{0, 0.520821285373}, {1, 0.479178714627}}},
                        {"1pb", {{0, 0.378873238767}, {1, 0.621126761233}}},
                        {"2", {{0, 0.419580194883}, {1, 0.580419805117}}},
                        {"2b", {{0, 0.202838286881}, {1, 0.797161713119}}},
                        {"2p", {{0, 0.5}, {1, 0.5}}},
                        {"2pb", {{0, 0.202838286881}, {1, 0.797161713119}}}});
}

void CheckBestResponsesAgaintGoldenResponses(
    const InfostatesAndActions& golden_actions,
    std::unordered_map<std::string, Action>& best_responses) {
  SPIEL_CHECK_EQ(best_responses.size(), golden_actions.size());
  for (const auto& infostate_and_best_response : golden_actions) {
    const std::string& infostate = infostate_and_best_response.first;
    Action action = infostate_and_best_response.second;
    auto it = best_responses.find(infostate);
    if (it == best_responses.end())
      SpielFatalError(absl::StrCat("Infostate ", infostate,
                                   " not found in best_responses."));
    if (it->second != action) {
      SpielFatalError(absl::StrCat(
          "Wrong best response at infostate ", infostate, "; expected ", action,
          " but received ", best_responses[infostate]));
    }
  }
}

void CheckBestResponseAgainstGoldenPolicy(
    const Game& game, Player best_responder, const TabularPolicy& policy,
    const InfostatesAndActions& golden_actions) {
  TabularBestResponse best_response(game, best_responder, &policy);
  best_response.Value(*game.NewInitialState());
  std::unordered_map<std::string, Action> best_responses =
      best_response.GetBestResponseActions();
  CheckBestResponsesAgaintGoldenResponses(golden_actions, best_responses);
}

InfostatesAndActions GetKuhnUniformBestResponsePid0() {
  return InfostatesAndActions(
      {{"0", 1}, {"0pb", 0}, {"1", 1}, {"1pb", 1}, {"2", 0}, {"2pb", 1}});
}

InfostatesAndActions GetKuhnUniformBestResponsePid1() {
  return InfostatesAndActions(
      {{"0b", 0}, {"0p", 1}, {"1b", 1}, {"1p", 1}, {"2b", 1}, {"2p", 1}});
}

// The best response values are taken from the existing Python implementation in
// open_spiel/algorithms/exploitability.py.
void KuhnPokerUniformBestResponsePid0() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetUniformPolicy(*game);
  CheckBestResponseAgainstGoldenPolicy(*game, /*best_responder=*/Player{0},
                                       policy,
                                       GetKuhnUniformBestResponsePid0());
}

// The best response values are taken from the existing Python implementation in
// open_spiel/algorithms/exploitability.py.
void KuhnPokerUniformBestResponsePid1() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetUniformPolicy(*game);
  CheckBestResponseAgainstGoldenPolicy(*game, /*best_responder=*/Player{1},
                                       policy,
                                       GetKuhnUniformBestResponsePid1());
}

// The following are regression tests. They should produce the same result, but
// didn't previously due to a caching bug.
InfostatesAndActions GetExploitabilityDescentBestResponses() {
  return InfostatesAndActions(
      {{"0b", 0}, {"0p", 0}, {"1b", 1}, {"1p", 1}, {"2b", 1}, {"2p", 1}});
}

void KuhnPokerExploitabilityDescentIteration4BestResponsePid0() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  CheckBestResponseAgainstGoldenPolicy(*game, /*best_responder=*/Player{1},
                                       GetKuhnEdIter4Policy(),
                                       GetExploitabilityDescentBestResponses());
}

void KuhnPokerUniformBestResponseAfterSwitchingPolicies() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetKuhnEdIter4Policy();
  TabularBestResponse response(*game, Player{1}, &policy);

  // Check that it's good
  InfostatesAndActions ed_golden_actions =
      GetExploitabilityDescentBestResponses();
  std::unordered_map<std::string, Action> best_responses =
      response.GetBestResponseActions();
  CheckBestResponsesAgaintGoldenResponses(ed_golden_actions, best_responses);

  // Swap policies, and check again.
  policy = GetUniformPolicy(*game);
  response.SetPolicy(&policy);

  // Check that this equals
  InfostatesAndActions actual_best_responses = GetKuhnUniformBestResponsePid1();
  best_responses = response.GetBestResponseActions();
  CheckBestResponsesAgaintGoldenResponses(actual_best_responses,
                                          best_responses);
}

// The best response values are taken from the existing Python implementation in
// open_spiel/algorithms/exploitability.py.
void KuhnPokerOptimalBestResponsePid0() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = kuhn_poker::GetOptimalPolicy(/*alpha=*/0.2);
  InfostatesAndActions actual_best_responses = {
      {"0", 0}, {"0pb", 0}, {"1", 0}, {"1pb", 0}, {"2", 0}, {"2pb", 1}};
  CheckBestResponseAgainstGoldenPolicy(*game, /*best_responder=*/Player{0},
                                       policy, actual_best_responses);
}

// The best response values are taken from the existing Python implementation in
// open_spiel/algorithms/exploitability.py.
void KuhnPokerOptimalBestResponsePid1() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = kuhn_poker::GetOptimalPolicy(/*alpha=*/0.2);
  InfostatesAndActions actual_best_responses = {
      {"0b", 0}, {"0p", 0}, {"1p", 0}, {"1b", 0}, {"2p", 1}, {"2b", 1}};
  CheckBestResponseAgainstGoldenPolicy(*game, /*best_responder=*/Player{1},
                                       policy, actual_best_responses);
}

void KuhnPokerFirstActionBestResponsePid0() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetFirstActionPolicy(*game);
  InfostatesAndActions actual_best_responses = {
      {"0pb", 0}, {"1", 1}, {"2", 0}, {"0", 1}, {"1pb", 0}, {"2pb", 0}};
  CheckBestResponseAgainstGoldenPolicy(*game, /*best_responder=*/Player{0},
                                       policy, actual_best_responses);
}

void KuhnPokerFirstActionBestResponsePid1() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetFirstActionPolicy(*game);
  InfostatesAndActions actual_best_responses = {
      {"1p", 1}, {"2p", 0}, {"0p", 1}, {"1b", 0}, {"2b", 0}, {"0b", 0}};
  CheckBestResponseAgainstGoldenPolicy(*game, /*best_responder=*/Player{1},
                                       policy, actual_best_responses);
}

void KuhnPokerExploitabilityDescentMinimalSimulationPid0() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  auto best_responder = Player{1};

  // We create a best responder with one policy...
  TabularPolicy kuhn_ed_iter1_policy = GetKuhnEdIter1Policy();
  TabularBestResponse best_response(*game, best_responder,
                                    &kuhn_ed_iter1_policy);

  // Calculate all the best responses...
  best_response.Value(*game->NewInitialState());

  // And then set a new policy. This *shouldn't* change the result- it should
  // produce the same result as in the test above which does this calculation
  // with best_response initialized with the GetKuhnEdIter4Policy, but due to
  // improperly resetting the caches, that was not the case previously.
  TabularPolicy kuhn_ed_iter4_policy = GetKuhnEdIter4Policy();
  best_response.SetPolicy(&kuhn_ed_iter4_policy);
  best_response.Value(*game->NewInitialState());
  auto best_responses = best_response.GetBestResponseActions();
  auto actual_best_responses = GetExploitabilityDescentBestResponses();
  SPIEL_CHECK_EQ(best_responses.size(), actual_best_responses.size());
  for (const auto& infostate_and_action : actual_best_responses) {
    const std::string& infostate = infostate_and_action.first;
    Action action = infostate_and_action.second;
    auto it = best_responses.find(infostate);
    if (it == best_responses.end())
      SpielFatalError(absl::StrCat("Infostate ", infostate,
                                   " not found in best_responses."));
    if (it->second != action) {
      SpielFatalError(absl::StrCat(
          "Wrong best response at infostate ", infostate, "; expected ", action,
          " but received ", best_responses[infostate]));
    }
  }
}

void CheckBestResponseValuesAgainstGoldenValues(
    const Game& game, Player best_responder, const TabularPolicy& policy,
    const std::vector<std::pair<std::string, double>>& golden_values) {
  TabularBestResponse best_response(game, best_responder, &policy);
  for (const auto& history_and_value : golden_values) {
    const std::string& history = history_and_value.first;
    if (!Near(best_response.Value(history), history_and_value.second)) {
      SpielFatalError(absl::StrCat("Value calculated for history '", history,
                                   "' is equal to ",
                                   best_response.Value(history), " but ",
                                   history_and_value.second, " was expected."));
    }
  }
}

void KuhnPokerUniformValueTestPid0() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetUniformPolicy(*game);
  std::vector<std::pair<std::string, double>> histories_and_values =
      GetKuhnUniformBestResponseValuesPid0();
  CheckBestResponseValuesAgainstGoldenValues(
      *game, /*best_responder=*/Player{0}, policy, histories_and_values);
}

void KuhnPokerUniformValueTestPid1() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetUniformPolicy(*game);
  std::vector<std::pair<std::string, double>> histories_and_values =
      GetKuhnUniformBestResponseValuesPid1();
  CheckBestResponseValuesAgainstGoldenValues(
      *game, /*best_responder=*/Player{1}, policy, histories_and_values);
}

void KuhnPokerEFGUniformValueTestPid1() {
  std::shared_ptr<const Game> game = efg_game::LoadEFGGame(
      efg_game::GetKuhnPokerEFGData());
  TabularPolicy policy = GetUniformPolicy(*game);
  std::vector<std::pair<std::string, double>> histories_and_values =
      GetKuhnUniformBestResponseValuesPid1();
  TabularBestResponse best_response(*game, 1, &policy);
  const double value = best_response.Value(*game->NewInitialState());
  SPIEL_CHECK_TRUE(Near(value, histories_and_values[0].second));
}

void KuhnPokerOptimalValueTestPid0() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = kuhn_poker::GetOptimalPolicy(/*alpha=*/0.2);
  std::vector<std::pair<std::string, double>> histories_and_values =
      GetKuhnOptimalBestResponseValuesPid0();
  CheckBestResponseValuesAgainstGoldenValues(
      *game, /*best_responder=*/Player{0}, policy, histories_and_values);
}

void KuhnPokerOptimalValueTestPid1() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = kuhn_poker::GetOptimalPolicy(/*alpha=*/0.2);
  std::vector<std::pair<std::string, double>> histories_and_values =
      GetKuhnOptimalBestResponseValuesPid1();
  CheckBestResponseValuesAgainstGoldenValues(
      *game, /*best_responder=*/Player{1}, policy, histories_and_values);
}

}  // namespace
}  // namespace algorithms
}  // namespace open_spiel

int main(int argc, char** argv) {
  open_spiel::algorithms::KuhnPokerUniformBestResponsePid0();
  open_spiel::algorithms::KuhnPokerUniformBestResponsePid1();
  open_spiel::algorithms::KuhnPokerOptimalBestResponsePid0();
  open_spiel::algorithms::KuhnPokerOptimalBestResponsePid1();
  open_spiel::algorithms::
      KuhnPokerExploitabilityDescentIteration4BestResponsePid0();
  open_spiel::algorithms::KuhnPokerFirstActionBestResponsePid0();
  open_spiel::algorithms::KuhnPokerFirstActionBestResponsePid1();
  open_spiel::algorithms::KuhnPokerExploitabilityDescentMinimalSimulationPid0();
  open_spiel::algorithms::KuhnPokerUniformValueTestPid0();
  open_spiel::algorithms::KuhnPokerUniformValueTestPid1();
  open_spiel::algorithms::KuhnPokerEFGUniformValueTestPid1();
  open_spiel::algorithms::KuhnPokerOptimalValueTestPid0();
  open_spiel::algorithms::KuhnPokerOptimalValueTestPid1();

  // Verifies that the code automatically generates the best response actions
  // after swapping policies.
  open_spiel::algorithms::KuhnPokerUniformBestResponseAfterSwitchingPolicies();
}
