#include <cstdlib>
#include <cstdint>
#include <cerrno>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <mpi.h>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

#include <sys/stat.h>
#include <sys/types.h>

#include <nlohmann/json.hpp>

#include "CliHelpUtils.hpp"
#include "CliJsonUtils.hpp"
#include "EvolPrivRepGame.hpp"
#include "InvasionAnalysis.hpp"
#include "Norm.hpp"
#include "PrivRepGame.hpp"

constexpr int kRuleStart = 0;
constexpr int kRuleEnd = 255;
constexpr double kBehavioralMutantBenefit = 5.0;

struct ProgramOptions {
  std::optional<std::string> params_arg;
  std::optional<std::string> out_path;
  int rd_start = kRuleStart;
  int rd_end = kRuleEnd;
  int rr_start = kRuleStart;
  int rr_end = kRuleEnd;
};

struct SimulationConfig {
  EvolPrivRepGame::Parameters params;
  double benefit = 5.0;
  double beta = 1.0;
  std::optional<nlohmann::json> raw_params;
};

struct SweepRow {
  int rd = 0;
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
  int best_behavioral_mutant_action = -1;
  double behavioral_max_advantage = std::numeric_limits<double>::quiet_NaN();
  double behavioral_resident_payoff = std::numeric_limits<double>::quiet_NaN();
  double behavioral_mutant_payoff = std::numeric_limits<double>::quiet_NaN();
};

struct PackedRow {
  uint64_t idx = 0;
  int rd = 0;
  int rr = 0;
  double self_coop = std::numeric_limits<double>::quiet_NaN();
  int has_bc_min = 0;
  double bc_min = std::numeric_limits<double>::quiet_NaN();
  int has_bc_max = 0;
  double bc_max = std::numeric_limits<double>::quiet_NaN();
  double eq_coop = std::numeric_limits<double>::quiet_NaN();
  double eq0 = std::numeric_limits<double>::quiet_NaN();
  double eq1 = std::numeric_limits<double>::quiet_NaN();
  double eq2 = std::numeric_limits<double>::quiet_NaN();
  double rho_alld_to_resident = std::numeric_limits<double>::quiet_NaN();
  double rho_resident_to_alld = std::numeric_limits<double>::quiet_NaN();
  double rho_allc_to_resident = std::numeric_limits<double>::quiet_NaN();
  double rho_resident_to_allc = std::numeric_limits<double>::quiet_NaN();
  int best_behavioral_mutant_action = -1;
  double behavioral_max_advantage = std::numeric_limits<double>::quiet_NaN();
  double behavioral_resident_payoff = std::numeric_limits<double>::quiet_NaN();
  double behavioral_mutant_payoff = std::numeric_limits<double>::quiet_NaN();
};

void PrintUsage(const char* exe) {
  std::cout << "Usage: " << exe << " [options]\n";
  std::cout << "Options:\n";
  CliHelpUtils::PrintOption(std::cout, "--params <json|path>", "Parameters JSON inline or file path");
  CliHelpUtils::PrintOption(std::cout, "--out <path>", "Output TSV path (default: R1R2_sweep.tsv)");
  CliHelpUtils::PrintOption(std::cout, "--rd-start <ID>", "First R1 rule ID to evaluate (default: 0)");
  CliHelpUtils::PrintOption(std::cout, "--rd-end <ID>", "Last R1 rule ID to evaluate, inclusive (default: 255)");
  CliHelpUtils::PrintOption(std::cout, "--rr-start <ID>", "First R2 rule ID to evaluate (default: 0)");
  CliHelpUtils::PrintOption(std::cout, "--rr-end <ID>", "Last R2 rule ID to evaluate, inclusive (default: 255)");
  CliHelpUtils::PrintOption(std::cout, "--help", "Show this message");
  std::cout << "\nJSON parameters:\n";
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
  std::cout << "\nBehavioral-mutant payoff advantage is always evaluated at b/c=5.\n";
}

std::string RequireValue(int argc, char** argv, int& i, const std::string& flag) {
  if (i + 1 >= argc) {
    throw std::runtime_error("missing value for " + flag);
  }
  return std::string(argv[++i]);
}

int ParseRuleID(const std::string& value, const std::string& flag) {
  int id = 0;
  try {
    size_t pos = 0;
    id = std::stoi(value, &pos);
    if (pos != value.size()) {
      throw std::runtime_error("trailing characters");
    }
  }
  catch (const std::exception&) {
    throw std::runtime_error("invalid rule ID for " + flag + ": " + value);
  }
  if (id < kRuleStart || id > kRuleEnd) {
    throw std::runtime_error(flag + " must be between 0 and 255");
  }
  return id;
}

