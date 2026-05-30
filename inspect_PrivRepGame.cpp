#include <iostream>
#include <chrono>
#include <fstream>
#include <regex>
#include <vector>
#include <queue>
#include <utility>
#include <string>
#include <cmath>
#include <icecream.hpp>
#include <nlohmann/json.hpp>
#include "CliHelpUtils.hpp"
#include "CliJsonUtils.hpp"
#include "InvasionAnalysis.hpp"
#include "PrivRepGame.hpp"


void PrintInitialTimeSeries(PrivateRepGame& prg, const nlohmann::json& params, std::ostream& out = std::cout) {
  size_t num_prints = 50;
  size_t interval = params.at("t_init").get<size_t>() / num_prints;

  size_t N_strategies = prg.Population().size();  // number of different strategies

  for (size_t t = 0; t < num_prints; t++) {
    prg.Update(interval, params.at("q"), params.at("mu_impl"), params.at("mu_percept"), params.at("mu_assess1"), params.at("mu_assess2"), false);
    size_t time = (t + 1) * interval;
    out << time << ' ' << prg.SystemWideCooperationLevel();
    if (N_strategies > 1) {
      auto c_levels = prg.NormCooperationLevels();
      for (size_t i = 0; i < N_strategies; i++) {
        for (size_t j = 0; j < N_strategies; j++) {
          out << ' ' << c_levels[i][j];
        }
      }
    }
    out << std::endl;
  }

  prg.ResetCounts();
}

nlohmann::json CooperationLevelsToJson(const std::vector<std::vector<double>>& c_levels) {
  nlohmann::json norm_levels = nlohmann::json::array();
  for (size_t i = 0; i < c_levels.size(); i++) {
    nlohmann::json row = nlohmann::json::array();
    for (size_t j = 0; j < c_levels[i].size(); j++) {
      double v = c_levels[i][j];
      if (std::isfinite(v)) row.push_back(v); else row.push_back(nullptr);
    }
    norm_levels.push_back(row);
  }
  return norm_levels;
}

std::string DeterministicTriplet(const Norm& norm) {
  return std::to_string(norm.Rd.ID()) + "-" +
         std::to_string(norm.Rr.ID()) + "-" +
         std::to_string(norm.P.ID());
}

void RunPrivateRepMeasurement(PrivateRepGame& prg, const nlohmann::json& params, bool count_good) {
  prg.Update(params.at("t_init").get<size_t>(),
             params.at("q").get<double>(),
             params.at("mu_impl").get<double>(),
             params.at("mu_percept").get<double>(),
             params.at("mu_assess1").get<double>(),
             params.at("mu_assess2").get<double>(),
             count_good);
  prg.ResetCounts();
  prg.Update(params.at("t_measure").get<size_t>(),
             params.at("q").get<double>(),
             params.at("mu_impl").get<double>(),
             params.at("mu_percept").get<double>(),
             params.at("mu_assess1").get<double>(),
             params.at("mu_assess2").get<double>(),
             count_good);
}

nlohmann::json AnalyzeLocalActionMutants(const Norm& resident, size_t N, const nlohmann::json& params) {
  if (N < 2) {
    throw std::runtime_error("N must be >= 2");
  }
  if (params.at("t_measure").get<size_t>() == 0) {
    throw std::runtime_error("t_measure must be > 0 for local invasion analysis");
  }

  const auto mutants = resident.ActionRuleVariants(false);
  std::vector<InvasionThresholds> thresholds_vec;
  thresholds_vec.reserve(mutants.size());

  nlohmann::json mutant_rows = nlohmann::json::array();
  for (const auto& mutant : mutants) {
    PrivateRepGame::population_t pop = {{resident, N - 1}, {mutant, 1}};
    PrivateRepGame prg(pop, params.at("_seed").get<uint64_t>());
    RunPrivateRepMeasurement(prg, params, false);

    auto c_levels = prg.NormCooperationLevels();
    auto thresholds = ComputeInvasionThresholds(c_levels);
    thresholds_vec.push_back(thresholds);

    nlohmann::json row = {
      {"norm", DeterministicTriplet(mutant)},
      {"norm_name", mutant.GetName()},
      {"norm_id", mutant.ID()},
      {"action_rule_id", mutant.P.ID()},
      {"NormCooperationLevels", CooperationLevelsToJson(c_levels)},
      {"Invasion", InvasionThresholdsToJson(thresholds)}
    };
    mutant_rows.push_back(row);
  }

  auto common = CombineInvasionThresholds(thresholds_vec);

  nlohmann::json out = {
    {"mode", "local_action_mutants"},
    {"resident", DeterministicTriplet(resident)},
    {"resident_name", resident.GetName()},
    {"resident_id", resident.ID()},
    {"N", N},
    {"mutant_size", 1},
    {"mutants", mutant_rows},
    {"CommonInvasion", CommonInvasionThresholdsToJson(common)}
  };
  return out;
}


