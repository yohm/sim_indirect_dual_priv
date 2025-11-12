#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "EvolPrivRepGame.hpp"
#include "PrivRepGame.hpp"
#include "Norm.hpp"

struct Range {
  int start = 0;
  int end = 0;
};

struct ProgramOptions {
  Range rd{0, 255};
  Range rr{0, 255};
  Range act{0, 15};
  nlohmann::json param_overrides = nlohmann::json::object();
};

void PrintUsage(const char* exe) {
  std::cerr << "Usage: " << exe << " [options]\n";
  std::cerr << "Options:\n";
  std::cerr << "  -j <json|path>      Simulation parameters (inline JSON or file path)\n";
  std::cerr << "  --rd-range a b      Inclusive R1 (donor) ID range [0,255]\n";
  std::cerr << "  --rr-range a b      Inclusive R2 (recipient) ID range [0,255]\n";
  std::cerr << "  --act-range a b     Inclusive action rule ID range [0,15]\n";
  std::cerr << "  --help              Show this message\n";
  std::cerr << "\nParameters JSON keys (optional):\n";
  std::cerr << "  N, t_init, t_measure, q, mu_impl, mu_percept, mu_assess1, mu_assess2, seed, _seed\n";
}

int ParseBound(const std::string& value, const std::string& label) {
  try {
    return std::stoi(value);
  } catch (const std::exception&) {
    throw std::runtime_error("invalid integer for " + label + ": " + value);
  }
}

void SetRange(Range& range, int start, int end, int min_value, int max_value, const std::string& label) {
  if (start < min_value || start > max_value || end < min_value || end > max_value || start > end) {
    std::ostringstream oss;
    oss << "invalid " << label << " range [" << start << ", " << end << "]";
    throw std::runtime_error(oss.str());
  }
  range.start = start;
  range.end = end;
}

nlohmann::json LoadJsonArg(const std::string& raw) {
  std::ifstream fin(raw);
  if (fin) {
    nlohmann::json j;
    fin >> j;
    return j;
  }
  return nlohmann::json::parse(raw);
}

ProgramOptions ParseArgs(int argc, char** argv) {
  ProgramOptions opt;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--help") {
      PrintUsage(argv[0]);
      std::exit(0);
    }
    else if (arg == "-j") {
      if (i + 1 >= argc) {
        throw std::runtime_error("-j requires a value");
      }
      opt.param_overrides = LoadJsonArg(argv[++i]);
    }
    else if (arg == "--rd-range") {
      if (i + 2 >= argc) {
        throw std::runtime_error("--rd-range requires two integers");
      }
      int start = ParseBound(argv[++i], "--rd-range");
      int end = ParseBound(argv[++i], "--rd-range");
      SetRange(opt.rd, start, end, 0, 255, "R1");
    }
    else if (arg == "--rr-range") {
      if (i + 2 >= argc) {
        throw std::runtime_error("--rr-range requires two integers");
      }
      int start = ParseBound(argv[++i], "--rr-range");
      int end = ParseBound(argv[++i], "--rr-range");
      SetRange(opt.rr, start, end, 0, 255, "R2");
    }
    else if (arg == "--act-range") {
      if (i + 2 >= argc) {
        throw std::runtime_error("--act-range requires two integers");
      }
      int start = ParseBound(argv[++i], "--act-range");
      int end = ParseBound(argv[++i], "--act-range");
      SetRange(opt.act, start, end, 0, 15, "Action");
    }
    else {
      throw std::runtime_error("unknown option: " + arg);
    }
  }
  return opt;
}

EvolPrivRepGame::Parameters BuildParameters(const nlohmann::json& overrides) {
  EvolPrivRepGame::Parameters params;
  if (!overrides.is_null()) {
    if (!overrides.is_object()) {
      throw std::runtime_error("parameters JSON must be an object");
    }

    const std::vector<std::string> allowed = {
      "N", "t_init", "t_measure", "q", "mu_impl", "mu_percept", "mu_assess1", "mu_assess2", "seed", "_seed"
    };
    for (auto it = overrides.begin(); it != overrides.end(); ++it) {
      if (std::find(allowed.begin(), allowed.end(), it.key()) == allowed.end()) {
        throw std::runtime_error("unknown parameter: " + it.key());
      }
    }

    if (overrides.contains("N")) { params.N = overrides.at("N").get<size_t>(); }
    if (overrides.contains("t_init")) { params.t_init = overrides.at("t_init").get<size_t>(); }
    if (overrides.contains("t_measure")) { params.t_measure = overrides.at("t_measure").get<size_t>(); }
    if (overrides.contains("q")) { params.q = overrides.at("q").get<double>(); }
    if (overrides.contains("mu_impl")) { params.mu_impl = overrides.at("mu_impl").get<double>(); }
    if (overrides.contains("mu_percept")) { params.mu_percept = overrides.at("mu_percept").get<double>(); }
    if (overrides.contains("mu_assess1")) { params.mu_assess1 = overrides.at("mu_assess1").get<double>(); }
    if (overrides.contains("mu_assess2")) { params.mu_assess2 = overrides.at("mu_assess2").get<double>(); }
    if (overrides.contains("seed")) { params.seed = overrides.at("seed").get<uint64_t>(); }
    if (overrides.contains("_seed")) { params.seed = overrides.at("_seed").get<uint64_t>(); }
  }
  if (params.N < 2) {
    throw std::runtime_error("population size N must be >= 2");
  }
  if (params.t_measure == 0) {
    throw std::runtime_error("t_measure must be > 0");
  }
  return params;
}

