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

#include "open_spiel/spiel.h"
#include "open_spiel/tests/basic_tests.h"
#include "open_spiel/tests/basic_tests.h"

namespace open_spiel
{
  namespace mnkgame
  {
    namespace
    {

      namespace testing = open_spiel::testing;

      void MNKLineStringTests()
      {
        std::cout << "String test:" << std::endl;  
        std::shared_ptr<const Game> game = LoadGame("mnkgame(m=3,n=3,k=3)");
        std::unique_ptr<State> state = game->NewInitialState();
        NewgameState *bstate = static_cast<NewgameState *>(state.get());
        bstate->SetStateFromString(0,"...xxxooo");
        std::string actual = bstate->ToString();
        std::string expected = "...\nxxx\nooo";
        std::cout << " Actual:" << actual << std::endl;
        int comp = expected.compare(actual);
        SPIEL_CHECK_EQ(0,comp);

      }

      void MNKLineString15Test()
      {
        std::cout << "String15 test:" << std::endl;  
        std::shared_ptr<const Game> game = LoadGame("mnkgame(m=15,n=15,k=5)");
        std::unique_ptr<State> state = game->NewInitialState();
        NewgameState *bstate = static_cast<NewgameState *>(state.get());
        //std::cout << "111"<< std::endl;  
        //std::string s("hello");
        bstate->SetStateFromString(1,"xxx.ooooo........................................................................................................................................................................................................................");
        bool actual = bstate->IsTerminal();
        SPIEL_CHECK_TRUE(!actual);
        //std::cout << "123"<< std::endl;  

        std::vector<double>  rets = bstate->Returns();
        //std::cout << "435"<< std::endl;  

        std::cout << "Rets:" << rets[0] << std::endl;  

        SPIEL_CHECK_EQ(-1,rets[0]);
        
        
      }

      void MNKLineTests()
      {
        std::cout << "Line test:" << std::endl;  
        std::shared_ptr<const Game> game = LoadGame("mnkgame(m=5,n=5,k=3)");
        std::unique_ptr<State> state = game->NewInitialState();
        NewgameState *bstate = static_cast<NewgameState *>(state.get());
        // .....
        // .ooo.
        // ..x..
        // ...x.
        // .....
        bstate->SetState(
            0,
            {CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kNought, CellState::kNought, CellState::kNought, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kCross, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kCross, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty});
        std::cout << bstate->ToString()<<std::endl;

        bool line = bstate->HasLine(1);

        SPIEL_CHECK_TRUE(line);

        state = game->NewInitialState();
        bstate = static_cast<NewgameState *>(state.get());
        //  .....
        //  .o...
        //  ..o..
        //  ...o.
        //  .....
        bstate->SetState(
            0,
            {CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kNought, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty});
        std::cout << bstate->ToString()<<std::endl;

        line = bstate->HasLine(1);

        SPIEL_CHECK_TRUE(line);

        state = game->NewInitialState();
        bstate = static_cast<NewgameState *>(state.get());
        //  .....
        //  .o...
        //  ..o..
        //  ...o.
        //  .....
        bstate->SetState(
            0,
            {CellState::kEmpty, CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty,
             CellState::kNought, CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kCross, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty});
        std::cout << bstate->ToString()<<std::endl;

        line = bstate->HasLine(1);

        SPIEL_CHECK_TRUE(line);

        state = game->NewInitialState();
        bstate = static_cast<NewgameState *>(state.get());
        //  .....
        //  .o...
        //  ..o..
        //  ...o.
        //  .....
        bstate->SetState(
            0,
            {CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty,
             CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kNought, CellState::kEmpty,
             CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty});
        std::cout << bstate->ToString()<<std::endl;

        line = bstate->HasLine(1);

        SPIEL_CHECK_TRUE(line);

        state = game->NewInitialState();
        bstate = static_cast<NewgameState *>(state.get());
        //  .....
        //  .o...
        //  ..o..
        //  ...o.
        //  .....
        bstate->SetState(
            0,
            {CellState::kEmpty, CellState::kNought, CellState::kNought, CellState::kEmpty, CellState::kNought,
             CellState::kNought, CellState::kNought, CellState::kEmpty, CellState::kEmpty, CellState::kNought,
             CellState::kEmpty, CellState::kEmpty, CellState::kNought, CellState::kEmpty, CellState::kEmpty,
             CellState::kNought, CellState::kEmpty, CellState::kEmpty, CellState::kEmpty, CellState::kNought,
             CellState::kNought, CellState::kNought, CellState::kEmpty, CellState::kEmpty, CellState::kNought});
        std::cout << bstate->ToString() << std::endl;

        line = bstate->HasLine(1);

        SPIEL_CHECK_TRUE(!line);

        // std::vector<Action> legal_actions = bstate->LegalActions();
        // std::cout << "Legal actions:" << std::endl;
        // for (Action action : legal_actions)
        // {
        //   std::cout << bstate->ActionToString(0, action) << std::endl;
        // }
        //SPIEL_CHECK_EQ(legal_actions.size(), 9);
      }

      void BasicNewgameTests()
      {
        testing::LoadGameTest("tic_tac_toe");
        testing::NoChanceOutcomesTest(*LoadGame("tic_tac_toe"));
        testing::RandomSimTest(*LoadGame("tic_tac_toe"), 100);
      }

    } // namespace
  }   // namespace tic_tac_toe
} // namespace open_spiel

int main(int argc, char **argv)
{
  open_spiel::mnkgame::BasicNewgameTests();
  open_spiel::mnkgame::MNKLineTests();
  open_spiel::mnkgame::MNKLineStringTests();
  open_spiel::mnkgame::MNKLineString15Test();
}