int main(int argc, char *argv[]) {

  std::queue<std::string> args;
  nlohmann::json params = nlohmann::json::object();
  bool count_good = false;
  bool local_action_mutants = false;
  // -j param.json : set parameters by json file or json string
  for (int i = 1; i < argc; ++i) {
    if (CliJsonUtils::ConsumeJsonOption(argc, argv, i, "-j", params)) {
      continue;
    }
    if (std::string(argv[i]) == "-g") {
      count_good = true;
    }
    else if (std::string(argv[i]) == "--local-action-mutants") {
      local_action_mutants = true;
    }
    else {
      args.emplace(argv[i]);
    }
  }

  // set default parameters
  const nlohmann::json default_params = { {"t_init", 1e3}, {"t_measure", 1e3}, {"q", 1.0}, {"mu_impl", 0.0}, {"mu_percept", 0.0}, {"mu_assess1", 0.05}, {"mu_assess2", 0.0}, {"_seed", 123456789ull} };
  try {
    CliJsonUtils::ValidateObjectKeys(params, CliJsonUtils::JsonKeys(default_params));
    CliJsonUtils::ApplyJsonDefaults(params, default_params);
  }
  catch (const std::exception& e) {
    std::cerr << "[Error] " << e.what() << std::endl;
    return 1;
  }

  std::cerr << "Parameters:" << std::endl;
  std::cerr << params.dump(2) << std::endl;

  auto show_usage = [&argv, default_params] {
    std::cerr << "Usage: " << argv[0] << " [options] <norm1> <size1> [<norm2> <size2> ...]\n";
    std::cerr << "       " << argv[0] << " [options] --local-action-mutants <resident_norm> <N>\n";
    std::cerr << "Options:\n";
    CliHelpUtils::PrintJsonOption(std::cerr);
    CliHelpUtils::PrintOption(std::cerr, "-g", "Include average reputations and write image.txt");
    CliHelpUtils::PrintOption(std::cerr, "--local-action-mutants", "Analyze b/c stability against one-player action-rule mutants");
    std::cerr << "Default parameters:\n";
    std::cerr << "  " << default_params.dump(2) << '\n';
    CliHelpUtils::PrintNormFormat(std::cerr);
  };

  auto start = std::chrono::high_resolution_clock::now();

  if (local_action_mutants) {
    if (args.size() != 2) {
      std::cerr << "[Error] --local-action-mutants expects <resident_norm> <N>" << std::endl;
      show_usage();
      return 1;
    }
    try {
      std::string norm_str = args.front(); args.pop();
      size_t N = std::stoull(args.front()); args.pop();
      Norm resident = Norm::ParseNormString(norm_str, false);
      auto out = AnalyzeLocalActionMutants(resident, N, params);
      std::cout << out.dump(2) << std::endl;
    }
    catch (const std::exception& e) {
      std::cerr << "[Error] " << e.what() << std::endl;
      return 1;
    }
  }
  else if (args.size() < 2 || args.size() % 2 != 0) {
    std::cerr << "[Error] wrong input format" << std::endl;
    show_usage();
    return 1;
  }
  else {
    PrivateRepGame::population_t pop;
    while (!args.empty()) {
      std::string norm_str = args.front(); args.pop();
      size_t size = std::stoi(args.front()); args.pop();
      Norm norm = Norm::ParseNormString(norm_str, false);
      pop.emplace_back(norm, size);
    }

    PrivateRepGame prg(pop, params["_seed"].get<uint64_t>());
    PrintInitialTimeSeries(prg, params, std::cerr);

    if (params.at("t_measure").get<size_t>() > 0) {
      prg.ResetCounts();
      prg.Update(params.at("t_measure").get<size_t>(), params.at("q"), params.at("mu_impl"), params.at("mu_percept").get<double>(),
                 params.at("mu_assess1").get<double>(), params.at("mu_assess2").get<double>(), count_good);

      nlohmann::json out = nlohmann::json::object();
      out["SystemWideCooperationLevel"] = prg.SystemWideCooperationLevel();

      auto c_levels = prg.NormCooperationLevels();
      if (c_levels.size() > 1) {
        out["NormCooperationLevels"] = CooperationLevelsToJson(c_levels);
      }

      if (pop.size() == 2 && pop[0].second > 1 && pop[1].second == 1)
      {
        out["Invasion"] = InvasionThresholdsToJson(ComputeInvasionThresholds(c_levels));

        std::cerr << "NormComparison:\n";
        std::cerr << prg.Population()[0].first.InspectComparison(prg.Population()[1].first);
      }

      if (count_good) {
        auto r_levels = prg.NormAverageReputation();
        nlohmann::json rep_levels = nlohmann::json::array();
        for (size_t i = 0; i < r_levels.size(); i++) {
          nlohmann::json row = nlohmann::json::array();
          for (size_t j = 0; j < r_levels[i].size(); j++) {
            double v = r_levels[i][j];
            if (std::isfinite(v)) row.push_back(v); else row.push_back(nullptr);
          }
          rep_levels.push_back(row);
        }
        out["NormAverageReputation"] = rep_levels;
      }

      std::cout << out.dump(2) << std::endl;
    }

    if (count_good) {
      std::ofstream fout("image.txt");
      prg.PrintImage(fout);
      std::cerr << "image was written to image.txt" << std::endl;
    }

  }

  auto end = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> elapsed = end - start;
  std::cerr << "Elapsed time: " << elapsed.count() << " s\n";

  return 0;
}