void ValidateRanges(const ProgramOptions& opt) {
  if (opt.rd_start > opt.rd_end) {
    throw std::runtime_error("--rd-start must be <= --rd-end");
  }
  if (opt.rr_start > opt.rr_end) {
    throw std::runtime_error("--rr-start must be <= --rr-end");
  }
}

ProgramOptions ParseArgs(int argc, char** argv) {
  if (argc <= 1) {
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
    else if (arg == "--rd-start") {
      opt.rd_start = ParseRuleID(RequireValue(argc, argv, i, arg), arg);
    }
    else if (arg == "--rd-end") {
      opt.rd_end = ParseRuleID(RequireValue(argc, argv, i, arg), arg);
    }
    else if (arg == "--rr-start") {
      opt.rr_start = ParseRuleID(RequireValue(argc, argv, i, arg), arg);
    }
    else if (arg == "--rr-end") {
      opt.rr_end = ParseRuleID(RequireValue(argc, argv, i, arg), arg);
    }
    else {
      throw std::runtime_error("unknown option: " + arg);
    }
  }
  ValidateRanges(opt);
  return opt;
}

SimulationConfig BuildSimulationConfig(const ProgramOptions& opt) {
  SimulationConfig cfg;
  nlohmann::json raw = nlohmann::json::object();
  if (opt.params_arg.has_value()) {
    raw = CliJsonUtils::LoadJsonFromFileOrString(opt.params_arg.value());
  }

  if (raw.is_object()) {
    CliJsonUtils::ValidateObjectKeys(raw, {"N", "t_init", "t_measure", "q", "mu_impl", "mu_percept", "mu_assess1", "mu_assess2", "_seed", "benefit", "beta"});
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
  if (cfg.params.t_measure == 0) {
    throw std::runtime_error("t_measure must be > 0");
  }

  cfg.benefit = (raw.is_object() && raw.contains("benefit")) ? raw.at("benefit").get<double>() : 5.0;
  cfg.beta = (raw.is_object() && raw.contains("beta")) ? raw.at("beta").get<double>() : 1.0;

  if (opt.params_arg.has_value()) {
    cfg.raw_params = raw;
  }
  return cfg;
}

Norm BuildNorm(int rd_id, int rr_id) {
  auto rd = AssessmentRule::MakeDeterministicRule(rd_id);
  auto rr = AssessmentRule::MakeDeterministicRule(rr_id);
  return Norm(rd, rr, ActionRule::DISC());
}

std::vector<std::vector<double>> RunPrivRepSimulation(const PrivateRepGame::population_t& pop,
                                                      const EvolPrivRepGame::Parameters& params,
                                                      bool count_good = false,
                                                      uint64_t seed_offset = 0) {
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

struct BehavioralMutantPayoffSummary {
  int best_action = -1;
  double max_advantage = -std::numeric_limits<double>::infinity();
  double resident_payoff = std::numeric_limits<double>::quiet_NaN();
  double mutant_payoff = std::numeric_limits<double>::quiet_NaN();
};

BehavioralMutantPayoffSummary AnalyzeBehavioralMutants(const Norm& resident,
                                                       const EvolPrivRepGame::Parameters& params) {
  BehavioralMutantPayoffSummary result;
  const auto mutants = resident.ActionRuleVariants(false);

  for (const auto& mutant : mutants) {
    auto bc_probs = EvolPrivRepGame::BenefitCostProbs(resident, params.N - 1, mutant, params);
    double resident_payoff = kBehavioralMutantBenefit * bc_probs.first.benefit_prob - bc_probs.first.cost_prob;
    double mutant_payoff = kBehavioralMutantBenefit * bc_probs.second.benefit_prob - bc_probs.second.cost_prob;
    double advantage = mutant_payoff - resident_payoff;

    if (advantage > result.max_advantage) {
      result.max_advantage = advantage;
      result.best_action = mutant.P.ID();
      result.resident_payoff = resident_payoff;
      result.mutant_payoff = mutant_payoff;
    }
  }

  return result;
}

SweepRow ComputeSweepRow(int rd,
                         int rr,
                         const Norm& candidate,
                         const EvolPrivRepGame::Parameters& params,
                         const Norm& allc,
                         const Norm& alld,
                         double benefit,
                         double beta) {
  SweepRow row;
  row.rd = rd;
  row.rr = rr;

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

  auto behavioral = AnalyzeBehavioralMutants(candidate, params);
  row.best_behavioral_mutant_action = behavioral.best_action;
  row.behavioral_max_advantage = behavioral.max_advantage;
  row.behavioral_resident_payoff = behavioral.resident_payoff;
  row.behavioral_mutant_payoff = behavioral.mutant_payoff;

  return row;
}

PackedRow PackRow(uint64_t idx, const SweepRow& row) {
  PackedRow packed;
  packed.idx = idx;
  packed.rd = row.rd;
  packed.rr = row.rr;
  packed.self_coop = row.self_coop;
  packed.has_bc_min = row.bc_min.has_value() ? 1 : 0;
  packed.bc_min = row.bc_min.value_or(std::numeric_limits<double>::quiet_NaN());
  packed.has_bc_max = row.bc_max.has_value() ? 1 : 0;
  packed.bc_max = row.bc_max.value_or(std::numeric_limits<double>::quiet_NaN());
  packed.eq_coop = row.eq_coop;
  packed.eq0 = row.eq0;
  packed.eq1 = row.eq1;
  packed.eq2 = row.eq2;
  packed.rho_alld_to_resident = row.rho_alld_to_resident;
  packed.rho_resident_to_alld = row.rho_resident_to_alld;
  packed.rho_allc_to_resident = row.rho_allc_to_resident;
  packed.rho_resident_to_allc = row.rho_resident_to_allc;
  packed.best_behavioral_mutant_action = row.best_behavioral_mutant_action;
  packed.behavioral_max_advantage = row.behavioral_max_advantage;
  packed.behavioral_resident_payoff = row.behavioral_resident_payoff;
  packed.behavioral_mutant_payoff = row.behavioral_mutant_payoff;
  return packed;
}

std::string FormatDouble(double value) {
  std::ostringstream oss;
  oss << std::setprecision(10) << value;
  return oss.str();
}

void CreateDirectories(const std::string& dir) {
  if (dir.empty()) {
    return;
  }

  std::string current;
  size_t pos = 0;
  if (dir[0] == '/') {
    current = "/";
    pos = 1;
  }

  while (pos <= dir.size()) {
    size_t next = dir.find('/', pos);
    std::string part = dir.substr(pos, next == std::string::npos ? std::string::npos : next - pos);
    if (!part.empty()) {
      if (!current.empty() && current.back() != '/') {
        current += '/';
      }
      current += part;
      if (mkdir(current.c_str(), 0755) != 0 && errno != EEXIST) {
        throw std::runtime_error("failed to create directory " + current + ": " + std::strerror(errno));
      }
    }
    if (next == std::string::npos) {
      break;
    }
    pos = next + 1;
  }
}

std::string ParentPath(const std::string& path) {
  size_t slash = path.find_last_of('/');
  if (slash == std::string::npos) {
    return "";
  }
  if (slash == 0) {
    return "/";
  }
  return path.substr(0, slash);
}

void WriteCombinedTable(const std::string& path, const std::vector<PackedRow>& rows) {
  CreateDirectories(ParentPath(path));
  std::ofstream fout(path);
  if (!fout) {
    throw std::runtime_error("failed to open output file: " + path);
  }

  fout << "# rd\trr\tself_coop\tbc_min(AllD)\tbc_max(AllC)\teq_coop\teq0\teq1\teq2\trho_alld_to_resident\trho_resident_to_alld\trho_allc_to_resident\trho_resident_to_allc\tbest_behavioral_mutant_action\tbehavioral_max_advantage_bc5\tbehavioral_resident_payoff_bc5\tbehavioral_mutant_payoff_bc5\n";
  for (const auto& row : rows) {
    fout << row.rd << '\t'
         << row.rr << '\t'
         << FormatDouble(row.self_coop) << '\t'
         << (row.has_bc_min ? FormatDouble(row.bc_min) : std::string("None")) << '\t'
         << (row.has_bc_max ? FormatDouble(row.bc_max) : std::string("None")) << '\t'
         << FormatDouble(row.eq_coop) << '\t'
         << FormatDouble(row.eq0) << '\t'
         << FormatDouble(row.eq1) << '\t'
         << FormatDouble(row.eq2) << '\t'
         << FormatDouble(row.rho_alld_to_resident) << '\t'
         << FormatDouble(row.rho_resident_to_alld) << '\t'
         << FormatDouble(row.rho_allc_to_resident) << '\t'
         << FormatDouble(row.rho_resident_to_allc) << '\t'
         << row.best_behavioral_mutant_action << '\t'
         << FormatDouble(row.behavioral_max_advantage) << '\t'
         << FormatDouble(row.behavioral_resident_payoff) << '\t'
         << FormatDouble(row.behavioral_mutant_payoff) << '\n';
  }
  std::cout << "Wrote: " << path << "\n";
}

int main(int argc, char** argv) {
  ProgramOptions opt;
  try {
    opt = ParseArgs(argc, argv);
  }
  catch (const std::exception& e) {
    std::cerr << "[Error] " << e.what() << std::endl;
    return 1;
  }

  int world_rank = 0;
  int world_size = 1;
  bool mpi_initialized = false;

  try {
    int rc = MPI_Init(&argc, &argv);
    if (rc != MPI_SUCCESS) {
      throw std::runtime_error("MPI_Init failed");
    }
    mpi_initialized = true;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    SimulationConfig cfg = BuildSimulationConfig(opt);
    const int rd_count = opt.rd_end - opt.rd_start + 1;
    const int rr_count = opt.rr_end - opt.rr_start + 1;
    const int sweep_count = rd_count * rr_count;
    if (world_rank == 0) {
      nlohmann::json cfg_json = nlohmann::json(cfg.params);
      cfg_json["benefit"] = cfg.benefit;
      cfg_json["beta"] = cfg.beta;
      std::cerr << "SimulationConfig: " << cfg_json.dump(2) << '\n';
      std::cerr << "Sweeping " << sweep_count << " norms with Discriminator action rule"
                << " (R1=" << opt.rd_start << ".." << opt.rd_end
                << ", R2=" << opt.rr_start << ".." << opt.rr_end << ")\n";
    }

    const Norm allc = Norm::AllC();
    const Norm alld = Norm::AllD();

    std::vector<PackedRow> local_rows;
    size_t reserve = (static_cast<size_t>(sweep_count) + static_cast<size_t>(world_size) - 1) / static_cast<size_t>(world_size);
    local_rows.reserve(reserve);

    for (int idx = world_rank; idx < sweep_count; idx += world_size) {
      int rd = opt.rd_start + idx / rr_count;
      int rr = opt.rr_start + idx % rr_count;
      Norm candidate = BuildNorm(rd, rr);
      SweepRow row = ComputeSweepRow(rd, rr, candidate, cfg.params, allc, alld, cfg.benefit, cfg.beta);
      local_rows.push_back(PackRow(static_cast<uint64_t>(idx), row));

      if (world_rank == 0 && idx % rr_count == 0) {
        std::cerr << "Progress: processed index " << idx << " / " << sweep_count << '\n';
      }
    }

    int local_count = static_cast<int>(local_rows.size());
    std::vector<int> recv_counts;
    if (world_rank == 0) {
      recv_counts.resize(world_size);
    }

    MPI_Gather(&local_count,
               1,
               MPI_INT,
               world_rank == 0 ? recv_counts.data() : nullptr,
               1,
               MPI_INT,
               0,
               MPI_COMM_WORLD);

    const int packed_size = static_cast<int>(sizeof(PackedRow));
    std::vector<int> recv_counts_bytes;
    std::vector<int> recv_displs;
    std::vector<PackedRow> gathered_rows;

    if (world_rank == 0) {
      recv_counts_bytes.resize(world_size, 0);
      recv_displs.resize(world_size, 0);
      int byte_offset = 0;
      for (int i = 0; i < world_size; ++i) {
        recv_counts_bytes[i] = recv_counts[i] * packed_size;
        recv_displs[i] = byte_offset;
        byte_offset += recv_counts_bytes[i];
      }
      gathered_rows.resize(static_cast<size_t>(byte_offset / packed_size));
    }

    MPI_Gatherv(local_rows.empty() ? nullptr : local_rows.data(),
                local_count * packed_size,
                MPI_BYTE,
                world_rank == 0 ? gathered_rows.data() : nullptr,
                world_rank == 0 ? recv_counts_bytes.data() : nullptr,
                world_rank == 0 ? recv_displs.data() : nullptr,
                MPI_BYTE,
                0,
                MPI_COMM_WORLD);

    if (world_rank == 0) {
      if (gathered_rows.size() != static_cast<size_t>(sweep_count)) {
        throw std::runtime_error("MPI gather produced inconsistent row count");
      }

      std::vector<PackedRow> rows(static_cast<size_t>(sweep_count));
      for (const auto& packed : gathered_rows) {
        if (packed.idx >= static_cast<uint64_t>(sweep_count)) {
          throw std::runtime_error("received row with invalid index");
        }
        rows[static_cast<size_t>(packed.idx)] = packed;
      }

      std::string out = opt.out_path.has_value() ? opt.out_path.value() : std::string("R1R2_sweep.tsv");
      WriteCombinedTable(out, rows);
    }

    MPI_Finalize();
    mpi_initialized = false;
    return 0;
  }
  catch (const std::exception& e) {
    if (mpi_initialized) {
      std::cerr << "[Rank " << world_rank << " Error] " << e.what() << std::endl;
      MPI_Abort(MPI_COMM_WORLD, 1);
    }
    else {
      std::cerr << "[Error] " << e.what() << std::endl;
    }
    return 1;
  }
}
