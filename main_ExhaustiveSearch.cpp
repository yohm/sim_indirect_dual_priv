#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mpi.h>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "EvolPrivRepGame.hpp"
#include "PrivRepGame.hpp"
#include "Norm.hpp"

struct ProgramOptions {
  nlohmann::json param_overrides = nlohmann::json::object();
  size_t debug_limit = 0;
};

struct PackedRow {
  uint64_t idx = 0;
  int rd = 0;
  int rr = 0;
  int act = 0;
  double self_coop = 0.0;
  double bc_min = -1.0;
};

void PrintUsage(const char* exe) {
  std::cerr << "Usage: " << exe << " [options]\n";
  std::cerr << "Options:\n";
  std::cerr << "  -j <json|path>      Simulation parameters (inline JSON or file path)\n";
  std::cerr << "  --debug-limit <N>   Only evaluate the first N norms (fill rest with defaults)\n";
  std::cerr << "  --help              Show this message\n";
  std::cerr << "\nParameters JSON keys (optional):\n";
  std::cerr << "  N, t_init, t_measure, q, mu_impl, mu_percept, mu_assess1, mu_assess2, _seed\n";
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
    else if (arg == "--debug-limit") {
      if (i + 1 >= argc) {
        throw std::runtime_error("--debug-limit requires a value");
      }
      const std::string value = argv[++i];
      try {
        opt.debug_limit = std::stoull(value);
      }
      catch (const std::exception&) {
        throw std::runtime_error("invalid integer for --debug-limit: " + value);
      }
      if (opt.debug_limit == 0) {
        throw std::runtime_error("--debug-limit must be > 0");
      }
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
      "N", "t_init", "t_measure", "q", "mu_impl", "mu_percept", "mu_assess1", "mu_assess2", "_seed"
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

    EvolPrivRepGame::Parameters params = BuildParameters(opt.param_overrides);
    auto norm_ids = Norm::Deterministic3rdOrderWithR2NormIDs();
    const size_t norm_count = norm_ids.size();
    size_t active_count = norm_count;
    if (opt.debug_limit > 0 && opt.debug_limit < norm_count) {
      active_count = opt.debug_limit;
    }

    if (world_rank == 0) {
      std::cerr << "Sweeping " << norm_count << " unique deterministic norms (up to B/G symmetry)\n";
      if (active_count < norm_count) {
        std::cerr << " Debug mode: only evaluating first " << active_count << " norms\n";
      }
    }

    Norm alld = Norm::AllD();
    std::vector<PackedRow> local_rows;
    size_t reserve = (norm_count + static_cast<size_t>(world_size) - 1) / static_cast<size_t>(world_size);
    local_rows.reserve(reserve);

    for (size_t idx = static_cast<size_t>(world_rank); idx < norm_count; idx += static_cast<size_t>(world_size)) {
      if (world_rank == 0 && idx % 128 == 0) {
        std::cerr << " progress: " << idx << " / " << norm_count << std::endl;
      }
      PackedRow packed;
      packed.idx = static_cast<uint64_t>(idx);
      if (idx < active_count) {
        size_t norm_id = norm_ids[idx];
        Norm candidate = Norm::ConstructFromID(static_cast<int>(norm_id));
        packed.rd = candidate.Rd.ID();
        packed.rr = candidate.Rr.ID();
        packed.act = candidate.P.ID();

        EvolPrivRepGame::Parameters mono_params = params;
        mono_params.seed += static_cast<uint64_t>(idx * 2);
        packed.self_coop = EvolPrivRepGame::MonomorphicCooperationLevel(candidate, mono_params);

        PrivateRepGame::population_t pop = {{candidate, params.N - 1}, {alld, 1}};
        auto c_levels = RunPrivRepSimulation(pop, params, static_cast<uint64_t>(idx * 2 + 1));
        auto bc_min = ComputeBcMin(c_levels);
        if (bc_min.has_value()) { packed.bc_min = bc_min.value(); }
      } else {
        packed.rd = -1;
        packed.rr = -1;
        packed.act = -1;
        packed.self_coop = 0.0;
        packed.bc_min = -1.0;
      }
      local_rows.push_back(packed);
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
      if (gathered_rows.size() != norm_count) {
        throw std::runtime_error("MPI gather produced inconsistent row count");
      }

      std::vector<PackedRow> rows(norm_count);
      for (const auto& packed : gathered_rows) {
        if (packed.idx >= norm_count) {
          throw std::runtime_error("Received row with invalid index");
        }
        rows[static_cast<size_t>(packed.idx)] = packed;
      }

      std::cout << "#R1\tR2\tAction\tSelfCoop\tbc_min(AllD)\n";
      for (const auto& row : rows) {
        std::cout << row.rd << '\t'
                  << row.rr << '\t'
                  << row.act << '\t'
                  << FormatDouble(row.self_coop) << '\t';
        if (row.bc_min > 0.0) {
          std::cout << FormatDouble(row.bc_min) << '\n';
        } else {
          std::cout << "None\n";
        }
      }
    }

    MPI_Finalize();
    mpi_initialized = false;
    return 0;
  }
  catch (const std::exception& e) {
    if (mpi_initialized) {
      std::cerr << "[Rank " << world_rank << " Error] " << e.what() << std::endl;
      MPI_Abort(MPI_COMM_WORLD, 1);
    } else {
      std::cerr << "[Error] " << e.what() << std::endl;
    }
    return 1;
  }
}
