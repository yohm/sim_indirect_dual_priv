#include <iostream>
#include <cassert>
#include <icecream.hpp>
#include <bitset>
#include <regex>
#include <vector>
#include <set>
#include "Norm.hpp"

constexpr Reputation B = Reputation::B, G = Reputation::G;
constexpr Action C = Action::C, D = Action::D;

int main(int argc, char** argv) {

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
    Norm n = Norm::ParseNormString(args[0], swap_gb);
    std::cout << n.Inspect();
  }
  else if (args.size() >= 2) {
    Norm n = Norm::ParseNormString(args[0], swap_gb);
    // loop over the other norms
    for (size_t i = 1; i < args.size(); ++i) {
      Norm n2 = Norm::ParseNormString(args[i], swap_gb);
      std::cout << n.InspectComparison(n2);
    }
  }
  else {   // no arguments
    std::cerr << "Usage: " << argv[0] << " [options] norm [other norms]" << std::endl;
    std::cerr << "Options:" << std::endl;
    std::cerr << "  -s         : swap G and B" << std::endl;
    std::cerr << "Norm format: [Norm name] or [ID] or [0xHEX_ID] or [Rd-Rr-P] or [c1 c2 c3 c4 g1 g2 g3 g4 g5 g6 g7 g8 r1 r2 r3 r4]" << std::endl;
    return 0;
  }

  return 0;
}
