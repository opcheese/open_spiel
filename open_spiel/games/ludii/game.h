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

#ifndef THIRD_PARTY_OPEN_SPIEL_GAMES_LUDII_GAME_H_
#define THIRD_PARTY_OPEN_SPIEL_GAMES_LUDII_GAME_H_

#include <string>

#include "jni.h"  // NOLINT
#include "open_spiel/games/ludii/mode.h"
#include "open_spiel/games/ludii/move.h"
#include "open_spiel/games/ludii/moves.h"

namespace open_spiel {
namespace ludii {

class Context;

class Game {
 public:
  Game(JNIEnv *env, jobject game, std::string game_path);

  std::string GetPath() const;

  jobject GetObj() const;

  void Create(int viewSize) const;

  std::string GetName() const;

  int StateFlags() const;

  Mode GetMode() const;

  void Start(Context context) const;

  Moves GetMoves(Context context) const;

  Move Apply(Context context, Move move) const;

 private:
  JNIEnv *env;
  jobject game;
  std::string game_path;
};

}  // namespace ludii
}  // namespace open_spiel

#endif  // THIRD_PARTY_OPEN_SPIEL_GAMES_LUDII_
