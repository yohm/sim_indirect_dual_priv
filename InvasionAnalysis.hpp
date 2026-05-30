#ifndef INVASION_ANALYSIS_HPP
#define INVASION_ANALYSIS_HPP

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <stdexcept>
#include <vector>

#include <nlohmann/json.hpp>

struct InvasionThresholds {
  std::optional<double> bc_min;
  std::optional<double> bc_max;
};

struct CommonInvasionThresholds {
  bool stable = true;
  double bc_min = 1.0;
  std::optional<double> bc_max;
};

inline InvasionThresholds ComputeInvasionThresholds(const std::vector<std::vector<double>>& c_levels) {
  InvasionThresholds thr;
  if (c_levels.size() != 2 || c_levels[0].size() != 2 || c_levels[1].size() != 2) {
    throw std::runtime_error("ComputeInvasionThresholds expects a 2x2 matrix");
  }

  const double p_rr = c_levels[0][0];
  const double p_rm = c_levels[0][1];
  const double p_mr = c_levels[1][0];

  if (p_rr > p_rm) {
    const double bc_min = (p_rr - p_mr) / (p_rr - p_rm);
    thr.bc_min = bc_min > 1.0 ? bc_min : 1.0;
    thr.bc_max.reset();
  }
  else if (p_rr < p_rm) {
    const double bc_max = (p_rr - p_mr) / (p_rr - p_rm);
    if (bc_max > 1.0) {
      thr.bc_min = 1.0;
      thr.bc_max = bc_max;
    }
    else {
      thr.bc_min.reset();
      thr.bc_max = 1.0;
    }
  }
  else {
    if (p_rr > p_mr) {
      thr.bc_min = 1.0;
      thr.bc_max.reset();
    }
    else {
      thr.bc_min.reset();
      thr.bc_max = 1.0;
    }
  }
  return thr;
}

inline nlohmann::json InvasionThresholdsToJson(const InvasionThresholds& thresholds) {
  nlohmann::json invasion = nlohmann::json::object();
  if (thresholds.bc_min.has_value()) {
    invasion["bc_min"] = thresholds.bc_min.value();
  }
  else {
    invasion["bc_min"] = nullptr;
  }
  if (thresholds.bc_max.has_value()) {
    invasion["bc_max"] = thresholds.bc_max.value();
  }
  else {
    invasion["bc_max"] = nullptr;
  }
  return invasion;
}

inline CommonInvasionThresholds CombineInvasionThresholds(const std::vector<InvasionThresholds>& thresholds_vec) {
  CommonInvasionThresholds common;
  double upper = std::numeric_limits<double>::infinity();

  for (const auto& thresholds : thresholds_vec) {
    if (!thresholds.bc_min.has_value()) {
      common.stable = false;
    }
    else {
      common.bc_min = std::max(common.bc_min, thresholds.bc_min.value());
    }

    if (thresholds.bc_max.has_value()) {
      upper = std::min(upper, thresholds.bc_max.value());
    }
  }

  if (std::isfinite(upper)) {
    common.bc_max = upper;
    if (common.bc_min >= upper) {
      common.stable = false;
    }
  }

  return common;
}

inline nlohmann::json CommonInvasionThresholdsToJson(const CommonInvasionThresholds& common) {
  nlohmann::json out = nlohmann::json::object();
  out["stable"] = common.stable;
  if (common.stable) {
    out["bc_min"] = common.bc_min;
    if (common.bc_max.has_value()) {
      out["bc_max"] = common.bc_max.value();
    }
    else {
      out["bc_max"] = nullptr;
    }
  }
  else {
    out["bc_min"] = nullptr;
    out["bc_max"] = nullptr;
  }
  return out;
}

#endif // INVASION_ANALYSIS_HPP
