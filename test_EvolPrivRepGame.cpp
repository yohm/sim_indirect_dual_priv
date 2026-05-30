#include <iostream>
#include <fstream>
#include <chrono>
#include <regex>
#include <algorithm>
#include <numeric>
#include <icecream.hpp>
#include <nlohmann/json.hpp>
#include "EvolPrivRepGame.hpp"

#include <gtest/gtest.h>


TEST(EvolPrivRepGame, AllC_AllD) {
  constexpr size_t t = 1e4;
  EvolPrivRepGame::Parameters params{50, t, t, 0.9, 0.0, 0.05, 0.0, 0.0, 1234};
  using evo = EvolPrivRepGame;

  Norm allc = Norm::AllC();
  Norm alld = Norm::AllD();
  auto rhos = evo::FixationProbabilities({allc, alld}, params, 5.0, 1.0);
  IC(rhos);
  // rhos: [[0, 0.667425], [2.39856e-24, 0]]
  EXPECT_NEAR(rhos[0][1], 0.667, 0.02);
  EXPECT_NEAR(rhos[1][0], 0.0, 0.02);

  auto eq = evo::EquilibriumPopulationLowMut(rhos);
  IC(eq);
  // eq: [0.0, 1.0]
  EXPECT_NEAR(eq[0], 0.0, 0.02);
  EXPECT_NEAR(eq[1], 1.0, 0.02);

  double pc_allc = EvolPrivRepGame::MonomorphicCooperationLevel({allc}, params);
  EXPECT_NEAR(pc_allc, 1.0, 0.02);

  double pc_alld = EvolPrivRepGame::MonomorphicCooperationLevel({alld}, params);
  EXPECT_NEAR(pc_alld, 0.0, 0.02);

  auto bc_probs = evo::BenefitCostProbs(allc, 20, alld, params);
  // bc_probs: [ {benefit_prob: 0.4, cost_prob: 1.0}, {benefit_prob: 0.4, cost_prob: 0.0} ]
  EXPECT_NEAR(bc_probs.first.benefit_prob, 0.4, 0.02);
  EXPECT_NEAR(bc_probs.first.cost_prob, 1.0, 0.02);
  EXPECT_NEAR(bc_probs.second.benefit_prob, 0.4, 0.02);
  EXPECT_NEAR(bc_probs.second.cost_prob, 0.0, 0.02);

  auto batch_rhos = evo::FixationProbabilityBatch(allc, alld, params, {{5.0, 1.0}, {1.1, 0.0001}});
  // batch_rhos[0] should equal to {0.667425, 0}
  // batch_rhos[1] should be neutral {0.02, 0.02}
  EXPECT_NEAR(batch_rhos[0].first, rhos[0][1], 0.02);
  EXPECT_NEAR(batch_rhos[0].second, rhos[1][0], 0.02);
  EXPECT_NEAR(batch_rhos[1].first, 0.02, 0.002);
  EXPECT_NEAR(batch_rhos[1].second, 0.02, 0.002);
}

TEST(EvolPrivRepGame, L1_AllC_AllD) {
  constexpr size_t t = 1e4;
  EvolPrivRepGame::Parameters params{50, t, t, 0.9, 0.0, 0.05, 0.0, 0.0, 1234};
  using evol = EvolPrivRepGame;

  double q_act = 0.9;
  Norm l1 = Norm::L1();
  Norm allc = Norm::AllC();
  Norm alld = Norm::AllD();
  auto rhos = evol::FixationProbabilities({l1, allc, alld}, params, 5.0, 1.0);
  // IC(rhos);
  // rhos: [
  // [0, 0.0976933, 4.47544e-29],
  // [0.0114276, 0, 0.668377],
  // [0.0444453, 2.16425e-24, 0]
  // ]

  EXPECT_NEAR(rhos[0][1], 0.097, 0.02);
  EXPECT_NEAR(rhos[0][2], 0.000, 0.02);
  EXPECT_NEAR(rhos[1][0], 0.012, 0.02);
  EXPECT_NEAR(rhos[2][0], 0.043, 0.02);
  EXPECT_NEAR(rhos[1][2], 0.668, 0.02);
  EXPECT_NEAR(rhos[2][1], 0.000, 0.02);

  auto eq = evol::EquilibriumPopulationLowMut(rhos);
  // IC(eq);
  // eq: [0.302589, 0.0434844, 0.653927]
  EXPECT_NEAR(eq[0], 0.30, 0.02);
  EXPECT_NEAR(eq[1], 0.04, 0.02);
  EXPECT_NEAR(eq[2], 0.66, 0.02);

  auto eq2 = evol::EquilibriumPopulationLowMutPowerMethod(rhos);
  // IC(eq2);
  EXPECT_NEAR(eq2[0], 0.30, 0.02);
  EXPECT_NEAR(eq2[1], 0.04, 0.02);
  EXPECT_NEAR(eq2[2], 0.66, 0.02);

  auto pc_l1 = evol::MonomorphicCooperationLevel({l1}, params);
  // IC(pc_l1);
  // pc_l1: 0.903
  EXPECT_NEAR(pc_l1, 0.90, 0.02);
}

