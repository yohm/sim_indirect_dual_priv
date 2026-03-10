#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

#include <nlohmann/json.hpp>

#include "CliJsonUtils.hpp"
#include "Norm.hpp"
#include "PrivRepGame.hpp"
#include "EvolPrivRepGame.hpp"

constexpr int kRrStart = 0;
constexpr int kRrEnd = 255;

struct ProgramOptions {
  std::optional<std::string> params_arg;
  std::optional<std::string> out_path;
};

struct SimulationConfig {
  EvolPrivRepGame::Parameters params;
  double benefit = 5.0;
  double beta = 1.0;
  std::optional<nlohmann::json> raw_params;
};

struct SweepRow {
  int rr = 0;
  double self_coop = std::numeric_limits<double>::quiet_NaN();
  std::optional<double> bc_min;
  std::optional<double> bc_max;
  double eq_coop = std::numeric_limits<double>::quiet_NaN();
  double eq0 = std::numeric_limits<double>::quiet_NaN();
  double eq1 = std::numeric_limits<double>::quiet_NaN();
  double eq2 = std::numeric_limits<double>::quiet_NaN();
  double rho_alld_to_resident = std::numeric_limits<double>::quiet_NaN();
  double rho_resident_to_alld = std::numeric_limits<double>::quiet_NaN();
  double rho_allc_to_resident = std::numeric_limits<double>::quiet_NaN();
  double rho_resident_to_allc = std::numeric_limits<double>::quiet_NaN();
};

void PrintUsage(const char* exe) {
  std::cout << "Usage: " << exe << " [options]\n";
  std::cout << "Options:\n";
  std::cout << "  --params <json|path> Parameters JSON inline or path\n";
  std::cout << "  --out <path>         Output TSV path (default: R2_sweep.tsv)\n";
  std::cout << "  --help               Show this message\n";
  std::cout << "\nJSON parameters:\n";
  std::cout << "  base_norm            (string) required\n";
  std::cout << "  N                    (size_t) EvolPrivRepGame population size\n";
  std::cout << "  t_init               (size_t) initialization steps\n";
  std::cout << "  t_measure            (size_t) measurement steps\n";
  std::cout << "  q                    (double) observation probability\n";
  std::cout << "  mu_impl              (double) implementation error\n";
  std::cout << "  mu_percept           (double) perception error\n";
  std::cout << "  mu_assess1           (double) assessment error 1\n";
  std::cout << "  mu_assess2           (double) assessment error 2\n";
  std::cout << "  _seed                (uint64_t) RNG seed\n";
  std::cout << "  benefit              (double) benefit parameter\n";
  std::cout << "  beta                 (double) selection strength\n";
}

std::string RequireValue(int argc, char** argv, int& i, const std::string& flag) {
  if (i + 1 >= argc) {
    throw std::runtime_error("missing value for " + flag);
  }
  return std::string(argv[++i]);
}

ProgramOptions ParseArgs(int argc, char** argv) {
  if (argc <= 1) {
    PrintUsage(argv[0]);
    std::exit(0);
  }

  if (std::string(argv[1]) == "--help") {
    PrintUsage(argv[0]);
    std::exit(0);
  }

  ProgramOptions opt;

  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--help") {
      PrintUsage(argv[0]);
      std::exit(0);
    }
    else if (arg == "--params") {
      opt.params_arg = RequireValue(argc, argv, i, arg);
    }
    else if (arg == "--out") {
      opt.out_path = RequireValue(argc, argv, i, arg);
    }
    else {
      throw std::runtime_error("unknown option: " + arg);
    }
  }

  return opt;
}

SimulationConfig BuildSimulationConfig(const ProgramOptions& opt) {
  SimulationConfig cfg;
  nlohmann::json raw = nlohmann::json::object();
  if (opt.params_arg.has_value()) {
    raw = CliJsonUtils::LoadJsonFromFileOrString(opt.params_arg.value());
  }

  if (raw.is_object()) {
    CliJsonUtils::ValidateObjectKeys(raw, {"N", "t_init", "t_measure", "q", "mu_impl", "mu_percept", "mu_assess1", "mu_assess2", "_seed", "benefit", "beta", "base_norm"});
  }
  else if (!raw.is_null()) {
    throw std::runtime_error("--params must be a JSON object");
  }

  nlohmann::json for_params = raw.is_null() ? nlohmann::json::object() : raw;
  if (for_params.is_object()) {
    for_params.erase("benefit");
    for_params.erase("beta");
  }
  cfg.params = for_params.get<EvolPrivRepGame::Parameters>();
  if (raw.is_object() && raw.contains("_seed")) {
    cfg.params._seed = raw.at("_seed").get<uint64_t>();
  }

  if (cfg.params.N < 2) {
    throw std::runtime_error("population size N must be >= 2");
  }

  cfg.benefit = (raw.is_object() && raw.contains("benefit")) ? raw.at("benefit").get<double>() : 5.0;
  cfg.beta = (raw.is_object() && raw.contains("beta")) ? raw.at("beta").get<double>() : 1.0;

  if (opt.params_arg.has_value()) {
    cfg.raw_params = raw;
  }
  return cfg;
}

