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

#include "open_spiel/game_parameters.h"

#include <list>
#include <map>
#include <regex>
#include <string>
#include <utility>

#include "open_spiel/abseil-cpp/absl/strings/str_cat.h"
#include "open_spiel/abseil-cpp/absl/strings/str_split.h"
#include "open_spiel/spiel_utils.h"

namespace open_spiel {

std::string GameParameter::ToReprString() const {
  switch (type_) {
    case Type::kInt:
      return absl::StrCat("GameParameter(int_value=", int_value(), ")");
    case Type::kDouble:
      return absl::StrCat("GameParameter(double_value=", double_value(), ")");
    case Type::kString:
      return absl::StrCat("GameParameter(string_value='", string_value(), "')");
    case Type::kBool:
      return absl::StrCat(
          "GameParameter(bool_value=", bool_value() ? "True" : "False", ")");
    case Type::kUnset:
      return absl::StrCat("GameParameter()");
    case Type::kGame:
      return absl::StrCat("GameParameter(game_value=",
                          GameParametersToString(game_value()));
    default:
      SpielFatalError("Unknown type.");
      return "This will never return.";
  }
}

std::string GameParameter::ToString() const {
  switch (type_) {
    case Type::kInt:
      return absl::StrCat(int_value());
    case Type::kDouble:
      return absl::StrCat(double_value());
    case Type::kString:
      return string_value();
    case Type::kBool:
      return bool_value() ? std::string("True") : std::string("False");
    case Type::kUnset:
      return absl::StrCat("unset");
    case Type::kGame:
      return GameParametersToString(game_value());
    default:
      SpielFatalError("Unknown type.");
      return "This will never return.";
  }
}

std::string GameParameter::Serialize(const std::string& delimiter) const {
  std::string val;
  switch (type_) {
    case Type::kString:
      val = std::regex_replace(ToString(), std::regex("\\n"), "\2");
      break;
    case Type::kGame:
      val = SerializeGameParameters(game_value());
      break;
    default:
      val = ToString();
  }
  return absl::StrCat(GameParameterTypeToString(type_), delimiter, val, 
                      delimiter, is_mandatory() ?  "true" : "false");
}

GameParameter DeserializeGameParameter(const std::string& data,
                                       const std::string& delimiter) {
  std::vector<std::string> parts = absl::StrSplit(data, delimiter);
  SPIEL_CHECK_EQ(parts.size(), 3);
  bool mandatory = (parts[2] == "True" || parts[2] == "true");
  if (parts[0] == "kUnset") {
    return GameParameter(GameParameter::Type::kUnset, mandatory);
  } else if (parts[0] == "kInt") {
    int value;
    SPIEL_CHECK_TRUE(absl::SimpleAtoi(parts[1], &value));
    return GameParameter(value, mandatory);
  } else if (parts[0] == "kDouble") {
    double value;
    SPIEL_CHECK_TRUE(absl::SimpleAtod(parts[1], &value));
    return GameParameter(value, mandatory);
  } else if (parts[0] == "kString") {
    return GameParameter(std::regex_replace(parts[1], std::regex("\2"), "\n"), 
                         mandatory);
  } else if (parts[0] == "kBool") {
    return GameParameter(parts[1] == "True" || parts[1] == "true", mandatory);
  } else if (parts[0] == "kGame") {
    return GameParameter(DeserializeGameParameters(parts[1]), mandatory);
  } else {
    SpielFatalError(absl::StrCat("Unrecognized type: ", parts[0]));
  }
}

std::string SerializeGameParameters(const GameParameters& game_params,
                                    const std::string& name_delimiter,
                                    const std::string& parameter_delimeter) {
  std::list<std::string> serialized_params;

  for (const auto& key_val : game_params) {
    std::string name = key_val.first;
    GameParameter parameter = key_val.second;

    serialized_params.push_back(absl::StrCat(name,
                                             name_delimiter,
                                             parameter.Serialize())); 
  }

  return absl::StrJoin(serialized_params, parameter_delimeter);
}

GameParameters DeserializeGameParameters(const std::string& data,
                                         const std::string& name_delimiter,
                                         const std::string& parameter_delimeter)
{
  GameParameters game_params;
  std::vector<std::string> parts = absl::StrSplit(data, parameter_delimeter);

  for (const auto& part : parts) {
    if (!part.empty()) {
      std::pair<std::string, std::string> pair = absl::StrSplit(part, 
                                                                name_delimiter);
      game_params.insert(
        std::pair<std::string, GameParameter>(
          pair.first, DeserializeGameParameter(pair.second))
      );
    }
  }
  return game_params;
}

inline std::string GameParametersToString(const GameParameters& game_params) {
  std::string str;
  if (game_params.count("name")) str = game_params.at("name").string_value();
  str.push_back('(');
  bool first = true;
  for (const auto& key_val : game_params) {
    if (key_val.first != "name") {
      if (!first) str.push_back(',');
      str.append(key_val.first);
      str.append("=");
      str.append(key_val.second.ToString());
      first = false;
    }
  }
  str.push_back(')');
  return str;
}

GameParameter GameParameterFromString(const std::string& str) {
  if (str == "True" || str == "true")
    return GameParameter(true);
  else if (str == "False" || str == "false")
    return GameParameter(false);
  else if (str.find_first_not_of("+-0123456789") == std::string::npos)
    return GameParameter(stoi(str));
  else if (str.find_first_not_of("+-0123456789.") == std::string::npos)
    return GameParameter(stod(str));
  else if (str.back() == ')')
    return GameParameter(GameParametersFromString(str));
  else
    return GameParameter(str);
}

GameParameters GameParametersFromString(const std::string& game_string) {
  GameParameters params;
  int first_paren = game_string.find('(');
  if (first_paren == std::string::npos) {
    params["name"] = GameParameter(game_string);
    return params;
  }
  params["name"] = GameParameter(game_string.substr(0, first_paren));
  int start = first_paren + 1;
  int parens = 1;
  int equals = -1;
  for (int i = start; i < game_string.length(); ++i) {
    if (game_string[i] == '(') {
      ++parens;
    } else if (game_string[i] == ')') {
      --parens;
    } else if (game_string[i] == '=' && parens == 1) {
      equals = i;
    }
    if ((game_string[i] == ',' && parens == 1) ||
        (game_string[i] == ')' && parens == 0 && i > start + 1)) {
      params[game_string.substr(start, equals - start)] =
          GameParameterFromString(
              game_string.substr(equals + 1, i - equals - 1));
      start = i + 1;
      equals = -1;
    }
  }
  return params;
}

std::string GameParameterTypeToString(const GameParameter::Type& type) {
  switch (type) {
    case GameParameter::Type::kUnset:
      return "kUnset";
    case GameParameter::Type::kInt:
      return "kInt";
    case GameParameter::Type::kDouble:
      return "kDouble";
    case GameParameter::Type::kString:
      return "kString";
    case GameParameter::Type::kBool:
      return "kBool";
    case GameParameter::Type::kGame:
      return "kGame";
    default:
      SpielFatalError("Invalid GameParameter");
  }
}

}  // namespace open_spiel
