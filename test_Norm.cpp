#include <iostream>
#include <icecream.hpp>
#include <bitset>
#include <regex>
#include <vector>
#include <set>
#include "Norm.hpp"

#include <gtest/gtest.h>

constexpr Reputation B = Reputation::B, G = Reputation::G;
constexpr Action C = Action::C, D = Action::D;

TEST(ActionRule, action_rules) {
  ActionRule P({0.1, 0.2, 0.5, 0.9});
  // std::cout << P.Inspect();

  EXPECT_DOUBLE_EQ( P.CProb(Reputation::B, Reputation::B), 0.1 );
  EXPECT_DOUBLE_EQ( P.CProb(Reputation::G, Reputation::B), 0.5 );
  EXPECT_FALSE(P.IsSecondOrder());

  P.SetCProb(Reputation::B, Reputation::G, 0.3);
  EXPECT_DOUBLE_EQ( P.CProb(Reputation::B, Reputation::G), 0.3 );

  ActionRule P2 = P.SwapGB();
  EXPECT_DOUBLE_EQ( P2.CProb(Reputation::G, Reputation::G), 0.1 );
  EXPECT_DOUBLE_EQ( P2.CProb(Reputation::B, Reputation::G), 0.5 );

  ActionRule P3({0.0, 1.0, 0.0, 1.0});
  // std::cout << P3.Inspect();
  EXPECT_TRUE( P3.IsDeterministic() );
  EXPECT_EQ( P3.ID(), 10 );
  EXPECT_TRUE( P3.IsSecondOrder() );

  auto disc = ActionRule::DISC();
  EXPECT_TRUE( disc.IsDeterministic() );
  EXPECT_EQ( disc.ID(), 10 );
  auto allc = ActionRule::ALLC();
  EXPECT_TRUE( allc.IsDeterministic() );
  EXPECT_EQ( allc.ID(), 15 );

  auto alld = ActionRule::ALLD();
  EXPECT_TRUE( alld.IsDeterministic() );
  EXPECT_EQ( alld.ID(), 0 );

  auto P4 = ActionRule::MakeDeterministicRule(7);
  EXPECT_TRUE( P4.IsDeterministic() );
  EXPECT_EQ( P4.ID(), 7 );

  // initialize by tables
  ActionRule P5({
    { {G,G}, 0.1 },
    { {G,B}, 0.2 },
    { {B,G}, 0.3 },
    { {B,B}, 0.4 },
  });

  EXPECT_DOUBLE_EQ( P5.CProb(Reputation::G, Reputation::G), 0.1 );
  EXPECT_DOUBLE_EQ( P5.CProb(Reputation::G, Reputation::B), 0.2 );
  EXPECT_DOUBLE_EQ( P5.CProb(Reputation::B, Reputation::G), 0.3 );
  EXPECT_DOUBLE_EQ( P5.CProb(Reputation::B, Reputation::B), 0.4 );
}