Norm BuildNorm(int rd_id, int rr_id, int p_id) {
  auto rd = AssessmentRule::MakeDeterministicRule(rd_id);
  auto rr = AssessmentRule::MakeDeterministicRule(rr_id);
  auto act = ActionRule::MakeDeterministicRule(p_id);
  return Norm(rd, rr, act);
}

std::vector<std::vector<double>> RunPrivRepSimulation(const PrivateRepGame::population_t& pop,
                                                      const EvolPrivRepGame::Parameters& params,
                                                      bool count_good = false,
                                                      uint64_t seed_offset = 0) {
  if (params.t_measure == 0) {
    throw std::runtime_error("t_measure must be > 0");
  }
  size_t total_size = 0;
  for (const auto& kv : pop) {
    total_size += kv.second;
  }
  if (total_size != params.N) {
    throw std::runtime_error("population size mismatch with parameters.N");
  }

  PrivateRepGame game(pop, params._seed + seed_offset);
  game.Update(params.t_init, params.q, params.mu_impl, params.mu_percept, params.mu_assess1, params.mu_assess2, count_good);
  game.ResetCounts();
  game.Update(params.t_measure, params.q, params.mu_impl, params.mu_percept, params.mu_assess1, params.mu_assess2, count_good);
  return game.NormCooperationLevels();
}

struct InvasionThresholds {
  std::optional<double> bc_min;
  std::optional<double> bc_max;
};

