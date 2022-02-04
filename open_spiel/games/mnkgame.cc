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

#include "open_spiel/games/mnkgame.h"

#include <algorithm>
#include <memory>
#include <utility>
#include <vector>

#include "open_spiel/spiel_utils.h"
#include "open_spiel/utils/tensor_view.h"

namespace open_spiel
{
  namespace mnkgame
  {
    namespace
    {

      // Facts about the game.
      const GameType kGameType{
          /*short_name=*/"mnkgame",
          /*long_name=*/"mnkgame",
          GameType::Dynamics::kSequential,
          GameType::ChanceMode::kDeterministic,
          GameType::Information::kPerfectInformation,
          GameType::Utility::kZeroSum,
          GameType::RewardModel::kTerminal,
          /*max_num_players=*/2,
          /*min_num_players=*/2,
          /*provides_information_state_string=*/true,
          /*provides_information_state_tensor=*/false,
          /*provides_observation_string=*/true,
          /*provides_observation_tensor=*/true,
          /*parameter_specification=*/
          {
              {"m", GameParameter(GameParameter::Type::kInt)},
     
              {"n",
              GameParameter(GameParameter::Type::kInt)},
              {"k", GameParameter(GameParameter::Type::kInt)},
          } 
      };

      std::shared_ptr<const Game> Factory(const GameParameters &params)
      {
        return std::shared_ptr<const Game>(new NewgameGame(params));
      }

      REGISTER_SPIEL_GAME(kGameType, Factory);

    } // namespace

    CellState PlayerToState(Player player)
    {
      switch (player)
      {
      case 0:
        return CellState::kCross;
      case 1:
        return CellState::kNought;
      default:
        SpielFatalError(absl::StrCat("Invalid player id ", player));
        return CellState::kEmpty;
      }
    }

    std::string StateToString(CellState state)
    {
      switch (state)
      {
      case CellState::kEmpty:
        return ".";
      case CellState::kNought:
        return "o";
      case CellState::kCross:
        return "x";
      default:
        SpielFatalError("Unknown state.");
      }
    }

    void NewgameState::DoApplyAction(Action move)
    {
      SPIEL_CHECK_EQ(board_[move], CellState::kEmpty);
      board_[move] = PlayerToState(CurrentPlayer());
      if (HasLine(current_player_))
      {
        outcome_ = current_player_;
      }
      current_player_ = 1 - current_player_;
      num_moves_ += 1;
    }

    std::vector<Action> NewgameState::LegalActions() const
    {
      if (IsTerminal())
        return {};
      // Can move in any empty cell.
      std::vector<Action> moves;
      for (int cell = 0; cell < kNumCells; ++cell)
      {
        if (board_[cell] == CellState::kEmpty)
        {
          moves.push_back(cell);
        }
      }
      return moves;
    }

    std::string NewgameState::ActionToString(Player player,
                                             Action action_id) const
    {
      return absl::StrCat(StateToString(PlayerToState(player)), "(",
                          action_id / kNumCols, ",", action_id % kNumCols, ")");
    }

    void NewgameState::SetState(int cur_player, const std::vector<CellState> &board)
    {
      current_player_ = cur_player;
      board_ = board;
      SPIEL_CHECK_EQ(kNumCols * kNumRows, board_.size());
    }

    void NewgameState::SetStateFromString(int cur_player,  const  std::string& boardString)
    {
      current_player_ = cur_player;
      //board_ =  std::vector<CellState>(kNumRows*kNumCols, CellState::kEmpty);
      int i = -1;
      //std::cout << "1111"<< std::endl;  

      for (char const &c: boardString) 
      {
         i++;
         if (c == 'x')
         {
          board_[i] =  CellState::kCross;
         } 
         else 
         {
           if (c == 'o')
           {
             board_[i] =  CellState::kNought;
           }
           else
           {
             board_[i] =  CellState::kEmpty;
           }
         }
      }
      //std::cout << "9999"<< std::endl;  
    
      SPIEL_CHECK_EQ(kNumCols * kNumRows, board_.size());
      //std::cout << "9999"<< std::endl;  
    }