TEST(AssessmentRule, assessment_rules) {
  AssessmentRule R({0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8});
  // std::cout << R.Inspect();

  EXPECT_DOUBLE_EQ( R.GProb(Reputation::B, Reputation::B, Action::D), 0.1 );
  EXPECT_DOUBLE_EQ( R.GProb(Reputation::B, Reputation::B, Action::C), 0.2 );
  EXPECT_DOUBLE_EQ( R.GProb(Reputation::G, Reputation::B, Action::C), 0.6 );
  EXPECT_FALSE(R.IsSecondOrder());

  R.SetGProb(Reputation::B, Reputation::G, Action::C, 0.9);
  EXPECT_DOUBLE_EQ( R.GProb(Reputation::B, Reputation::G, Action::C), 0.9 );

  AssessmentRule R2 = R.SwapGB();
  EXPECT_DOUBLE_EQ( R2.GProb(Reputation::G, Reputation::G, Action::C), 1.0 - R.GProb(Reputation::B, Reputation::B, Action::C) );

  AssessmentRule Q3({0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0});
  EXPECT_TRUE( Q3.IsDeterministic() );
  EXPECT_EQ( Q3.ID(), 0b10101010 );
  EXPECT_TRUE( Q3.IsSecondOrder() );

  auto allg = AssessmentRule::AllGood();
  EXPECT_TRUE( allg.IsDeterministic() );
  EXPECT_EQ( allg.ID(), 0b11111111 );
  auto allb = AssessmentRule::AllBad();
  EXPECT_TRUE( allb.IsDeterministic() );
  EXPECT_EQ( allb.ID(), 0b00000000 );
  auto is = AssessmentRule::ImageScoring();
  EXPECT_TRUE( is.IsDeterministic() );
  EXPECT_EQ( is.ID(), 0b10101010 );

  AssessmentRule Q4({
    {{G,G,C}, 0.1},
    {{G,G,D}, 0.2},
    {{G,B,C}, 0.3},
    {{G,B,D}, 0.4},
    {{B,G,C}, 0.5},
    {{B,G,D}, 0.6},
    {{B,B,C}, 0.7},
    {{B,B,D}, 0.8}
  });
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::G, Reputation::G, Action::C), 0.1 );
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::G, Reputation::G, Action::D), 0.2 );
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::G, Reputation::B, Action::C), 0.3 );
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::G, Reputation::B, Action::D), 0.4 );
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::B, Reputation::G, Action::C), 0.5 );
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::B, Reputation::G, Action::D), 0.6 );
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::B, Reputation::B, Action::C), 0.7 );
  EXPECT_DOUBLE_EQ( Q4.GProb(Reputation::B, Reputation::B, Action::D), 0.8 );
}

TEST(Norm, base) {
  // ActionRule p = ActionRule::DISC();
  // AssessmentRule r1 = AssessmentRule::ImageScoring();
  // AssessmentRule r2 = AssessmentRule::AllGood();
  // std::cout << Norm(r1, r2, p).Inspect();

  Norm n(
      {{0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7}},
      {{0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9}},
      {{0.0, 0.25, 0.5, 0.75}}
  );
  EXPECT_FALSE(n.IsDeterministic());
  EXPECT_FALSE(n.IsSecondOrder());
  EXPECT_FALSE(n.IsRecipKeep());
  EXPECT_DOUBLE_EQ(n.GProbDonor(Reputation::B, Reputation::G, Action::C), 0.3);
  EXPECT_DOUBLE_EQ(n.GProbRecip(Reputation::B, Reputation::G, Action::C), 0.5);
  EXPECT_DOUBLE_EQ(n.CProb(Reputation::B, Reputation::G), 0.25);
  // std::cout << n.Inspect();
}