InvasionThresholds ComputeInvasionThresholds(const std::vector<std::vector<double>>& c_levels) {
  InvasionThresholds thr;
  if (c_levels.size() != 2 || c_levels[0].size() != 2 || c_levels[1].size() != 2) {
    throw std::runtime_error("ComputeInvasionThresholds expects a 2x2 matrix");
  }
  // Solve known invasion condition:
  //   pi_res = (b - c)(p_rr)
  //   pi_mut = b * p_rm - p_mr
  // pi_res > pi_mut  => b(p_rr - p_rm) > c(p_rr - p_mr)
  //   if p_rr > p_rm : b/c > (p_rr - p_mr)/(p_rr - p_rm)
  //   if p_rr < p_rm : b/c < (p_rr - p_mr)/(p_rr - p_rm)
  //   if p_rr == p_rm :
  //       if p_rr > p_mr : always stable
  //       if p_rr < p_mr : never stable
  // The critical ratio is (p_rr - p_mr)/(p_rr - p_rm), with special handling when numerator/denominator signs match or differ.

  double p_rr = c_levels[0][0];
  double p_rm = c_levels[0][1];
  double p_mr = c_levels[1][0];

  if (p_rr > p_rm) {
    double bc_min = (p_rr - p_mr) / (p_rr - p_rm);
    if (bc_min > 1.0) {
      thr.bc_min = bc_min;
      thr.bc_max.reset();
    }
    else {
      thr.bc_min = 1.0;
      thr.bc_max.reset();
    }
  }
  else if (p_rr < p_rm) {
    double bc_max = (p_rr - p_mr) / (p_rr - p_rm);
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

SweepRow ComputeSweepRow(int rr,
                         const Norm& candidate,
                         const EvolPrivRepGame::Parameters& params,
                         const Norm& allc,
                         const Norm& alld,
                         double benefit,
                         double beta) {
  SweepRow row;
  row.rr = rr;

  row.self_coop = EvolPrivRepGame::MonomorphicCooperationLevel(candidate, params);

  PrivateRepGame::population_t pop_alld = {{candidate, params.N - 1}, {alld, 1}};
  auto c_levels_alld = RunPrivRepSimulation(pop_alld, params, false, 1);
  auto inv_alld = ComputeInvasionThresholds(c_levels_alld);
  row.bc_min = inv_alld.bc_min;

  PrivateRepGame::population_t pop_allc = {{candidate, params.N - 1}, {allc, 1}};
  auto c_levels_allc = RunPrivRepSimulation(pop_allc, params, false, 2);
  auto inv_allc = ComputeInvasionThresholds(c_levels_allc);
  row.bc_max = inv_allc.bc_max;

  auto evo_result = EvolPrivRepGame::EquilibriumCoopLevelAllCAllD(candidate, params, benefit, beta);
  row.self_coop = std::get<0>(evo_result);
  const auto& rhos = std::get<1>(evo_result);
  const auto& eq = std::get<2>(evo_result);
  if (eq.size() >= 3) {
    row.eq0 = eq[0];
    row.eq1 = eq[1];
    row.eq2 = eq[2];
    row.eq_coop = row.self_coop * eq[0] + 1.0 * eq[1];
  }
  else {
    row.eq_coop = row.self_coop;
  }

  if (rhos.size() >= 3 && rhos[0].size() >= 3) {
    row.rho_resident_to_allc = rhos[0][1];
    row.rho_allc_to_resident = rhos[1][0];
    row.rho_resident_to_alld = rhos[0][2];
    row.rho_alld_to_resident = rhos[2][0];
  }

  return row;
}

std::string FormatDouble(double value) {
  std::ostringstream oss;
  oss << std::setprecision(10) << value;
  return oss.str();
}

void WriteCombinedTable(const std::filesystem::path& path,
                        const std::vector<SweepRow>& rows) {
  auto parent = path.parent_path();
  if (!parent.empty()) {
    std::filesystem::create_directories(parent);
  }
  std::ofstream fout(path);
  if (!fout) {
    throw std::runtime_error("failed to open output file: " + path.string());
  }

  fout << "# rr\tself_coop\tbc_min(AllD)\tbc_max(AllC)\teq_coop\teq0\teq1\teq2\trho_alld_to_resident\trho_resident_to_alld\trho_allc_to_resident\trho_resident_to_allc\n";
  for (const auto& row : rows) {
    fout << row.rr << '\t'
         << FormatDouble(row.self_coop) << '\t'
         << (row.bc_min.has_value() ? FormatDouble(row.bc_min.value()) : std::string("None")) << '\t'
         << (row.bc_max.has_value() ? FormatDouble(row.bc_max.value()) : std::string("None")) << '\t'
         << FormatDouble(row.eq_coop) << '\t'
         << FormatDouble(row.eq0) << '\t'
         << FormatDouble(row.eq1) << '\t'
         << FormatDouble(row.eq2) << '\t'
         << FormatDouble(row.rho_alld_to_resident) << '\t'
         << FormatDouble(row.rho_resident_to_alld) << '\t'
         << FormatDouble(row.rho_allc_to_resident) << '\t'
         << FormatDouble(row.rho_resident_to_allc) << '\n';
  }
  std::cout << "Wrote: " << path << "\n";
}

int main(int argc, char** argv) {
  try {
    ProgramOptions opt = ParseArgs(argc, argv);
    SimulationConfig cfg = BuildSimulationConfig(opt);

    std::string norm_string;
    if (cfg.raw_params && cfg.raw_params->contains("base_norm")) {
      norm_string = (*cfg.raw_params)["base_norm"].get<std::string>();
    } else {
      throw std::runtime_error("base_norm must be provided in parameters JSON");
    }

    nlohmann::json cfg_json = nlohmann::json(cfg.params);
    cfg_json["benefit"] = cfg.benefit;
    cfg_json["beta"] = cfg.beta;
    cfg_json["base_norm"] = norm_string;
    std::cerr << "SimulationConfig: " << cfg_json.dump(2) << '\n';

    Norm base_norm = Norm::ParseNormString(norm_string);
    int rd_id = base_norm.Rd.ID();
    int p_id = base_norm.P.ID();
    if (rd_id < 0 || p_id < 0) {
      throw std::runtime_error("base norm must be deterministic to derive Rd and P ids");
    }

    const Norm allc = Norm::AllC();
    const Norm alld = Norm::AllD();

    std::vector<SweepRow> sweep_rows;
    sweep_rows.reserve(kRrEnd - kRrStart + 1);

    for (int rr = kRrStart; rr <= kRrEnd; ++rr) {
      Norm candidate = BuildNorm(rd_id, rr, p_id);
      sweep_rows.push_back(ComputeSweepRow(rr, candidate, cfg.params, allc, alld, cfg.benefit, cfg.beta));
      if (rr % 10 == 0) {
        std::cerr << "Progress: processed Rr=" << rr << '\n';
      }
    }

    std::filesystem::path out = opt.out_path.has_value()
                                  ? std::filesystem::path(opt.out_path.value())
                                  : std::filesystem::path("R2_sweep.tsv");
    WriteCombinedTable(out, sweep_rows);
  }
  catch (const std::exception& ex) {
    std::cerr << "Error: " << ex.what() << "\n";
    return 1;
  }
  return 0;
}
