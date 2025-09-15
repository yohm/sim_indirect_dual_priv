#include <iostream>
#include <regex>
#include <cassert>
#include <icecream.hpp>
#include "PublicRepGame.hpp"


void PrintESSRange(const Norm& norm) {
  double mu_e = 0.001, mu_a_donor = 0.001, mu_a_recip = 0.001;
  PublicRepGame g(mu_e, mu_a_donor, mu_a_recip, norm);
  std::cerr << g.r_norm.Inspect();
  std::cerr << "h*: " << g.h_star << ", pc_res_res: " << g.pc_res_res << std::endl;

  ActionRule alld = ActionRule::ALLD();
  auto br_alld = g.StableBenefitRangeAgainstMutant(alld);
  std::cerr << "stable benefit range against ALLD: " << br_alld[0] << ", " << br_alld[1] << std::endl;
  ActionRule allc = ActionRule::ALLC();
  auto br_allc = g.StableBenefitRangeAgainstMutant(allc);
  std::cerr << "stable benefit range against ALLC: " << br_alld[0] << ", " << br_alld[1] << std::endl;

  auto br = g.ESSBenefitRange();
  std::cerr << "ESS b_range: " << br[0] << ", " << br[1] << std::endl;
}

int main(int argc, char* argv[]) {

  std::vector<std::string> args;
  bool swap_gb = false;
  for (int i = 1; i < argc; ++i) {
    if (std::string(argv[i]) == "-s") {
      swap_gb = true;
    }
    else {
      args.emplace_back(argv[i]);
    }
  }

  if (args.size() == 1) {
    Norm n = Norm::ParseNormString(argv[1], swap_gb);
    PrintESSRange(n);
  }
  else {
    std::cerr << "Usage: " << argv[0] << " [-s] <norm_string>" << std::endl;
    std::cerr << "  -s: swap good/bad" << std::endl;
    std::cerr << "Norm format: [Norm name] or [ID] or [0xHEX_ID] or [Rd-Rr-P] or [c1 c2 c3 c4 g1 g2 g3 g4 g5 g6 g7 g8 r1 r2 r3 r4]" << std::endl;

    return 1;
  }

  return 0;
}
