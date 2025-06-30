#include <iostream>
#include <fstream>
#include <chrono>
#include <regex>
#include <vector>
#include <queue>
#include <utility>
#include <string>
#include <icecream.hpp>
#include <nlohmann/json.hpp>
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
    if (std::string(argv[i]) == "-j" && i + 1 < argc) {
      std::ifstream fin(argv[++i]);
      // check if file exists
      if (fin) {
        fin >> params;
        fin.close();
      }
      else {
        std::istringstream iss(argv[i]);
        iss >> params;
      }
    }
    else if (std::string(argv[i]) == "-g") {
      count_good = true;
    }
    else {
      args.emplace(argv[i]);
    }
  }

  // set default parameters
  const nlohmann::json default_params = { {"t_init", 1e3}, {"t_measure", 1e3}, {"q", 1.0}, {"mu_impl", 0.0}, {"mu_percept", 0.0}, {"mu_assess1", 0.05}, {"mu_assess2", 0.0}, {"seed", 123456789ull} };
  for (auto it = default_params.begin(); it != default_params.end(); ++it) {
    if (!params.contains(it.key())) {
      params[it.key()] = it.value();
    }
  }

  // if params has keys other than default_params, print them
  for (auto it = params.begin(); it != params.end(); ++it) {
    if (!default_params.contains(it.key())) {
      std::cerr << "[Error] unknown parameter: " << it.key() << std::endl;
      return 1;
    }
  }

  std::cerr << "Parameters:" << std::endl;
  std::cerr << params.dump(2) << std::endl;

  auto show_usage = [&argv, default_params] {
    std::cerr << "Usage: " << argv[0] << " [-j param.json] norm1 size1 [norm2 size2 ...]" << std::endl;
    std::cerr << "Default parameters:" << std::endl;
    std::cerr << "  " << default_params.dump(2) << std::endl;
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
    PrintInitialTimeSeries(prg, params, std::cout);

    if (params.at("t_measure").get<size_t>() > 0) {
      prg.ResetCounts();
      prg.Update(params.at("t_measure").get<size_t>(), params.at("q"), params.at("mu_impl"), params.at("mu_percept").get<double>(),
                 params.at("mu_assess1").get<double>(), params.at("mu_assess2").get<double>(), count_good);
      std::cout << "SystemWideCooperationLevel: " << prg.SystemWideCooperationLevel() << std::endl;
      auto c_levels = prg.NormCooperationLevels();
      if (c_levels.size() > 1) {
        std::cout << "NormCooperationLevels:\n";
        for (size_t i = 0; i < c_levels.size(); i++) {
          for (size_t j = 0; j < c_levels[i].size(); j++) {
            std::cout << ' ' << c_levels[i][j];
          }
          std::cout << "\n";
        }
      }
      if (pop.size() == 2 && pop[0].second > 1 && pop[1].second == 1)
      {
        // calculate critical b/c for invasion analysis
        // (b-c)p_rr >= b p_rm - c p_mr
        // b(p_rr - p_rm) >= c(p_rr - p_mr)
        double p_rr = c_levels[0][0];
        double p_rm = c_levels[0][1];
        double p_mr = c_levels[1][0];
        if (p_rr > p_rm) {
          double b_c_min = (p_rr - p_mr) / (p_rr - p_rm);
          if (b_c_min > 1.0) {
            std::cout << "Critical b/c for invasion: b/c > " << b_c_min << std::endl;
          }
          else {
            std::cout << "Always stable" << std::endl;
          }
        }
        else if (p_rr < p_rm) {
          double b_c_max = (p_rr - p_mr) / (p_rr - p_rm);
          std::cout << "b_c_max: " << b_c_max << std::endl;
          if (b_c_max > 1.0) {
            std::cout << "Critical b/c for invasion: b/c < " << b_c_max << std::endl;
          }
          else {
            std::cout << "Never stable" << std::endl;
          }
        }
        else
        {
          if (p_rr > p_mr) {
            std::cout << "Always stable" << std::endl;
          }
          else {
            std::cout << "Never stable" << std::endl;
          }
        }
        std::cout << "NormComparison:\n";
        std::cout << prg.Population()[0].first.InspectComparison(prg.Population()[1].first);
      }
      if (count_good) {
        std::cout << "NormAverageReputation:\n";
        auto r_levels = prg.NormAverageReputation();
        for (size_t i = 0; i < r_levels.size(); i++) {
          for (size_t j = 0; j < r_levels[i].size(); j++) {
            std::cout << ' ' << r_levels[i][j];
          }
          std::cout << "\n";
        }
      }
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