    bool NewgameState::HasLine(Player player) const
    {
      //std::cout << "plaery "<< player << std::endl;

      CellState c = PlayerToState(player);
      // return (board_[0] == c && board_[1] == c && board_[2] == c) ||
      //        (board_[3] == c && board_[4] == c && board_[5] == c) ||
      //        (board_[6] == c && board_[7] == c && board_[8] == c) ||
      //        (board_[0] == c && board_[3] == c && board_[6] == c) ||
      //        (board_[1] == c && board_[4] == c && board_[7] == c) ||
      //        (board_[2] == c && board_[5] == c && board_[8] == c) ||
      //        (board_[0] == c && board_[4] == c && board_[8] == c) ||
      //        (board_[2] == c && board_[4] == c && board_[6] == c);
      // int cou = 0;
      // bool found = false;
      // for (int i = 0; i < kNumCells; ++i) {
      //   if (i%kNumCols==0) cou =0;
      //   int coord = i;
      //   if (board_[coord] == c) cou++; else cou = 0;
      //   if (cou >= kWin) {
      //     found = true;
      //     break;
      //   }
      // }
      // if (found) return true;

      // for (int i = 0; i < kNumCells; ++i) {
      //   if (i%kNumRows==0) cou =0;
      //   int coord = (i%kNumRows)*kNumRows+i/kNumRows;
      //   if (board_[coord] == c) cou++; else cou = 0;
      //   if (cou >= kWin) {
      //     found = true;
      //     break;
      //   }
      // }
      //std::cout << "here1 " << kNumCells << std::endl;

      std::vector<short>  mainDiagWin((int)kNumCells,0);
      //std::cout << "here1 " << kNumCells << std::endl;

      std::vector<short>  secondDiagWin((int)kNumCells,0);
      //std::cout << "here1 " << std::endl;


      std::vector<short>  rowWin((int)kNumCells,0);
      //std::cout << "here1 " << kNumCells << std::endl;
      
      std::vector<short>  colWin((int)kNumCells,0);
      //std::cout << "here1 " << kNumCells << std::endl;



      bool found = false;

      for (int i = 0; i < kNumCells; ++i)
      {
        if (board_[i] == c)
        {
          uint curCol = i % kNumRows;
          //rows
          if (i % kNumCols > 0 && i > 0)
          {
            rowWin[i] += rowWin[i - 1] + 1;
          }
          else
          {
            //newlines
            rowWin[i] = 1;
          }

          if (rowWin[i] >= kWin)
          {
            //std::cout << "row win\n"<< i << std::endl;

            found = true;
            break;
          }
          //cols
          if (i > kNumCols)
          {
            colWin[i] += colWin[i - kNumCols] + 1;
          }
          else
          {
            colWin[i] = 1;
          }

          if (colWin[i] >= kWin)
          {
            //std::cout << "Col win"<< i << std::endl;

            found = true;
            break;
          }

          //main diag
          if (i > kNumCols + 1 && curCol > 0)
          {
            mainDiagWin[i] += mainDiagWin[i - kNumCols - 1] + 1;
          }
          else
          {
            mainDiagWin[i] = 1;
          }
          if (mainDiagWin[i] >= kWin)
          {
            //std::cout << "main win" << i << std::endl;

            found = true;
            break;
          }
          //secondary diag
          if (i > kNumCols && curCol != (kNumCols - 1))
          {
            secondDiagWin[i] += secondDiagWin[i - kNumCols + 1] + 1;
          }
          else
          {
            secondDiagWin[i] = 1;
          }
          if (secondDiagWin[i] >= kWin)
          {
            //std::cout << "second win" << i << std::endl;

            found = true;
            break;
          }
        }
        else
        {
          rowWin[i] = 0;
          colWin[i] = 0;
          mainDiagWin[i] = 0;
          secondDiagWin[i] = 0;
        }
      }

      return found;
    }

    bool NewgameState::IsFull() const { return num_moves_ == kNumCells; }

    NewgameState::NewgameState(std::shared_ptr<const Game> game, int m, int n, int k) : State(game)
    {
      kNumRows = m;
      kNumCols = n;
      kWin = k;
      board_ =  std::vector<CellState>(m*n, CellState::kEmpty);
      kNumCells = m*n;
      //std::fill(begin(board_), end(board_), CellState::kEmpty);
     
    }

    std::string NewgameState::ToString() const
    {
      std::string str;
      for (int r = 0; r < kNumRows; ++r)
      {
        for (int c = 0; c < kNumCols; ++c)
        {
          absl::StrAppend(&str, StateToString(BoardAt(r, c)));
        }
        if (r < (kNumRows - 1))
        {
          absl::StrAppend(&str, "\n");
        }
      }
      return str;
    }

    bool NewgameState::IsTerminal() const
    {
      return outcome_ != kInvalidPlayer || IsFull();
    }

    std::vector<double> NewgameState::Returns() const
    {
       //std::cout << "41"<< std::endl;  
      if (HasLine(Player{0}))
      {
       //std::cout << "42"<< std::endl;  

        return {1.0, -1.0};
      }
      else if (HasLine(Player{1}))
      {
       //std::cout << "3"<< std::endl;  

        return {-1.0, 1.0};
      }
      else
      {
        return {0.0, 0.0};
      }
    }

    std::string NewgameState::InformationStateString(Player player) const
    {
      SPIEL_CHECK_GE(player, 0);
      SPIEL_CHECK_LT(player, num_players_);
      return HistoryString();
    }

    std::string NewgameState::ObservationString(Player player) const
    {
      SPIEL_CHECK_GE(player, 0);
      SPIEL_CHECK_LT(player, num_players_);
      return ToString();
    }

    void NewgameState::ObservationTensor(Player player,
                                         absl::Span<float> values) const
    {
      SPIEL_CHECK_GE(player, 0);
      SPIEL_CHECK_LT(player, num_players_);

      // Treat `values` as a 2-d tensor.
      TensorView<2> view(values, {kCellStates, kNumCells}, true);
      for (int cell = 0; cell < kNumCells; ++cell)
      {
        view[{static_cast<int>(board_[cell]), cell}] = 1.0;
      }
    }

    void NewgameState::UndoAction(Player player, Action move)
    {
      board_[move] = CellState::kEmpty;
      current_player_ = player;
      outcome_ = kInvalidPlayer;
      num_moves_ -= 1;
      history_.pop_back();
      --move_number_;
    }

    std::unique_ptr<State> NewgameState::Clone() const
    {
      return std::unique_ptr<State>(new NewgameState(*this));
    }

    NewgameGame::NewgameGame(const GameParameters &params)
        : Game(kGameType, params), 
      m(ParameterValue<int>("m",15)),
      n(ParameterValue<int>("n", 15)),
      k(ParameterValue<int>("k",5)) {}

  } // namespace tic_tac_toe
} // namespace open_spiel