TEST(EvolPrivRepGameAllCAllD, L1) {
  constexpr size_t t = 1e4;
  EvolPrivRepGame::Parameters params{50, t, t, 0.9, 0.0, 0.05, 0.0, 0.0, 1234};

  Norm l1 = Norm::L1();
  auto selfc_rho_eq = EvolPrivRepGame::EquilibriumCoopLevelAllCAllD(l1, params, 5.0, 1.0);
  double self_cooperation_level = std::get<0>(selfc_rho_eq);
  auto rhos = std::get<1>(selfc_rho_eq);
  auto eq = std::get<2>(selfc_rho_eq);

  // IC(self_cooperation_level, rhos, eq);
  // ic| self_cooperation_level: 0.90224
  // ic| rhos: [
  // [0, 0.0933583, 4.4365e-29],
  // [0.0120976, 0, 0.670243],
  // [0.0453502, 2.35795e-24, 0]
  // ]
  // ic| eq: [0.316563, 0.0433123, 0.640125]

  EXPECT_NEAR(self_cooperation_level, 0.90, 0.02);
  EXPECT_NEAR(rhos[0][1], 0.097, 0.02);
  EXPECT_NEAR(rhos[0][2], 0.000, 0.02);
  EXPECT_NEAR(rhos[1][0], 0.012, 0.02);
  EXPECT_NEAR(rhos[1][2], 0.670, 0.02);
  EXPECT_NEAR(rhos[2][0], 0.043, 0.02);
  EXPECT_NEAR(rhos[2][1], 0.000, 0.02);
  EXPECT_NEAR(eq[0], 0.30, 0.02);
  EXPECT_NEAR(eq[1], 0.04, 0.02);
  EXPECT_NEAR(eq[2], 0.66, 0.02);
}

TEST(EvolPrivRepGame, ActionRuleVariants) {
  EvolPrivRepGame::Parameters params{12, 100, 100, 0.9, 0.0, 0.05, 0.0, 0.0, 1234};

  Norm resident = Norm::L1();
  auto variants = resident.ActionRuleVariants(true);

  ASSERT_EQ(variants.size(), 16);
  EXPECT_EQ(variants.front().P, resident.P);
  for (size_t i = 1; i < variants.size(); i++) {
    EXPECT_EQ(variants[i].Rd, resident.Rd);
    EXPECT_EQ(variants[i].Rr, resident.Rr);
    EXPECT_NE(variants[i].P, resident.P);
  }

  std::vector<int> action_rule_ids;
  action_rule_ids.reserve(variants.size());
  for (const auto& variant : variants) {
    action_rule_ids.push_back(variant.P.ID());
  }

  auto fixation_probs = EvolPrivRepGame::FixationProbabilities(variants, params, 5.0, 1.0);
  auto equilibrium_population = EvolPrivRepGame::EquilibriumPopulationLowMut(fixation_probs);
  ASSERT_EQ(fixation_probs.size(), 16);
  ASSERT_EQ(equilibrium_population.size(), 16);

  EXPECT_EQ(action_rule_ids.front(), resident.P.ID());
  EXPECT_NE(std::find(action_rule_ids.begin(), action_rule_ids.end(), 5), action_rule_ids.end());

  for (const auto& row : fixation_probs) {
    ASSERT_EQ(row.size(), 16);
  }

  double eq_sum = std::accumulate(equilibrium_population.begin(), equilibrium_population.end(), 0.0);
  EXPECT_NEAR(eq_sum, 1.0, 1.0e-8);
}
