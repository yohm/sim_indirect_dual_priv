#ifndef CLI_HELP_UTILS_HPP
#define CLI_HELP_UTILS_HPP

#include <iostream>
#include <string>

namespace CliHelpUtils {

inline constexpr const char* NormFormatHelp() {
  return "[Norm name] or [ID] or [0xHEX_ID] or [Rd-Rr-P] or [c1 c2 c3 c4 g1 g2 g3 g4 g5 g6 g7 g8 r1 r2 r3 r4]";
}

inline void PrintOption(std::ostream& out, const std::string& option, const std::string& description) {
  out << "  " << option;
  if (option.size() < 20) {
    out << std::string(20 - option.size(), ' ');
  }
  else {
    out << ' ';
  }
  out << description << '\n';
}

inline void PrintNormFormat(std::ostream& out) {
  out << "Norm format:\n";
  out << "  " << NormFormatHelp() << '\n';
}

inline void PrintJsonOption(std::ostream& out, const std::string& option = "-j <json|path>") {
  PrintOption(out, option, "Parameters JSON inline or file path");
}

}  // namespace CliHelpUtils

#endif
