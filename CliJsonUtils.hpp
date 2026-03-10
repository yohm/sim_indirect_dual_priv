#ifndef CLI_JSON_UTILS_HPP
#define CLI_JSON_UTILS_HPP

#include <fstream>
#include <initializer_list>
#include <set>
#include <stdexcept>
#include <string>

#include <nlohmann/json.hpp>
#include "CliHelpUtils.hpp"

namespace CliJsonUtils {

inline nlohmann::json LoadJsonFromFileOrString(const std::string& raw) {
  std::ifstream fin(raw);
  if (fin) {
    nlohmann::json j;
    fin >> j;
    return j;
  }
  return nlohmann::json::parse(raw);
}

inline bool ConsumeJsonOption(int argc, char** argv, int& index, const std::string& option, nlohmann::json& out_json) {
  if (std::string(argv[index]) != option) {
    return false;
  }
  if (index + 1 >= argc) {
    throw std::runtime_error(option + " requires a value");
  }
  out_json = LoadJsonFromFileOrString(argv[++index]);
  return true;
}

inline std::set<std::string> JsonKeys(const nlohmann::json& j) {
  std::set<std::string> keys;
  if (!j.is_object()) {
    return keys;
  }
  for (auto it = j.begin(); it != j.end(); ++it) {
    keys.insert(it.key());
  }
  return keys;
}

inline std::set<std::string> JsonKeysWithExtras(const nlohmann::json& j, std::initializer_list<std::string> extras = {}) {
  auto keys = JsonKeys(j);
  keys.insert(extras.begin(), extras.end());
  return keys;
}

inline void ValidateObjectKeys(const nlohmann::json& j, const std::set<std::string>& allowed_keys, const std::string& label = "parameter") {
  if (!j.is_object()) {
    throw std::runtime_error(label + " JSON must be an object");
  }
  for (auto it = j.begin(); it != j.end(); ++it) {
    if (!allowed_keys.count(it.key())) {
      throw std::runtime_error("unknown " + label + ": " + it.key());
    }
  }
}

inline void ApplyJsonDefaults(nlohmann::json& target, const nlohmann::json& defaults) {
  for (auto it = defaults.begin(); it != defaults.end(); ++it) {
    if (!target.contains(it.key())) {
      target[it.key()] = it.value();
    }
  }
}

}  // namespace CliJsonUtils

#endif
