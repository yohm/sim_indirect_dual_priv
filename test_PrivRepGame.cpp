#include <iostream>
#include <fstream>
#include <regex>
#include <icecream.hpp>
#include "InvasionAnalysis.hpp"
#include "PrivRepGame.hpp"

#include <gtest/gtest.h>

void test_SelfCooperationLevel(const Norm& norm, double expected_c_level, double expected_good_rep) {
  PrivateRepGame priv_game( {{norm, 50}}, 123456789ull);
  priv_game.Update(1e3, 0.9, 0.0, 0.05, 0.0, 0.0, false);
  priv_game.ResetCounts();
  priv_game.Update(1e3, 0.9, 0.0, 0.05, 0.0, 0.0, true);
  // IC( priv_game.NormCooperationLevels(), priv_game.NormAverageReputation() );
  EXPECT_NEAR( priv_game.SystemWideCooperationLevel(), expected_c_level, 0.02);
  EXPECT_NEAR( priv_game.NormCooperationLevels()[0][0], expected_c_level, 0.02);
  EXPECT_NEAR( priv_game.NormAverageReputation()[0][0], expected_good_rep, 0.02);
}

TEST(SelfCooperationLevel, RandomNorm) {
  test_SelfCooperationLevel(Norm::Random(), 0.5, 0.5);
}

TEST(SelfCooperationLevel, LeadingEight) {
  test_SelfCooperationLevel(Norm::L1(), 0.90, 0.90);
  test_SelfCooperationLevel(Norm::L2(), 0.66, 0.65);
  test_SelfCooperationLevel(Norm::L3(), 0.90, 0.90);
  test_SelfCooperationLevel(Norm::L4(), 0.90, 0.90);
  test_SelfCooperationLevel(Norm::L5(), 0.70, 0.70);
  test_SelfCooperationLevel(Norm::L6(), 0.50, 0.50);
  test_SelfCooperationLevel(Norm::L7(), 0.88, 0.88);
  test_SelfCooperationLevel(Norm::L8(), 0.0, 0.0);
}

TEST(PrivateRepGame, RandomNonIdenticalPermutations) {
  PrivateRepGame priv_game({{Norm::Random(), 3}}, 123456789ull);
  for (int t = 0; t < 100; t++) {
    std::mt19937_64 rng(123456789ull + t);
    auto [perm1, perm2] = priv_game.RandomNonIdenticalPermutations(2, rng);
    EXPECT_EQ(perm1.size(), 2);
    EXPECT_EQ(perm2.size(), 2);
    std::set<size_t> s1, s2;
    for (int i = 0; i < perm1.size(); i++) {
      EXPECT_NE(perm1[i], perm2[i]);
      s1.insert(perm1[i]);
      s2.insert(perm2[i]);
    }
    EXPECT_EQ(s1.size(), 2);
    EXPECT_EQ(s2.size(), 2);
  }
  for (int t = 0; t < 100; t++) {
    std::mt19937_64 rng(123456789ull + t);
    auto [perm1, perm2] = priv_game.RandomNonIdenticalPermutations(3, rng);
    EXPECT_EQ(perm1.size(), 3);
    EXPECT_EQ(perm2.size(), 3);
    std::set<size_t> s1, s2;
    for (int i = 0; i < perm1.size(); i++) {
      EXPECT_NE(perm1[i], perm2[i]);
      s1.insert(perm1[i]);
      s2.insert(perm2[i]);
    }
    EXPECT_EQ(s1.size(), 3);
    EXPECT_EQ(s2.size(), 3);
  }
  for (int t = 0; t < 100; t++) {
    std::mt19937_64 rng(123456789ull + t);
    auto [perm1, perm2] = priv_game.RandomNonIdenticalPermutations(50, rng);
    EXPECT_EQ(perm1.size(), 50);
    EXPECT_EQ(perm2.size(), 50);
    std::set<size_t> s1, s2;
    for (int i = 0; i < perm1.size(); i++) {
      EXPECT_NE(perm1[i], perm2[i]);
      s1.insert(perm1[i]);
      s2.insert(perm2[i]);
    }
    EXPECT_EQ(s1.size(), 50);
    EXPECT_EQ(s2.size(), 50);
  }
}

TEST(InvasionAnalysis, ThresholdsAndCommonRange) {
  auto lower_bound = ComputeInvasionThresholds({{0.8, 0.2}, {0.5, 0.0}});
  ASSERT_TRUE(lower_bound.bc_min.has_value());
  EXPECT_NEAR(lower_bound.bc_min.value(), 1.0, 1.0e-12);
  EXPECT_FALSE(lower_bound.bc_max.has_value());

  auto upper_bound = ComputeInvasionThresholds({{0.5, 0.8}, {0.9, 0.0}});
  ASSERT_TRUE(upper_bound.bc_min.has_value());
  ASSERT_TRUE(upper_bound.bc_max.has_value());
  EXPECT_NEAR(upper_bound.bc_min.value(), 1.0, 1.0e-12);
  EXPECT_NEAR(upper_bound.bc_max.value(), 4.0 / 3.0, 1.0e-12);

  auto common = CombineInvasionThresholds({lower_bound});
  EXPECT_TRUE(common.stable);
  EXPECT_NEAR(common.bc_min, 1.0, 1.0e-12);
  EXPECT_FALSE(common.bc_max.has_value());
}
