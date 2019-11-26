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

#include "open_spiel/algorithms/history_tree.h"

#include <cmath>
#include <functional>
#include <iostream>
#include <unordered_set>

#include "open_spiel/algorithms/minimax.h"
#include "open_spiel/game_parameters.h"
#include "open_spiel/games/goofspiel.h"
#include "open_spiel/games/kuhn_poker.h"
#include "open_spiel/games/leduc_poker.h"
#include "open_spiel/games/liars_dice.h"
#include "open_spiel/games/tic_tac_toe.h"
#include "open_spiel/spiel.h"
#include "open_spiel/spiel_utils.h"

namespace open_spiel {
namespace algorithms {
namespace {

void TestGameTree() {
  std::vector<std::string> game_names = {"leduc_poker", "kuhn_poker",
                                         "liars_dice"};
  std::unordered_map<std::string, int> num_histories = {
      // Not sure if these are correct. Chosen to make test pass. They seem to
      // have the right order of magnitude.
      {"kuhn_poker", 58},
      {"leduc_poker", 9457},
      {"liars_dice", 294883}};

  for (const auto& game_name : game_names) {
    std::shared_ptr<const Game> game = LoadGame(game_name);
    for (Player player_id : {Player{0}, Player{1}}) {
      HistoryTree tree(game->NewInitialState(), player_id);
      if (tree.NumHistories() != num_histories[game_name]) {
        // TODO(b/126764761): Replace calls to SpielFatalError with more
        // appropriate test macros once they support logging.
        SpielFatalError(absl::StrCat(
            "In the game ", game_name,
            ", tree has wrong number of nodes: ", tree.NumHistories(), "but ",
            num_histories[game_name], "nodes were expected."));
      }

      // Check that the root is not null.
      if (tree.Root() == nullptr) {
        SpielFatalError("Root of HistoryTree is null for game: " + game_name);
      }
      for (const std::string& history : tree.GetHistories()) {
        HistoryNode* node = tree.GetByHistory(history);
        if (node == nullptr) {
          SpielFatalError(absl::StrCat("node is null for history: ", history,
                                       " in game: ", game_name));
        }
        if (node->GetState() == nullptr) {
          SpielFatalError(absl::StrCat("state is null for history: ", history,
                                       " in game: ", game_name));
        }
        if (node->GetState()->ToString() != node->GetHistory()) {
          SpielFatalError(
              "history generated by state does not match history"
              " stored in HistoryNode.");
        }
        if (history != node->GetHistory()) {
          SpielFatalError(
              "history key does not match history stored in "
              "HistoryNode.");
        }
        if (node->GetType() != StateType::kTerminal) {
          std::vector<Action> legal_actions = node->GetState()->LegalActions();
          std::vector<Action> child_actions = node->GetChildActions();
          if (legal_actions.size() != child_actions.size()) {
            SpielFatalError(absl::StrCat(
                "For state ", history, ", child actions has a different size (",
                child_actions.size(), ") than legal actions (",
                legal_actions.size(), ")."));
          }
          for (int i = 0; i < legal_actions.size(); ++i) {
            if (legal_actions[i] != child_actions[i]) {
              SpielFatalError(absl::StrCat(
                  "legal_actions[i] != child_actions[i]: ", legal_actions[i],
                  " != ", child_actions[i]));
            }
          }
        }

        if (node->GetType() != StateType::kTerminal &&
            node->NumChildren() != node->GetState()->LegalActions().size()) {
          SpielFatalError(absl::StrCat(
              "number of child nodes does not match number of legal"
              " actions in history: ",
              history, " in game: ", game_name));
        }
        if (node->GetType() == StateType::kDecision &&
            node->GetState()->CurrentPlayer() != player_id) {
          if (node->GetInfoState() !=
              node->GetState()->InformationStateString()) {
            SpielFatalError(absl::StrCat(
                "infostate generated by state does not match ",
                "infostate stored in HistoryNode for history: ", history,
                "in game: ", game_name));
          }
        } else {
          if (node->GetInfoState() !=
              node->GetState()->InformationStateString(player_id)) {
            SpielFatalError(absl::StrCat(
                "infostate generated by state does not match ",
                "infostate stored in HistoryNode for history: ", history,
                "in game: ", game_name));
          }
        }
      }
    }
  }
}

void TestInfoSetsHaveRightNumberOfGameStates() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  std::unique_ptr<State> state = game->NewInitialState();
  TabularPolicy policy = GetUniformPolicy(*game);
  auto best_responder = Player{0};
  HistoryTree tree(game->NewInitialState(), best_responder);
  auto infosets =
      GetAllInfoSets(game->NewInitialState(), best_responder, &policy, &tree);
  for (const auto& kv : infosets) {
    const std::string& infostate = kv.first;
    const std::vector<std::pair<HistoryNode*, double>>& histories = kv.second;
    int num_histories = histories.size();
    // The infostate represented by the empty string corresponds to the root
    // infoset, which only has one history associated with it.
    if (infostate.empty()) {
      if (num_histories != 1) {
        SpielFatalError(
            absl::StrCat("Wrong number of histories in infoset at root;"
                         " expected 1, but found ",
                         num_histories));
      }
    } else {
      if (num_histories != 2) {
        SpielFatalError(
            absl::StrCat("Wrong number of histories in infoset at infostate ",
                         infostate, " expected 2, but found ", num_histories));
      }
    }
  }
}

void TestGetAllInfoSetsMatchesInfoStates() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  std::unique_ptr<State> state = game->NewInitialState();
  TabularPolicy policy = GetUniformPolicy(*game);
  for (const auto& best_responder : {Player{0}, Player{1}}) {
    HistoryTree tree(game->NewInitialState(), best_responder);
    auto infosets =
        GetAllInfoSets(game->NewInitialState(), best_responder, &policy, &tree);
    for (const auto& kv : infosets) {
      const std::string& infostate = kv.first;
      for (const auto& state_and_prob : kv.second) {
        HistoryNode* node = state_and_prob.first;
        if (node == nullptr) SpielFatalError("Node is null.");
        std::string node_infostate = node->GetInfoState();
        if (infostate != node_infostate) {
          SpielFatalError(
              absl::StrCat("infostate key (", infostate, ") does not match ",
                           "infostate stored in node (", node_infostate, ")."));
        }
        State* node_state = node->GetState();
        std::string state_infostate =
            node_state->InformationStateString(best_responder);
        if (node_infostate != state_infostate) {
          SpielFatalError(
              absl::StrCat("infostate stored in node (", node_infostate, ") ",
                           "does not match infostate calculated from state ",
                           "stored in node (", state_infostate, ")."));
        }
        if (node->GetType() == StateType::kDecision) {
          if (node_state->CurrentPlayer() != best_responder) {
            SpielFatalError(
                absl::StrCat("CurrentPlayer for state stored in node (",
                             node_state->CurrentPlayer(), ") does not match ",
                             "best_responder (", best_responder, ")."));
          }
        } else if (node->GetType() == StateType::kDecision) {
          if (node_state->CurrentPlayer() == best_responder) {
            SpielFatalError(absl::StrCat(
                "CurrentPlayer for state stored in node (",
                node_state->CurrentPlayer(), ") matches best_responder (",
                best_responder, ") but has type kDecision."));
          }
        }
        std::vector<Action> child_actions_vector = node->GetChildActions();
        std::unordered_set<Action> child_actions(child_actions_vector.begin(),
                                                 child_actions_vector.end());
        std::vector<Action> legal_actions_vector = node_state->LegalActions();
        std::unordered_set<Action> legal_actions(legal_actions_vector.begin(),
                                                 legal_actions_vector.end());
        for (const auto& child_action : child_actions) {
          if (legal_actions.count(child_action) == 0) {
            SpielFatalError("Child action found that's not a legal action.");
          }
        }
        for (const auto& legal_action : node_state->LegalActions()) {
          if (child_actions.count(legal_action) == 0) {
            SpielFatalError("Legal action found that's not a child action.");
          }
          std::unique_ptr<State> child = node_state->Child(legal_action);
          HistoryNode child_node = HistoryNode(Player{0}, std::move(child));
          if (node->GetType() != StateType::kChance) {
            Player child_player = child_node.GetState()->CurrentPlayer();
            if (node_state->CurrentPlayer() == child_player) {
              SpielFatalError(absl::StrCat(
                  "Child and parent have the same current player (",
                  child_player, ")."));
            }
            if (infostate == child_node.GetInfoState()) {
              SpielFatalError(
                  absl::StrCat("Child and parent have the same infostate (",
                               infostate, ")."));
            }
          }
        }
      }
    }
  }
}

void TestHistoryTreeIsSubsetOfGetAllInfoSets() {
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  std::unique_ptr<State> state = game->NewInitialState();
  TabularPolicy policy = GetUniformPolicy(*game);
  for (const auto& best_responder : {Player{0}, Player{1}}) {
    HistoryTree tree(game->NewInitialState(), best_responder);
    auto infosets =
        GetAllInfoSets(game->NewInitialState(), best_responder, &policy, &tree);
    for (const auto& history : tree.GetHistories()) {
      HistoryNode* node = tree.GetByHistory(history);
      if (node->GetState()->CurrentPlayer() == best_responder &&
          node->GetType() != StateType::kTerminal &&
          infosets.count(node->GetInfoState()) == 0) {
        SpielFatalError(absl::StrCat("Infoset ", node->GetInfoState(),
                                     " missing from GetAllInfoSets."));
      }
    }
  }
}

// This is a common test that we want to make. We want to validate the
// counter-factual probabilities produced by this implementation against the
// golden values produced by existing implementations.
// best_responder is the player from who's view the infostate strings are
// calculated from, and represents the player for whom we are calculating a
// best response as. It can be any value in the range [0, game.NumPlayers()).
void CheckCounterFactualProbs(
    const Game& game, const TabularPolicy& policy,
    const std::unordered_map<std::string, double>& histories_and_probs,
    Player best_responder) {
  HistoryTree tree(game.NewInitialState(), best_responder);

  // Infosets maps infostate strings to a list of all histories that map to that
  // same infostate, along with corresponding counter-factual reach
  // probabilities. The counter-factual reach probability of a history is
  // defined recursively:
  // - At the root, the reach probability is 1.
  // - At a chance node, you multiply the parent's reach probability by the
  //   probability of having that chance outcome.
  // - At a decision node, if the current player is the one making the decision,
  //   you multiply the reach probability by 1.
  // - If another player is making a decision, you multiply the parent's reach
  //   probability by the probability that player makes that decision (taken
  //   here from their policy).
  // Infostate strings here are assumed to be those that are returned from
  // open_spiel::State::InformationState(best_responder), which are
  // equivalent to those returned by HistoryNode::GetInfoState.
  std::unordered_map<std::string, std::vector<std::pair<HistoryNode*, double>>>
      infosets = GetAllInfoSets(game.NewInitialState(), best_responder, &policy,
                                &tree);

  // We check this for every infoset in the game.
  for (const auto& infoset : infosets) {
    for (const auto& state_and_prob : infoset.second) {
      HistoryNode* node = state_and_prob.first;
      // We only check for nodes where the best responder is playing. This is
      // because the counter-factual probability calculations assign a
      // probability of 1. to all of the best responder's actions, so by
      // checking the nodes where the best responder plays, we remove spurious
      // failures (as the probability would be wrong at a different decision
      // node iff the probability is wrong at a decision node where the best
      // responder is playing).
      if (node->GetState()->CurrentPlayer() != best_responder) continue;
      double prob = state_and_prob.second;
      auto it = histories_and_probs.find(node->GetHistory());
      if (it == histories_and_probs.end())
        SpielFatalError(absl::StrCat("Missing history: ", node->GetHistory()));
      SPIEL_CHECK_FLOAT_EQ(prob, it->second);
    }
  }
}

// Verifies that GetAllInfoSets returns the correct counter-factual
// probabilities when calculating a best-response as player 0 against the
// uniform policy.
void TestGetAllInfoSetsHasRightCounterFactualProbsUniformPolicyPid0() {
  // These values come from running the existing implementation against the
  // uniform policy. The existing implementation in
  // open_spiel/python/algorithms/exploitability.py has been tested extensively
  // against multiple reference implementations that have all been verified to
  // produce the golden values referenced in the published, scientific
  // literature. Do not change these values without an extremely good reason.
  // These values are known to be correct.
  std::unordered_map<std::string, double> histories_and_probs = {
      {"0 1", 0.166666667}, {"0 1 pb", 0.083333333},
      {"0 2", 0.166666667}, {"0 2 pb", 0.083333333},
      {"1 0", 0.166666667}, {"1 0 pb", 0.083333333},
      {"1 2", 0.166666667}, {"1 2 pb", 0.083333333},
      {"2 0", 0.166666667}, {"2 0 pb", 0.083333333},
      {"2 1", 0.166666667}, {"2 1 pb", 0.083333333}};
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetUniformPolicy(*game);
  CheckCounterFactualProbs(*game, policy, histories_and_probs,
                           /*best_responder=*/Player{0});
}

// Verifies that GetAllInfoSets returns the correct counter-factual
// probabilities when calculating a best-response as player 1 against the
// uniform policy.
void TestGetAllInfoSetsHasRightCounterFactualProbsUniformPolicyPid1() {
  // These values come from running the existing implementation against the
  // uniform policy.
  std::unordered_map<std::string, double> histories_and_probs = {
      {"0 1 p", 0.083333333}, {"0 1 b", 0.083333333}, {"0 2 p", 0.083333333},
      {"0 2 b", 0.083333333}, {"1 0 p", 0.083333333}, {"1 0 b", 0.083333333},
      {"1 2 p", 0.083333333}, {"1 2 b", 0.083333333}, {"2 0 p", 0.083333333},
      {"2 0 b", 0.083333333}, {"2 1 p", 0.083333333}, {"2 1 b", 0.083333333}};
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetUniformPolicy(*game);
  CheckCounterFactualProbs(*game, policy, histories_and_probs,
                           /*best_responder=*/Player{1});
}

// Verifies that GetAllInfoSets returns the correct counter-factual
// probabilities when calculating a best-response as player 0 against the
// AlwaysFold policy.
void TestGetAllInfoSetsHasRightCounterFactualProbsAlwaysFoldPid0() {
  // These values come from running the existing implementation against the
  // AlwaysFold policy.
  std::unordered_map<std::string, double> histories_and_probs = {
      {"0 1", 0.166666667}, {"0 1 pb", 0.000000000},
      {"0 2", 0.166666667}, {"0 2 pb", 0.000000000},
      {"1 0", 0.166666667}, {"1 0 pb", 0.000000000},
      {"1 2", 0.166666667}, {"1 2 pb", 0.000000000},
      {"2 0", 0.166666667}, {"2 0 pb", 0.000000000},
      {"2 1", 0.166666667}, {"2 1 pb", 0.000000000}};
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetFirstActionPolicy(*game);
  CheckCounterFactualProbs(*game, policy, histories_and_probs,
                           /*best_responder=*/Player{0});
}

// Verifies that GetAllInfoSets returns the correct counter-factual
// probabilities when calculating a best-response as player 1 against the
// AlwaysFold policy.
void TestGetAllInfoSetsHasRightCounterFactualProbsAlwaysFoldPid1() {
  // These values come from running the existing implementation against the
  // AlwaysFold policy.
  std::unordered_map<std::string, double> histories_and_probs = {
      {"0 1 p", 0.166666667}, {"0 1 b", 0.000000000}, {"0 2 p", 0.166666667},
      {"0 2 b", 0.000000000}, {"1 0 p", 0.166666667}, {"1 0 b", 0.000000000},
      {"1 2 p", 0.166666667}, {"1 2 b", 0.000000000}, {"2 0 p", 0.166666667},
      {"2 0 b", 0.000000000}, {"2 1 p", 0.166666667}, {"2 1 b", 0.000000000}};
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetFirstActionPolicy(*game);
  CheckCounterFactualProbs(*game, policy, histories_and_probs,
                           /*best_responder=*/Player{1});
}

// The optimal Kuhn policy is taken directly from the Python implementation in
// open_spiel/python/algorithms/exploitability_test.py. In it, the player bets
// with probability alpha with the jack.
TabularPolicy GetOptimalKuhnPolicy(double alpha) {
  double three_alpha = 3 * alpha;
  std::unordered_map<std::string, ActionsAndProbs> policy_table;
  // Player 0
  policy_table["0"] = {{0, 1 - alpha}, {1, alpha}};
  policy_table["0pb"] = {{0, 1}, {1, 0}};
  policy_table["1"] = {{0, 1}, {1, 0}};
  policy_table["1pb"] = {{0, 2. / 3. - alpha}, {1, 1. / 3. + alpha}};
  policy_table["2"] = {{0, 1 - three_alpha}, {1, three_alpha}};
  policy_table["2pb"] = {{0, 0}, {1, 1}};

  // Player 1
  policy_table["0p"] = {{0, 2. / 3.}, {1, 1. / 3.}};
  policy_table["0b"] = {{0, 1}, {1, 0}};
  policy_table["1p"] = {{0, 1}, {1, 0}};
  policy_table["1b"] = {{0, 2. / 3.}, {1, 1. / 3.}};
  policy_table["2p"] = {{0, 0}, {1, 1}};
  policy_table["2b"] = {{0, 0}, {1, 1}};
  return TabularPolicy(policy_table);
}

// Verifies that GetAllInfoSets returns the correct counter-factual
// probabilities when calculating a best-response as player 0 against the
// optimal policy for Kuhn policy.
void TestGetAllInfoSetsHasRightCounterFactualProbsOptimalPid0() {
  // These values come from running the existing implementation against the
  // Optimal policy for Kuhn with alpha = 0.2.
  std::unordered_map<std::string, double> histories_and_probs = {
      {"0 1", 0.166666667}, {"0 1 pb", 0.000000000},
      {"0 2", 0.166666667}, {"0 2 pb", 0.166666667},
      {"1 0", 0.166666667}, {"1 0 pb", 0.055555556},
      {"1 2", 0.166666667}, {"1 2 pb", 0.166666667},
      {"2 0", 0.166666667}, {"2 0 pb", 0.055555556},
      {"2 1", 0.166666667}, {"2 1 pb", 0.000000000}};
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetOptimalKuhnPolicy(/*alpha=*/0.2);
  CheckCounterFactualProbs(*game, policy, histories_and_probs,
                           /*best_responder=*/Player{0});
}

// Verifies that GetAllInfoSets returns the correct counter-factual
// probabilities when calculating a best-response as player 1 against the
// optimal policy for Kuhn policy.
void TestGetAllInfoSetsHasRightCounterFactualProbsOptimalPid1() {
  // These values come from running the existing implementation against the
  // Optimal policy for Kuhn with alpha = 0.2.
  std::unordered_map<std::string, double> histories_and_probs = {
      {"0 1 p", 0.133333333}, {"0 1 b", 0.033333333}, {"0 2 p", 0.133333333},
      {"0 2 b", 0.033333333}, {"1 0 p", 0.166666667}, {"1 0 b", 0.000000000},
      {"1 2 p", 0.166666667}, {"1 2 b", 0.000000000}, {"2 0 p", 0.066666667},
      {"2 0 b", 0.100000000}, {"2 1 p", 0.066666667}, {"2 1 b", 0.100000000}};
  std::shared_ptr<const Game> game = LoadGame("kuhn_poker");
  TabularPolicy policy = GetOptimalKuhnPolicy(/*alpha=*/0.2);
  CheckCounterFactualProbs(*game, policy, histories_and_probs,
                           /*best_responder=*/Player{1});
}

}  // namespace
}  // namespace algorithms
}  // namespace open_spiel

int main(int argc, char** argv) {
  open_spiel::algorithms::TestGameTree();
  open_spiel::algorithms::TestInfoSetsHaveRightNumberOfGameStates();
  open_spiel::algorithms::TestGetAllInfoSetsMatchesInfoStates();
  open_spiel::algorithms::TestHistoryTreeIsSubsetOfGetAllInfoSets();
  open_spiel::algorithms::
      TestGetAllInfoSetsHasRightCounterFactualProbsUniformPolicyPid0();
  open_spiel::algorithms::
      TestGetAllInfoSetsHasRightCounterFactualProbsUniformPolicyPid1();
  open_spiel::algorithms::
      TestGetAllInfoSetsHasRightCounterFactualProbsAlwaysFoldPid0();
  open_spiel::algorithms::
      TestGetAllInfoSetsHasRightCounterFactualProbsAlwaysFoldPid1();
  open_spiel::algorithms::
      TestGetAllInfoSetsHasRightCounterFactualProbsOptimalPid0();
  open_spiel::algorithms::
      TestGetAllInfoSetsHasRightCounterFactualProbsOptimalPid1();
}