std::vector<int> ExpandRange(const Range& range) {
  std::vector<int> ids;
  ids.reserve(static_cast<size_t>(range.end - range.start + 1));
  for (int id = range.start; id <= range.end; ++id) {
    ids.push_back(id);
  }
  return ids;
}

std::vector<std::vector<double>> RunPrivRepSimulation(const PrivateRepGame::population_t& pop,
                                                      const EvolPrivRepGame::Parameters& base_params,
                                                      uint64_t seed_offset) {
  size_t total = 0;
  for (const auto& kv : pop) {
    total += kv.second;
  }
  if (total != base_params.N) {
    throw std::runtime_error("population size mismatch with parameters.N");
  }

  EvolPrivRepGame::Parameters params = base_params;
  params.seed += seed_offset;

  PrivateRepGame game(pop, params.seed);
  game.Update(params.t_init, params.q, params.mu_impl, params.mu_percept, params.mu_assess1, params.mu_assess2, false);
  game.ResetCounts();
  game.Update(params.t_measure, params.q, params.mu_impl, params.mu_percept, params.mu_assess1, params.mu_assess2, false);
  return game.NormCooperationLevels();
}

std::optional<double> ComputeBcMin(const std::vector<std::vector<double>>& c_levels) {
  if (c_levels.size() != 2 || c_levels[0].size() != 2 || c_levels[1].size() != 2) {
    throw std::runtime_error("ComputeBcMin expects a 2x2 cooperation matrix");
  }
  double p_rr = c_levels[0][0];
  double p_rm = c_levels[0][1];
  double p_mr = c_levels[1][0];

  if (p_rr > p_rm) {
    double bc_min = (p_rr - p_mr) / (p_rr - p_rm);
    if (bc_min > 1.0) {
      return bc_min;
    }
    return 1.0;
  }
  else if (p_rr < p_rm) {
    double bc_max = (p_rr - p_mr) / (p_rr - p_rm);
    if (bc_max > 1.0) {
      return 1.0;
    }
    return std::nullopt;
  }
  else {
    if (p_rr > p_mr) {
      return 1.0;
    }
    return std::nullopt;
  }
}

std::string FormatDouble(double value) {
  std::ostringstream oss;
  oss << std::setprecision(10) << value;
  return oss.str();
}

int main(int argc, char** argv) {
  try {
    ProgramOptions opt = ParseArgs(argc, argv);
    EvolPrivRepGame::Parameters params = BuildParameters(opt.param_overrides);
    auto rd_ids = ExpandRange(opt.rd);
    auto rr_ids = ExpandRange(opt.rr);
    auto act_ids = ExpandRange(opt.act);

    size_t total = static_cast<size_t>(rd_ids.size()) * rr_ids.size() * act_ids.size();
    std::cerr << "Sweeping " << total << " combinations "
              << "(R1: " << opt.rd.start << "-" << opt.rd.end
              << ", R2: " << opt.rr.start << "-" << opt.rr.end
              << ", Action: " << opt.act.start << "-" << opt.act.end << ")\n";

    Norm alld = Norm::AllD();
    std::cout << "#R1\tR2\tAction\tSelfCoop\tbc_min(AllD)\n";

    size_t combo_index = 0;
    for (int rd_id : rd_ids) {
      auto rd = AssessmentRule::MakeDeterministicRule(rd_id);
      for (int rr_id : rr_ids) {
        auto rr = AssessmentRule::MakeDeterministicRule(rr_id);
        for (int act_id : act_ids) {
          auto act = ActionRule::MakeDeterministicRule(act_id);
          Norm candidate(rd, rr, act);

          EvolPrivRepGame::Parameters mono_params = params;
          mono_params.seed += static_cast<uint64_t>(combo_index * 2);
          double self_coop = EvolPrivRepGame::MonomorphicCooperationLevel(candidate, mono_params);

          PrivateRepGame::population_t pop = {{candidate, params.N - 1}, {alld, 1}};
          auto c_levels = RunPrivRepSimulation(pop, params, static_cast<uint64_t>(combo_index * 2 + 1));
          auto bc_min = ComputeBcMin(c_levels);

          std::cout << rd_id << '\t'
                    << rr_id << '\t'
                    << act_id << '\t'
                    << FormatDouble(self_coop) << '\t';
          if (bc_min.has_value()) {
            std::cout << FormatDouble(bc_min.value()) << '\n';
          } else {
            std::cout << "None\n";
          }
          ++combo_index;
        }
      }
    }
  }
  catch (const std::exception& e) {
    std::cerr << "[Error] " << e.what() << std::endl;
    return 1;
  }
  return 0;
}
