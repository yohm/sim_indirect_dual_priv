#include <iostream>
#include <chrono>
#include <regex>
#include <vector>
#include <queue>
#include <utility>
#include <string>
#include <cmath>
#include <icecream.hpp>
#include <nlohmann/json.hpp>
#include "CliJsonUtils.hpp"
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


int main(int argc, char *argv[]) {

  std::queue<std::string> args;
  nlohmann::json params = nlohmann::json::object();
  bool count_good = false;
  // -j param.json : set parameters by json file or json string
  for (int i = 1; i < argc; ++i) {
    if (CliJsonUtils::ConsumeJsonOption(argc, argv, i, "-j", params)) {
      continue;
    }
    if (std::string(argv[i]) == "-g") {
      count_good = true;
    }
    else {
      args.emplace(argv[i]);
    }
  }

  // set default parameters
  const nlohmann::json default_params = { {"t_init", 1e3}, {"t_measure", 1e3}, {"q", 1.0}, {"mu_impl", 0.0}, {"mu_percept", 0.0}, {"mu_assess1", 0.05}, {"mu_assess2", 0.0}, {"seed", 123456789ull} };
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
    std::cerr << "Usage: " << argv[0] << " [-j param.json] norm1 size1 [norm2 size2 ...]" << std::endl;
    std::cerr << "Default parameters:" << std::endl;
    std::cerr << "  " << default_params.dump(2) << std::endl;
    std::cerr << "Norm format: " << CliJsonUtils::NormFormatHelp() << std::endl;
  };

  auto start = std::chrono::high_resolution_clock::now();

  if (args.size() < 2 || args.size() % 2 != 0) {
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

    PrivateRepGame prg(pop, params["seed"].get<uint64_t>());
    PrintInitialTimeSeries(prg, params, std::cerr);

    if (params.at("t_measure").get<size_t>() > 0) {
      prg.ResetCounts();
      prg.Update(params.at("t_measure").get<size_t>(), params.at("q"), params.at("mu_impl"), params.at("mu_percept").get<double>(),
                 params.at("mu_assess1").get<double>(), params.at("mu_assess2").get<double>(), count_good);

      nlohmann::json out = nlohmann::json::object();
      out["SystemWideCooperationLevel"] = prg.SystemWideCooperationLevel();

      auto c_levels = prg.NormCooperationLevels();
      if (c_levels.size() > 1) {
        nlohmann::json norm_levels = nlohmann::json::array();
        for (size_t i = 0; i < c_levels.size(); i++) {
          nlohmann::json row = nlohmann::json::array();
          for (size_t j = 0; j < c_levels[i].size(); j++) {
            double v = c_levels[i][j];
            if (std::isfinite(v)) row.push_back(v); else row.push_back(nullptr);
          }
          norm_levels.push_back(row);
        }
        out["NormCooperationLevels"] = norm_levels;
      }

      if (pop.size() == 2 && pop[0].second > 1 && pop[1].second == 1)
      {
        // calculate critical b/c for invasion analysis
        // (b-c)p_rr >= b p_rm - c p_mr
        // b(p_rr - p_rm) >= c(p_rr - p_mr)
        double p_rr = c_levels[0][0];
        double p_rm = c_levels[0][1];
        double p_mr = c_levels[1][0];
        nlohmann::json invasion = nlohmann::json::object();
        if (p_rr > p_rm) {
          double b_c_min = (p_rr - p_mr) / (p_rr - p_rm);
          if (b_c_min > 1.0) {
            invasion["bc_min"] = b_c_min;
            invasion["bc_max"] = nullptr;
          }
          else {
            // always stable
            invasion["bc_min"] = 1.0;
            invasion["bc_max"] = nullptr;
          }
        }
        else if (p_rr < p_rm) {
          double b_c_max = (p_rr - p_mr) / (p_rr - p_rm);
          invasion["bc_max"] = b_c_max;
          if (b_c_max > 1.0) {
            invasion["bc_min"] = 1.0;
            invasion["bc_max"] = b_c_max;
          }
          else {
            // never stable
            invasion["bc_min"] = nullptr;
            invasion["bc_max"] = 1.0;
          }
        }
        else
        {
          if (p_rr > p_mr) {
            // Always stable
            invasion["bc_min"] = 1.0;
            invasion["bc_max"] = nullptr;
          }
          else {
            // never stable
            invasion["bc_min"] = nullptr;
            invasion["bc_max"] = 1.0;
          }
        }
        out["Invasion"] = invasion;

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
