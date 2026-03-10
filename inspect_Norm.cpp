#include <iostream>
#include <cassert>
#include <icecream.hpp>
#include <bitset>
#include <regex>
#include <vector>
#include <set>
#include "CliHelpUtils.hpp"
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
    std::cerr << "Usage: " << argv[0] << " [options] <norm> [other norms]\n";
    std::cerr << "Options:" << std::endl;
    CliHelpUtils::PrintOption(std::cerr, "-s", "Swap good and bad labels");
    CliHelpUtils::PrintNormFormat(std::cerr);
    return 1;
  }

  return 0;
}