TEST(Norm, ImageScoring) {
  Norm is = Norm::ImageScoring();
  EXPECT_TRUE( is.IsRecipKeep() );
  EXPECT_TRUE( is.IsDeterministic() );
  EXPECT_TRUE( is.IsSecondOrder() );
  EXPECT_EQ( is.ID(), 0b10101010'11001100'1010);
  EXPECT_EQ( is.IDwithoutR2(), 0b10101010'1010);
}

TEST(Norm, AllG) {
  Norm allg = Norm::AllG();
  EXPECT_TRUE( allg.IsRecipKeep() );
  EXPECT_TRUE( allg.IsDeterministic() );
  EXPECT_TRUE( allg.IsSecondOrder() );
  EXPECT_EQ( allg.ID(), 0b11111111'11001100'1010);
  EXPECT_EQ( allg.IDwithoutR2(), 0b11111111'1010);
}

TEST(Norm, AllB) {
  Norm allb = Norm::AllB();
  EXPECT_TRUE( allb.IsRecipKeep() );
  EXPECT_TRUE( allb.IsDeterministic() );
  EXPECT_TRUE( allb.IsSecondOrder() );
  EXPECT_EQ( allb.ID(), 0b00000000'11001100'1010);
  EXPECT_EQ( allb.IDwithoutR2(), 0b00000000'1010);
}

TEST(Norm, LeadingEight) {
  std::array<Norm, 8> leading_eight = {Norm::L1(), Norm::L2(), Norm::L3(), Norm::L4(),
                                       Norm::L5(), Norm::L6(), Norm::L7(), Norm::L8()};
  std::array<int, 8> l8_ids =
      {0b10111010'11001100'1011, 0b10011010'11001100'1011, 0b10111011'11001100'1010, 0b10111001'11001100'1010,
       0b10011011'11001100'1010, 0b10011001'11001100'1010, 0b10111000'11001100'1010, 0b10011000'11001100'1010
      };
  std::array<int, 8> l8_ids_withoutR2 =
      {0b10111010'1011, 0b10011010'1011, 0b10111011'1010, 0b10111001'1010,
       0b10011011'1010, 0b10011001'1010, 0b10111000'1010, 0b10011000'1010
      };
  for (size_t i = 0; i < 8; i++) {
    auto l = leading_eight[i];
    // std::cout << "L" << i + 1 << " : " << l.Inspect();
    EXPECT_TRUE( l.IsDeterministic() );
    EXPECT_TRUE( l.IsRecipKeep() );
    if (i == 2 || i == 5) {
      EXPECT_TRUE( l.IsSecondOrder() );
    } else {
      EXPECT_FALSE( l.IsSecondOrder() );
    }
    EXPECT_EQ( l.GetName(), ("L" + std::to_string(i + 1)));
    EXPECT_EQ( l.ID(), l8_ids[i] );
    EXPECT_EQ( l.IDwithoutR2(), l8_ids_withoutR2[i] );
    EXPECT_EQ( Norm::ConstructFromID(l.ID()), l );
    EXPECT_EQ( Norm::ConstructFromIDwithoutR2(l.IDwithoutR2()), l );

    EXPECT_DOUBLE_EQ( l.CProb(Reputation::G, Reputation::G), 1.0 );
    EXPECT_DOUBLE_EQ( l.CProb(Reputation::G, Reputation::B), 0.0 );
    EXPECT_DOUBLE_EQ( l.CProb(Reputation::B, Reputation::G), 1.0 );
    EXPECT_DOUBLE_EQ( l.GProbDonor(Reputation::G, Reputation::G, Action::C), 1.0 );
    EXPECT_DOUBLE_EQ( l.GProbDonor(Reputation::G, Reputation::G, Action::D), 0.0 );  // identification of defectors
    EXPECT_DOUBLE_EQ( l.GProbDonor(Reputation::B, Reputation::G, Action::D), 0.0 );  // identification of defectors
    EXPECT_DOUBLE_EQ( l.GProbDonor(Reputation::G, Reputation::B, Action::D), 1.0 );  // justified punishment
    EXPECT_DOUBLE_EQ( l.GProbDonor(Reputation::B, Reputation::G, Action::C), 1.0 );  // apology

    Norm similar = l;
    similar.Rr.SetGProb(Reputation::G, Reputation::G, Action::C, 0.5);
    EXPECT_EQ( similar.PR1_Name(), l.GetName() );
  }
}

TEST(Norm, SecondarySixteen) {
  std::vector<Norm> secondary_sixteen;
  for (int i = 1; i <= 16; i++) {
    secondary_sixteen.push_back(Norm::SecondarySixteen(i));
  }

  for (const Norm& n: secondary_sixteen) {
    std::string name = n.GetName();
    std::regex word_regex("(S[1-9]|S1[0-6])");
    EXPECT_TRUE(std::regex_match(name, word_regex));

    EXPECT_TRUE(n.IsDeterministic());
    EXPECT_TRUE(n.IsRecipKeep());
    EXPECT_EQ(Norm::ConstructFromID(n.ID()), n);

    // test common prescriptions
    EXPECT_DOUBLE_EQ( n.CProb(G, G), 1.0 );
    EXPECT_DOUBLE_EQ( n.CProb(G, B), 0.0 );
    EXPECT_DOUBLE_EQ( n.CProb(B, G), 0.0 );
    EXPECT_DOUBLE_EQ( n.GProbDonor(G, G, C), 1.0 );
    EXPECT_DOUBLE_EQ( n.GProbDonor(G, G, D), 0.0 );
    EXPECT_DOUBLE_EQ( n.GProbDonor(G, B, D), 1.0 );
    EXPECT_DOUBLE_EQ( n.GProbDonor(B, G, D), 1.0 );

    if (n.GProbDonor(B,B,C) == 1 && n.GProbDonor(B,B,D) == 0) {
      EXPECT_DOUBLE_EQ( n.CProb(B, B), 1.0 );
    } else {
      EXPECT_DOUBLE_EQ( n.CProb(B, B), 0.0 );
    }
  }
}

TEST(Norm, rescaling) {
  Norm n = Norm::L6();
  auto rescaled = n.RescaleWithError(0.1, 0.02, 0.0);
  // std::cout << "rescaled: " << rescaled.Inspect() << std::endl;
  auto expected1 = std::array<double,4>{0.0, 0.9, 0.0, 0.9};
  for (int i = 0; i < 4; i++) {
    EXPECT_DOUBLE_EQ( rescaled.P.coop_probs[i], expected1[i] );
  }
  auto expected2 = std::array<double,8>{0.98, 0.02, 0.02, 0.98, 0.98, 0.02, 0.02, 0.98};
  for (int i = 0; i < 8; i++) {
    EXPECT_DOUBLE_EQ( rescaled.Rd.good_probs[i], expected2[i] );
  }
  auto expected3 = std::array<double,8>{0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0};
  for (int i = 0; i < 8; i++) {
    EXPECT_DOUBLE_EQ( rescaled.Rr.good_probs[i], expected3[i] );
  }
}

TEST(Norm, GenerousScoring) {
  Norm gsco = Norm::GenerousScoring(5.0);
  EXPECT_TRUE( gsco.IsGenerousScoring() );
  std::string name = gsco.GetName();
  EXPECT_EQ( name, "GSCO-5.0" );

  gsco.Rd.good_probs[0] = 0.5;
  EXPECT_FALSE( gsco.IsGenerousScoring() );

  gsco = Norm::GenerousScoring(1.5);
  EXPECT_EQ( gsco.GetName(), "GSCO-1.5" );

  Norm n = Norm::ConstructFromName("GSCO-1.5");
  EXPECT_TRUE( n.IsGenerousScoring() );
  EXPECT_EQ(n.GetName(), "GSCO-1.5");
  EXPECT_DOUBLE_EQ( n.Rd.good_probs[0], 2.0/3.0 );
}

TEST(Norm, Deterministic2ndOrder) {
  std::vector<Norm> norms = Norm::Deterministic2ndOrderWithoutR2Norms();
  std::set<int> ids;
  for (const Norm& n: norms) {
    EXPECT_TRUE(n.IsDeterministic());
    EXPECT_TRUE(n.IsRecipKeep());
    EXPECT_TRUE(n.IsSecondOrder());
    ids.insert(n.ID());
  }
  EXPECT_EQ( norms.size(), 36 );
  EXPECT_EQ( ids.size(), 36 );
}

TEST(Norm, Determinisitic3rdOrder) {
  std::vector<Norm> norms = Norm::Deterministic3rdOrderWithoutR2Norms();
  std::set<int> ids;
  std::vector<Norm> alld_vec, allc_vec;

  for (const Norm& n: norms) {
    EXPECT_TRUE(n.IsDeterministic());
    EXPECT_TRUE(n.IsRecipKeep());
    ids.insert(n.ID());
    if (n.P == ActionRule::ALLC()) {
      allc_vec.push_back(n);
    }
    else if (n.P == ActionRule::ALLD()) {
      alld_vec.push_back(n);
    }
  }
  EXPECT_EQ( norms.size(), 2080 );    // # of self-symmetric = 64, (4096 - 64)/2 + 64 = 2080
  EXPECT_EQ( ids.size(), 2080 );
  EXPECT_EQ( allc_vec.size(), 136 );  // # of self-symmetric = 16, thus (256-16)/2 + 16 = 136
  EXPECT_EQ( alld_vec.size(), 136 );
}

TEST(Norm, Deterministic2ndOrderWithR2) {
  std::vector<Norm> norms = Norm::Deterministic2ndOrderWithR2Norms();
  std::set<int> ids;
  std::set<int> self_symmetric;
  for (const Norm& n: norms) {
    EXPECT_TRUE(n.IsDeterministic());
    EXPECT_TRUE(n.IsSecondOrder());
    ids.insert(n.ID());
    if (n.SwapGB().ID() == n.ID()) {
      self_symmetric.insert(n.ID());
    }
  }
  EXPECT_EQ( norms.size(), 528 );
  EXPECT_EQ( ids.size(), 528 );
  EXPECT_EQ( self_symmetric.size(), 32 );
}

TEST(Norm, ParseNormString) {
  EXPECT_EQ( Norm::ParseNormString("AllG").GetName(), "AllG" );
  EXPECT_EQ( Norm::ParseNormString("L1").GetName(), "L1" );
  EXPECT_EQ( Norm::ParseNormString("S16").GetName(), "S16" );

  EXPECT_EQ( Norm::ParseNormString("GSCO-1.5").GetName(), "GSCO-1.5" );
  EXPECT_EQ( Norm::ParseNormString("857181").ID(), 857181 );
  EXPECT_EQ( Norm::ParseNormString("0xd145d").ID(), 857181 );
  EXPECT_EQ( Norm::ParseNormString("857181", true).ID(), 0xb8aeb );

  // New Rd-Rr-P triplet format for deterministic norms
  // Example: Rd=128, Rr=132, P=2
  Norm trip = Norm::ParseNormString("128-132-2");
  int expected_id = (128 << 12) + (132 << 4) + 2;
  EXPECT_TRUE(trip.IsDeterministic());
  EXPECT_EQ(trip.ID(), expected_id);
  EXPECT_EQ(trip.Rd.ID(), 128);
  EXPECT_EQ(trip.Rr.ID(), 132);
  EXPECT_EQ(trip.P.ID(), 2);
  // Inspect string should include the triplet format
  std::string trip_inspect = trip.Inspect();
  EXPECT_NE(trip_inspect.find("128-132-2"), std::string::npos);

  // Serialized format: [P(gg), P(gb), P(bg), P(bb)] [Rd reversed 8] [Rr reversed 8]
  // Choose values to satisfy assertions below:
  //   P: CProb(G,G)=1, CProb(G,B)=0, CProb(B,G)=1, CProb(B,B)=0
  //   Rd: GProbDonor(G,G,C)=0.8, GProbDonor(B,B,D)=0.1
  //   Rr: GProbRecip(G,G,C)=0.1, GProbRecip(B,B,D)=0.8
  const std::string s =
      "1.0 0.0 1.0 0.0 "
      "0.8 0.7 0.6 0.5 0.4 0.3 0.2 0.1 "
      "0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8";
  Norm n = Norm::ParseNormString(s);
  EXPECT_DOUBLE_EQ( n.CProb(G, G), 1.0 );
  EXPECT_DOUBLE_EQ( n.CProb(G, B), 0.0 );
  EXPECT_DOUBLE_EQ( n.CProb(B, G), 1.0 );
  EXPECT_DOUBLE_EQ( n.CProb(B, B), 0.0 );
  EXPECT_DOUBLE_EQ( n.GProbDonor(G, G, C), 0.8 );
  EXPECT_DOUBLE_EQ( n.GProbDonor(B, B, D), 0.1 );
  EXPECT_DOUBLE_EQ( n.GProbRecip(G, G, C), 0.1 );
  EXPECT_DOUBLE_EQ( n.GProbRecip(B, B, D), 0.8 );
}
