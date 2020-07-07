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

#include "open_spiel/python/pybind11/game_transforms.h"

// Python bindings for policies and algorithms handling them.

#include "open_spiel/game_transforms/normal_form_extensive_game.h"
#include "open_spiel/game_transforms/turn_based_simultaneous_game.h"
#include "pybind11/include/pybind11/detail/common.h"
#include "pybind11/include/pybind11/detail/descr.h"
#include "pybind11/include/pybind11/functional.h"
#include "pybind11/include/pybind11/numpy.h"
#include "pybind11/include/pybind11/operators.h"
#include "pybind11/include/pybind11/pybind11.h"
#include "pybind11/include/pybind11/stl.h"

namespace open_spiel {
namespace py = ::pybind11;

void init_pyspiel_game_transforms(py::module& m) {
  m.def("load_game_as_turn_based",
        py::overload_cast<const std::string&>(&open_spiel::LoadGameAsTurnBased),
        "Converts a simultaneous game into an turn-based game with infosets.");

  m.def("load_game_as_turn_based",
        py::overload_cast<const std::string&, const GameParameters&>(
            &open_spiel::LoadGameAsTurnBased),
        "Converts a simultaneous game into an turn-based game with infosets.");

  m.def("extensive_to_tensor_game", open_spiel::ExtensiveToTensorGame,
        "Converts an extensive-game to its equivalent tensor game, "
        "which is exponentially larger. Use only with small games.");

  m.def("convert_to_turn_based", open_spiel::ConvertToTurnBased,
        "Returns a turn-based version of the given game.");
}
}  // namespace open_spiel
