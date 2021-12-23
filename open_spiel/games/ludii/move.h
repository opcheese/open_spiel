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

#ifndef OPEN_SPIEL_GAMES_LUDII_MOVE_H_
#define OPEN_SPIEL_GAMES_LUDII_MOVE_H_

#include <string>
#include <vector>

#include "jni.h"  // NOLINT

namespace open_spiel {
namespace ludii {

class Move {
 public:
  Move(JNIEnv *env, jobject move);

  jobject GetObj() const;

 private:
  JNIEnv *env;
  jobject move;
};

}  // namespace ludii
}  // namespace open_spiel

#endif  // OPEN_SPIEL_GAMES_LUDII_MOVE_H_
