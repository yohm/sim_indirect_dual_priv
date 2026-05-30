#include <iostream>
#include <fstream>
#include <chrono>
#include <regex>
#include <icecream.hpp>
#include <nlohmann/json.hpp>
#include "CliHelpUtils.hpp"
#include "CliJsonUtils.hpp"
#include "EvolPrivRepGame.hpp"


void PrintSelectionMutationEquilibriumAllCAllD(const Norm& norm, const EvolPrivRepGame::Parameters& params, double benefit, double beta) {
  auto start = std::chrono::high_resolution_clock::now();

  std::cerr << "Norm: " << norm.GetName() << std::endl;
  std::cerr << "Parameteres:" << nlohmann::json(params).dump(2)  << std::endl;
  std::cerr << "benefit: " << benefit << std::endl;
  std::cerr << "beta: " << beta << std::endl;

  auto selfc_rho_eq = EvolPrivRepGame::EquilibriumCoopLevelAllCAllD(norm, params, benefit, beta);

  double self_cooperation_level = std::get<0>(selfc_rho_eq);
  auto rhos = std::get<1>(selfc_rho_eq);
  auto eq = std::get<2>(selfc_rho_eq);
  double eq_cooperation_level = self_cooperation_level * eq[0] + 1.0 * eq[1] + 0.0 * eq[2];

  nlohmann::json j = {
    {"self_cooperation_level", self_cooperation_level},
    {"rhos", rhos},
    {"eq", eq},
    {"eq_cooperation_level", eq_cooperation_level}
  };
  std::cout << j.dump(2) << std::endl;

  auto end = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> elapsed = end - start;
  std::cerr << "Elapsed time: " << elapsed.count() << " s\n";
}

void PrintNormSetEquilibrium(const std::vector<std::string>& norm_labels,
                             const EvolPrivRepGame::norms_t& norms,
                             const EvolPrivRepGame::Parameters& params,
                             double benefit,
                             double beta,
                             nlohmann::json extra_fields = nlohmann::json::object()) {
  auto start = std::chrono::high_resolution_clock::now();

  int omp_threads = omp_get_max_threads();
  std::cerr << "Running with " << omp_threads << " threads" << std::endl;
  auto json_params = nlohmann::json(params);
  json_params["benefit"] = benefit;
  json_params["beta"] = beta;
  std::cerr << "Parameters:" << json_params.dump(2)  << std::endl;

  std::vector<std::string> norm_names;
  std::vector<int> norm_ids;
  std::vector<int> action_rule_ids;
  std::vector<double> monomorphic_coop_levels;
  norm_names.reserve(norms.size());
  norm_ids.reserve(norms.size());
  action_rule_ids.reserve(norms.size());
  monomorphic_coop_levels.reserve(norms.size());

  for (const auto& norm : norms) {
    norm_names.push_back(norm.GetName());
    norm_ids.push_back(norm.ID());
    action_rule_ids.push_back(norm.P.ID());
    monomorphic_coop_levels.push_back(EvolPrivRepGame::MonomorphicCooperationLevel(norm, params));
  }

  auto rhos = EvolPrivRepGame::FixationProbabilities(norms, params, benefit, beta);
  auto eq = EvolPrivRepGame::EquilibriumPopulationLowMut(rhos);

  double eq_cooperation_level = 0.0;
  for (size_t i = 0; i < eq.size(); i++) {
    eq_cooperation_level += eq[i] * monomorphic_coop_levels[i];
  }

  nlohmann::json out_j = {
    {"norms", norm_labels},
    {"norm_names", norm_names},
    {"norm_ids", norm_ids},
    {"action_rule_ids", action_rule_ids},
    {"monomorphic_coop_levels", monomorphic_coop_levels},
    {"rhos", rhos},
    {"eq", eq},
    {"eq_cooperation_level", eq_cooperation_level}
  };
  out_j.update(extra_fields);
  std::cout << out_j.dump(2) << std::endl;

  auto end = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> elapsed = end - start;
  std::cerr << "Elapsed time: " << elapsed.count() << " s\n";
}


void PrintActionRuleMutantEquilibrium(const Norm& norm, const EvolPrivRepGame::Parameters& params, double benefit, double beta) {
  std::vector<std::string> labels;
  auto variants = norm.ActionRuleVariants(true);
  labels.reserve(variants.size());
  for (const auto& variant : variants) {
    labels.push_back(std::to_string(variant.Rd.ID()) + "-" +
                     std::to_string(variant.Rr.ID()) + "-" +
                     std::to_string(variant.P.ID()));
  }

  nlohmann::json extra_fields = {
    {"resident", norm.GetName()},
    {"mode", "action_rule_mutants"}
  };
  PrintNormSetEquilibrium(labels, variants, params, benefit, beta, extra_fields);
}


void PrintStrategySetEquilibrium(const std::vector<std::string>& norm_args, const EvolPrivRepGame::Parameters& params, double benefit, double beta) {
  EvolPrivRepGame::norms_t norms;
  norms.reserve(norm_args.size());
  for (const auto& norm_arg : norm_args) {
    norms.push_back(Norm::ParseNormString(norm_arg));
  }

  PrintNormSetEquilibrium(norm_args, norms, params, benefit, beta);
}


void PrintCompetition(const Norm& n1, const Norm& n2, const EvolPrivRepGame::Parameters& params, double benefit, double beta) {
  auto start = std::chrono::high_resolution_clock::now();

  int omp_threads = omp_get_max_threads();
  std::cerr << "Running with " << omp_threads << " threads" << std::endl;
  auto json_params = nlohmann::json(params);
  json_params["benefit"] = benefit;
  json_params["beta"] = beta;
  std::cerr << "Parameters:" << json_params.dump(2)  << std::endl;

  auto rhoij_rhoji_pii_pij = EvolPrivRepGame::FixationProbabilityAndPayoff(n1, n2, params, benefit, beta);

  std::vector<std::vector<double>> rhos = { {0.0, std::get<0>(rhoij_rhoji_pii_pij)}, {std::get<1>(rhoij_rhoji_pii_pij), 0.0} };

  nlohmann::json out_j = {
    {"transition_prob:n1->n2", rhos[0][1]},
    {"transition_prob:n1<-n2", rhos[1][0]}
  };
  auto eq = EvolPrivRepGame::EquilibriumPopulationLowMut(rhos);
  out_j["equilibrium_population"] = eq;

  double pc_s1 = EvolPrivRepGame::MonomorphicCooperationLevel(n1, params);
  double pc_s2 = EvolPrivRepGame::MonomorphicCooperationLevel(n2, params);
  out_j["monomorphic_coop_levels"] = {pc_s1, pc_s2};
  std::cout << out_j.dump(2) << std::endl;

  std::ofstream fout("payoffs.dat");
  auto pi_i = std::get<2>(rhoij_rhoji_pii_pij);
  auto pi_j = std::get<3>(rhoij_rhoji_pii_pij);
  for (size_t l = 1; l < params.N; l++) {
    fout << l << " " << pi_i[l] << " " << pi_j[l] << std::endl;
  }
  fout.close();

  auto end = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> elapsed = end - start;
  std::cerr << "Elapsed time: " << elapsed.count() << " s\n";
}

int main(int argc, char *argv[]) {

  std::vector<std::string> args;
  nlohmann::json j = nlohmann::json::object();
  bool action_mutants = false;
  // -j param.json : set parameters used for evolutionary simulation by json file
  // -l : check local mutants
  for (int i = 1; i < argc; ++i) {
    if (CliJsonUtils::ConsumeJsonOption(argc, argv, i, "-j", j)) {
      continue;
    }
    else if (std::string(argv[i]) == "--action-mutants") {
      action_mutants = true;
    }
    else {
      args.emplace_back(argv[i]);
    }
  }

  // Validate JSON keys against default Parameters fields, plus optional benefit/beta
  try {
    CliJsonUtils::ValidateObjectKeys(j, CliJsonUtils::JsonKeysWithExtras(nlohmann::json(EvolPrivRepGame::Parameters{}), {"benefit", "beta"}));
  }
  catch (const std::exception& e) {
    std::cerr << "[Error] " << e.what() << std::endl;
    return 1;
  }

  EvolPrivRepGame::Parameters params = j.get<EvolPrivRepGame::Parameters>();
  // if j has a key "benefit" and "beta, use these as a benefit value
  double benefit = 5.0, beta = 1.0;
  if (j.contains("benefit")) {
    benefit = j["benefit"].get<double>();
  }
  if (j.contains("beta")) {
    beta = j["beta"].get<double>();
  }

  if (action_mutants && args.size() == 1) {
    Norm s = Norm::ParseNormString(args.at(0));
    PrintActionRuleMutantEquilibrium(s, params, benefit, beta);
  }
  else if (!action_mutants && args.size() == 1) {
    Norm s = Norm::ParseNormString(args.at(0));
    PrintSelectionMutationEquilibriumAllCAllD(s, params, benefit, beta);
  }
  else if (!action_mutants && args.size() == 2) {  // if two arguments are given, direct competition between two norms are shown
    Norm s1 = Norm::ParseNormString(args.at(0));
    Norm s2 = Norm::ParseNormString(args.at(1));
    PrintCompetition(s1, s2, params, benefit, beta);
  }
  else if (!action_mutants && args.size() >= 3) {
    PrintStrategySetEquilibrium(args, params, benefit, beta);
  }
  else {
    std::cerr << "Usage: " << argv[0] << " [options] <norm>\n";
    std::cerr << "       " << argv[0] << " [options] --action-mutants <norm>\n";
    std::cerr << "       " << argv[0] << " [options] <norm1> <norm2>\n";
    std::cerr << "       " << argv[0] << " [options] <norm1> <norm2> <norm3> [...]\n";
    std::cerr << "Options:\n";
    CliHelpUtils::PrintJsonOption(std::cerr);
    CliHelpUtils::PrintOption(std::cerr, "--action-mutants", "Evaluate resident plus all deterministic action-rule mutants");
    std::cerr << "Default parameters:\n";
    std::cerr << "  " << nlohmann::json(EvolPrivRepGame::Parameters{}).dump(2) << '\n';
    CliHelpUtils::PrintNormFormat(std::cerr);
    return 1;
  }

  return 0;
}
