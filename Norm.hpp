#ifndef NORM_HPP
#define NORM_HPP

#include <iostream>
#include <iomanip>
#include <string>
#include <sstream>
#include <vector>
#include <array>
#include <map>
#include <algorithm>
#include <cstdint>
#include <regex>


enum class Action {
  D = 0,  // defect
  C = 1   // cooperate
};

Action FlipAction(Action a) {
  if (a == Action::C) { return Action::D; }
  else { return Action::C; }
}

enum class Reputation {
  B = 0,   // bad
  G = 1    // good
};

Reputation FlipReputation(Reputation r) {
  if (r == Reputation::G) { return Reputation::B; }
  else { return Reputation::G; }
}

char A2C(Action a) {
  if (a == Action::D) { return 'd'; }
  else { return 'c'; }
}
Action C2A(char c) {
  if (c == 'd') { return Action::D; }
  else if (c == 'c') { return Action::C; }
  else { throw std::runtime_error("invalid character for action"); }
}
char R2C(Reputation r) {
  if (r == Reputation::B) { return 'B'; }
  else { return 'G'; }
}
Reputation C2R(char c) {
  if (c == 'B') { return Reputation::B; }
  else if (c == 'G') { return Reputation::G; }
  else { throw std::runtime_error("invalid character for action"); }
}
std::ostream &operator<<(std::ostream &os, const Action &act) {
  os << A2C(act);
  return os;
}
std::ostream &operator<<(std::ostream &os, const Reputation &rep) {
  os << R2C(rep);
  return os;
}

class ActionRule {
  public:
  ActionRule(const std::array<double,4>& coop_probs) : coop_probs(coop_probs) {};
  // {P(C|B,B), P(C|B,G), P(C|G,B), P(C|G,G)}

  ActionRule(const std::map<std::pair<Reputation,Reputation>,double>& actions) {
    // { (B,B,P(B,B)), (B,G,P(B,G)), (G,B,P(G,B)), (G,G,P(G,G)) }
    if (actions.size() != 4) {
      throw std::runtime_error("unspecified actions");
    }
    coop_probs[0] = actions.at({Reputation::B, Reputation::B});
    coop_probs[1] = actions.at({Reputation::B, Reputation::G});
    coop_probs[2] = actions.at({Reputation::G, Reputation::B});
    coop_probs[3] = actions.at({Reputation::G, Reputation::G});
  }
  ActionRule(const std::map<std::pair<Reputation,Reputation>,Action>& actions) {
    // { (B,B,D), (B,G,C), (G,B,D), (G,G,C) }
    if (actions.size() != 4) {
      throw std::runtime_error("unspecified actions");
    }
    coop_probs[0] = actions.at({Reputation::B, Reputation::B}) == Action::C ? 1.0 : 0.0;
    coop_probs[1] = actions.at({Reputation::B, Reputation::G}) == Action::C ? 1.0 : 0.0;
    coop_probs[2] = actions.at({Reputation::G, Reputation::B}) == Action::C ? 1.0 : 0.0;
    coop_probs[3] = actions.at({Reputation::G, Reputation::G}) == Action::C ? 1.0 : 0.0;
  }

  std::array<double,4> coop_probs; // P(C|B,B), P(C|B,G), P(C|G,B), P(C|G,G)

  ActionRule Clone() const { return ActionRule(coop_probs); }

  double CProb(const Reputation& rep_d, const Reputation& rep_r) const {
    size_t idx = static_cast<size_t>(rep_d) * 2 + static_cast<size_t>(rep_r);
    return coop_probs[idx];
  }
  void SetCProb(const Reputation& rep_d, const Reputation& rep_r, double c_prob) {
    size_t idx = static_cast<size_t>(rep_d) * 2 + static_cast<size_t>(rep_r);
    coop_probs[idx] = c_prob;
  }
  ActionRule SwapGB() const { // returns a new action rule with G and B swapped
    std::array<double,4> new_coop_probs = {coop_probs[3], coop_probs[2], coop_probs[1], coop_probs[0]};
    return ActionRule{new_coop_probs};
  }

  std::string Inspect() const {
    std::stringstream ss;
    ss << "ActionRule: " << ID() << std::endl;
    for (size_t i = 0; i < 4; i++) {
      Reputation rep_d = static_cast<Reputation>(i / 2);
      Reputation rep_r = static_cast<Reputation>(i % 2);
      ss << "(" << rep_d << "->" << rep_r << ") : " << coop_probs[i];
      if (i % 2 == 1) { ss << std::endl; }
      else { ss << "\t"; }
    }
    return ss.str();
  }

  ActionRule RescaleWithError(double mu_e) const {
    std::array<double,4> rescaled = {0.0};
    for (size_t i = 0; i < 4; i++) {
      rescaled[i] = (1.0 - mu_e) * coop_probs[i];
    }
    return ActionRule{rescaled};
  }

  bool IsSecondOrder() const {
    if (coop_probs[0] == coop_probs[2] && coop_probs[1] == coop_probs[3]) { return true; }
    else { return false; }
  }

  bool IsDeterministic() const {
    if (( coop_probs[0] == 0.0 || coop_probs[0] == 1.0 ) &&
        ( coop_probs[1] == 0.0 || coop_probs[1] == 1.0 ) &&
        ( coop_probs[2] == 0.0 || coop_probs[2] == 1.0 ) &&
        ( coop_probs[3] == 0.0 || coop_probs[3] == 1.0 ) ) {
      return true;
    }
    return false;
  }

  int ID() const {
    if (!IsDeterministic()) { return -1; }
    int id = 0;
    for (size_t i = 0; i < 4; i++) {
      if (coop_probs[i] == 1.0) { id += 1 << i; }
    }
    return id;
  }

  static ActionRule MakeDeterministicRule(int id) {
    if (id < 0 || id > 15) {
      throw std::runtime_error("AssessmentRuleDet: id must be between 0 and 15");
    }
    std::array<double,4> c_probs = {0.0};
    for (size_t i = 0; i < c_probs.size(); i++) {
      if ((id >> i) % 2) { c_probs[i] = 1.0; }
      else { c_probs[i] = 0.0; }
    }
    return ActionRule{ c_probs };
  }

  static ActionRule DISC() {
    return ActionRule{ {0.0, 1.0, 0.0, 1.0} };
  }
  static ActionRule ALLC() {
    return ActionRule{ {1.0, 1.0, 1.0, 1.0} };
  }
  static ActionRule ALLD() {
    return ActionRule{ {0.0, 0.0, 0.0, 0.0} };
  }
};

bool operator==(const ActionRule& t1, const ActionRule& t2) {
  return t1.coop_probs[0] == t2.coop_probs[0] &&
         t1.coop_probs[1] == t2.coop_probs[1] &&
         t1.coop_probs[2] == t2.coop_probs[2] &&
         t1.coop_probs[3] == t2.coop_probs[3];
}
bool operator!=(const ActionRule& t1, const ActionRule& t2) { return !(t1 == t2); }

class AssessmentRule {
  public:
  AssessmentRule(const std::array<double,8>& g_probs) : good_probs(g_probs) {};
  // {P(G|B,B,D), P(G|B,B,C), P(G|B,G,D), P(G|B,G,C), P(G|G,B,D), P(G|G,B,C), P(G|G,G,D), P(G|G,G,C)}

  AssessmentRule(const std::map< std::tuple<Reputation,Reputation,Action>, double> & g_probs) {
    if (g_probs.size() != 8) {
      throw std::runtime_error("AssessmentRule: g_probs must have 8 elements");
    }
    good_probs[0] = g_probs.at({Reputation::B, Reputation::B, Action::D});
    good_probs[1] = g_probs.at({Reputation::B, Reputation::B, Action::C});
    good_probs[2] = g_probs.at({Reputation::B, Reputation::G, Action::D});
    good_probs[3] = g_probs.at({Reputation::B, Reputation::G, Action::C});
    good_probs[4] = g_probs.at({Reputation::G, Reputation::B, Action::D});
    good_probs[5] = g_probs.at({Reputation::G, Reputation::B, Action::C});
    good_probs[6] = g_probs.at({Reputation::G, Reputation::G, Action::D});
    good_probs[7] = g_probs.at({Reputation::G, Reputation::G, Action::C});
  }

  std::array<double,8> good_probs;

  AssessmentRule Clone() const { return AssessmentRule(good_probs); }
  AssessmentRule SwapGB() const {
    std::array<double,8> new_good_probs = {1.0-good_probs[6], 1.0-good_probs[7], 1.0-good_probs[4], 1.0-good_probs[5],
                                           1.0-good_probs[2], 1.0-good_probs[3], 1.0-good_probs[0], 1.0-good_probs[1]};
    return {new_good_probs};
  }
  double GProb(const Reputation& rep_d, const Reputation& rep_r, const Action& act) const {
    size_t idx = static_cast<size_t>(rep_d) * 4 + static_cast<size_t>(rep_r) * 2 + static_cast<size_t>(act);
    return good_probs[idx];
  }
  void SetGProb(const Reputation& rep_d, const Reputation& rep_r, const Action& act, double g_prob) {
    size_t idx = static_cast<size_t>(rep_d) * 4 + static_cast<size_t>(rep_r) * 2 + static_cast<size_t>(act);
    good_probs[idx] = g_prob;
  }

  std::string Inspect() const {
    std::stringstream ss;
    ss << "AssessmentRule: " << ID() << std::endl;
    for (size_t i = 0; i < 8; i++) {
      Reputation rep_d = static_cast<Reputation>(i / 4);
      Reputation rep_r = static_cast<Reputation>((i/2) % 2);
      Action act = static_cast<Action>(i % 2);
      ss << "(" << rep_d << "->" << rep_r << "," << act << ") : " << good_probs[i];
      if (i % 4 == 3) { ss << std::endl; }
      else { ss << "\t"; }
    }
    return ss.str();
  }

  bool IsSecondOrder() const {
    if (good_probs[0] == good_probs[4] && good_probs[1] == good_probs[5] &&
        good_probs[2] == good_probs[6] && good_probs[3] == good_probs[7]) { return true; }
    else { return false; }
  }

  bool IsDeterministic() const {
    if (( good_probs[0] == 0.0 || good_probs[0] == 1.0 ) &&
        ( good_probs[1] == 0.0 || good_probs[1] == 1.0 ) &&
        ( good_probs[2] == 0.0 || good_probs[2] == 1.0 ) &&
        ( good_probs[3] == 0.0 || good_probs[3] == 1.0 ) &&
        ( good_probs[4] == 0.0 || good_probs[4] == 1.0 ) &&
        ( good_probs[5] == 0.0 || good_probs[5] == 1.0 ) &&
        ( good_probs[6] == 0.0 || good_probs[6] == 1.0 ) &&
        ( good_probs[7] == 0.0 || good_probs[7] == 1.0 ) ) {
      return true;
    }
    return false;
  }

  int ID() const {
    if (!IsDeterministic()) { return -1; }
    int id = 0;
    for (size_t i = 0; i < 8; i++) {
      if (good_probs[i] == 1.0) { id += 1 << i; }
    }
    return id;
  }

  static AssessmentRule MakeDeterministicRule(int id) {
    if (id < 0 || id > 255) {
      throw std::runtime_error("AssessmentRuleDet: id must be between 0 and 255");
    }
    std::array<double,8> good_probs = {0.0};
    for (size_t i = 0; i < 8; i++) {
      if ((id >> i) % 2) { good_probs[i] = 1.0; }
      else { good_probs[i] = 0.0; }
    }
    return AssessmentRule{ good_probs };
  }

  static AssessmentRule AllGood() {
    return AssessmentRule::MakeDeterministicRule(0b11111111);
  }
  static AssessmentRule AllBad() {
    return AssessmentRule::MakeDeterministicRule(0b00000000);
  }
  static AssessmentRule ImageScoring() {
    return AssessmentRule{{0,1,0,1,0,1,0,1}};
  }
  static AssessmentRule KeepRecipient() {
    return AssessmentRule{{0,0,1,1,0,0,1,1}};
  }
};

bool operator==(const AssessmentRule& t1, const AssessmentRule& t2) {
  return t1.good_probs[0] == t2.good_probs[0] &&
         t1.good_probs[1] == t2.good_probs[1] &&
         t1.good_probs[2] == t2.good_probs[2] &&
         t1.good_probs[3] == t2.good_probs[3] &&
         t1.good_probs[4] == t2.good_probs[4] &&
         t1.good_probs[5] == t2.good_probs[5] &&
         t1.good_probs[6] == t2.good_probs[6] &&
         t1.good_probs[7] == t2.good_probs[7];
}
bool operator!=(const AssessmentRule& t1, const AssessmentRule& t2) {
  return !(t1 == t2);
}

// Norm is a set of AssessmentRule & ActionRule
class Norm {
public:
  Norm(const AssessmentRule &R_d, const AssessmentRule &R_r, const ActionRule &act)
      : Rd(R_d.good_probs), Rr(R_r.good_probs), P(act.coop_probs) {};
  Norm(const Norm &rhs) : Rd(rhs.Rd), Rr(rhs.Rr), P(rhs.P) {};
  static Norm FromSerialized(const std::array<double,20>& serialized) {
    std::array<double,4> P_serialized;
    std::copy(serialized.begin(), serialized.begin()+4, P_serialized.begin());
    std::array<double,8> Rd_serialized, Rr_serialized;
    std::copy(serialized.begin()+4, serialized.begin()+12, Rd_serialized.begin());
    std::copy(serialized.begin()+12, serialized.begin()+20, Rr_serialized.begin());
    // reverse P_serialized
    std::reverse(P_serialized.begin(), P_serialized.end());
    std::reverse(Rd_serialized.begin(), Rd_serialized.end());
    std::reverse(Rr_serialized.begin(), Rr_serialized.end());
    return Norm{AssessmentRule{Rd_serialized}, AssessmentRule{Rr_serialized}, ActionRule{P_serialized}};
  }
  AssessmentRule Rd, Rr;  // assessment rules to assess donor and recipient
  ActionRule P;  // action rule
  std::string Inspect() const {
    std::stringstream ss;
    if (IsDeterministic()) {
      ss << "Norm: 0x" << std::setfill('0') << std::setw(5) << std::hex << ID()
         << " " << std::dec << ID()
         << " [" << Rd.ID() << "-" << Rr.ID() << "-" << P.ID() << "]"
         << " : " << GetName() << std::endl;
      ss << std::resetiosflags(std::ios_base::fmtflags(-1));
      for (int i = 3; i >= 0; i--) {
        Reputation X = static_cast<Reputation>(i / 2);
        Reputation Y = static_cast<Reputation>(i % 2);
        Action A = (CProb(X, Y) == 1.0) ? Action::C : Action::D;
        Action notA = FlipAction(A);
        Reputation donor_rep = Rd.GProb(X, Y, A) == 1.0 ? Reputation::G : Reputation::B;
        Reputation donor_rep_not = Rd.GProb(X, Y, notA) == 1.0 ? Reputation::G : Reputation::B;
        Reputation recip_rep = Rr.GProb(X, Y, A) == 1.0 ? Reputation::G : Reputation::B;
        Reputation recip_rep_not = Rr.GProb(X, Y, notA) == 1.0 ? Reputation::G : Reputation::B;
        ss << "(" << X << "->" << Y << "):" << A << donor_rep << donor_rep_not << ":" << recip_rep << recip_rep_not
           << "\t";
      }
      ss << "\n";
    }
    for (int i = 3; i >= 0; i--) {
      Reputation X = static_cast<Reputation>(i / 2);
      Reputation Y = static_cast<Reputation>(i % 2);
      double c_prob = P.CProb(X, Y);
      double gd_prob_d = Rd.GProb(X, Y, Action::D);
      double gd_prob_c = Rd.GProb(X, Y, Action::C);
      double gr_prob_d = Rr.GProb(X, Y, Action::D);
      double gr_prob_c = Rr.GProb(X, Y, Action::C);
      ss << std::setprecision(3) << std::fixed;
      ss << "(" << X << "->" << Y << "): "
         << "P:" << c_prob << " : "
         << "R1 (c:" << gd_prob_c << ",d:" << gd_prob_d << ") : "
         << "R2 (c:" << gr_prob_c << ",d:" << gr_prob_d << ")\n";
    }
    auto serialized = Serialize();
    ss << "Serialized:" << std::setprecision(2) << std::fixed;
    for (const auto& val : serialized) {
      ss << " " << val;
    }
    ss << std::endl;
    return ss.str();
  }
  std::string InspectComparison(const Norm& other) const {
    // compare this norm and `other` norm and highlight the differences
    std::stringstream ss;
    ss << std::setfill('0') << std::setw(5) << std::hex;
    ss << "Norm: 0x" << ID() << " : " << GetName() << " vs 0x" << other.ID() << " : " << other.GetName() << std::endl;
    ss << std::resetiosflags(std::ios_base::fmtflags(-1));

    for (int i = 3; i >= 0; i--) {
      auto X = static_cast<Reputation>(i / 2);
      auto Y = static_cast<Reputation>(i % 2);
      double c_prob1 = P.CProb(X, Y);
      double gd_prob_d1 = Rd.GProb(X, Y, Action::D);
      double gd_prob_c1 = Rd.GProb(X, Y, Action::C);
      double gr_prob_d1 = Rr.GProb(X, Y, Action::D);
      double gr_prob_c1 = Rr.GProb(X, Y, Action::C);

      double c_prob2 = other.P.CProb(X, Y);
      double gd_prob_d2 = other.Rd.GProb(X, Y, Action::D);
      double gd_prob_c2 = other.Rd.GProb(X, Y, Action::C);
      double gr_prob_d2 = other.Rr.GProb(X, Y, Action::D);
      double gr_prob_c2 = other.Rr.GProb(X, Y, Action::C);
      ss << std::setprecision(2) << std::fixed;
      ss << "(" << X << "->" << Y << "): ";
      ss << "P:";
      auto highlight_diff = [&ss](double a, double b) {
        if (a != b) {
          ss << "\033[1;31m";
          ss << a << " != " << b;
          ss << "\033[0m";
        } else {
          ss << a << "        ";
        }
      };
      highlight_diff(c_prob1, c_prob2);
      ss << " : ";
      ss << "R1 (c:";
      highlight_diff(gd_prob_c1, gd_prob_c2);
      ss << ",d:";
      highlight_diff(gd_prob_d1, gd_prob_d2);
      ss << ") : ";
      ss << "R2 (c:";
      highlight_diff(gr_prob_c1, gr_prob_c2);
      ss << ",d:";
      highlight_diff(gr_prob_d1, gr_prob_d2);
      ss << ")\n";
    }
    return ss.str();
  }
  std::array<double,20> Serialize() const {
    std::array<double,20> out;
    // first 4 elements are P's coop_probs, next 8 are Rd's good_probs, last 8 are Rr's good_probs
    // the order is reversed for human-readability
    for (size_t i = 0; i < 4; i++) {
      out[3-i] = P.coop_probs[i];
    }
    for (size_t i = 0; i < 8; i++) {
      out[11-i] = Rd.good_probs[i];
      out[19-i] = Rr.good_probs[i];
    }
    return out;
  }
  double CProb(Reputation donor, Reputation recipient) const { return P.CProb(donor, recipient); }
  double GProbDonor(Reputation donor, Reputation recipient, Action act) const {
    return Rd.GProb(donor, recipient, act);
  }
  double GProbRecip(Reputation donor, Reputation recipient, Action act) const {
    return Rr.GProb(donor, recipient, act);
  }
  Norm SwapGB() const {
    return Norm(Rd.SwapGB(), Rr.SwapGB(), P.SwapGB());
  }
  bool IsSecondOrder() const {
    return P.IsSecondOrder() && Rd.IsSecondOrder() && Rr.IsSecondOrder();
  }
  bool IsDeterministic() const {
    return P.IsDeterministic() && Rd.IsDeterministic() && Rr.IsDeterministic();
  }
  bool IsRecipKeep() const { // recipient's reputation is kept
    return Rr.IsDeterministic() && Rr.ID() == 0b11001100;
  }
  Norm RescaleWithError(double mu_e,
                        double mu_a_donor,
                        double mu_a_recip) const { // return the norm that takes into account error probabilities
    std::array<double, 8> good_probs_donor = {0.0};
    std::array<double, 8> good_probs_recip = {0.0};
    for (size_t i = 0; i < 8; i++) {
      good_probs_donor[i] = (1.0 - 2.0 * mu_a_donor) * Rd.good_probs[i] + mu_a_donor;
      good_probs_recip[i] = (1.0 - 2.0 * mu_a_recip) * Rr.good_probs[i] + mu_a_recip;
    }
    return Norm{{good_probs_donor}, {good_probs_recip}, P.RescaleWithError(mu_e)};
  }
  int ID() const {
    if (!IsDeterministic()) {
      return -1;
    }
    int id = 0;
    id += Rd.ID() << 12;
    id += Rr.ID() << 4;
    id += P.ID();
    return id;
  }
  int IDwithoutR2() const {
    if (!IsDeterministic() || !IsRecipKeep() ) {
      return -1;
    }
    int id = 0;
    id += Rd.ID() << 4;
    id += P.ID();
    return id;
  }
  static Norm ConstructFromID(int id) {
    if (id < 0 || id >= (1 << 20)) {
      throw std::runtime_error("Norm: id must be between 0 and 2^20-1");
    }
    int Rd_id = (id >> 12) & 0xFF;
    int Rr_id = (id >> 4) & 0xFF;
    int P_id = id & 0xF;
    return Norm(AssessmentRule::MakeDeterministicRule(Rd_id),
                AssessmentRule::MakeDeterministicRule(Rr_id),
                ActionRule::MakeDeterministicRule(P_id));
  }
  static Norm ConstructFromIDwithoutR2(int id) {
    if (id < 0 || id >= (1 << 12)) {
      throw std::runtime_error("Norm: id must be between 0 and 2^12-1");
    }
    int Rd_id = (id >> 4) & 0xFF;
    int P_id = id & 0xF;
    return Norm(AssessmentRule::MakeDeterministicRule(Rd_id),
                AssessmentRule::KeepRecipient(),
                ActionRule::MakeDeterministicRule(P_id));
  }
  static Norm AllC() {
    return Norm(AssessmentRule{{1, 1, 1, 1, 1, 1, 1, 1}},
                AssessmentRule::KeepRecipient(),
                ActionRule{{1, 1, 1, 1}});
  }
  static Norm AllD() {
    return Norm(AssessmentRule{{0, 0, 0, 0, 0, 0, 0, 0}},
                AssessmentRule::KeepRecipient(),
                ActionRule{{0, 0, 0, 0}});
  }
  static Norm AllG() {
    // Always assess G, but action rule is Discriminator
    // it may defect under assessment error
    return Norm(AssessmentRule::AllGood(),
                AssessmentRule::KeepRecipient(),
                ActionRule::DISC());
  }
  static Norm AllB() {
    // Always assess B, but action rule is Discriminator
    // it may defect under assessment error
    return Norm(AssessmentRule::AllBad(),
                AssessmentRule::KeepRecipient(),
                ActionRule::DISC());
  }
  static Norm ImageScoring() {
    return Norm(AssessmentRule::ImageScoring(),
                AssessmentRule::KeepRecipient(),
                ActionRule::DISC());
  }
  static Norm Random() {
    return Norm( AssessmentRule{{0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5}},
                 AssessmentRule{{0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5}},
                 ActionRule{{0.5, 0.5, 0.5, 0.5}});
  }
  static Norm L1() {
    return Norm({{0, 1, 0, 1, 1, 1, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{1, 1, 0, 1}});
  }
  static Norm L1v() {
    // Variant of L1 with (B,B) -> D in the action rule
    // Same assessment rule as L1; action rule becomes DISC (0,1,0,1)
    return Norm({{0, 1, 0, 1, 1, 1, 0, 1}},
                AssessmentRule::KeepRecipient(),
                ActionRule::DISC());
  }
  static Norm L2() {
    return Norm({{0, 1, 0, 1, 1, 0, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{1, 1, 0, 1}});
  }
  static Norm L2v() {
    // Variant of L2 with (B,B) -> D in the action rule (DISC)
    return Norm({{0, 1, 0, 1, 1, 0, 0, 1}},
                AssessmentRule::KeepRecipient(),
                ActionRule::DISC());
  }
  static Norm L3() {
    return Norm({{1, 1, 0, 1, 1, 1, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{0, 1, 0, 1}});
  }
  static Norm L4() {
    return Norm({{1, 0, 0, 1, 1, 1, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{0, 1, 0, 1}});
  }
  static Norm L5() {
    return Norm({{1, 1, 0, 1, 1, 0, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{0, 1, 0, 1}});
  }
  static Norm L6() {
    return Norm({{1, 0, 0, 1, 1, 0, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{0, 1, 0, 1}});
  }
  static Norm L7() {
    return Norm({{0, 0, 0, 1, 1, 1, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{0, 1, 0, 1}});
  }
  static Norm L8() {
    return Norm({{0, 0, 0, 1, 1, 0, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{0, 1, 0, 1}});
  }
  // L*-IS variants: same as L* but with Rr = ImageScoring
  static Norm L1_IS() {
    Norm n = L1();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L1v_IS() {
    Norm n = L1v();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L2_IS() {
    Norm n = L2();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L2v_IS() {
    Norm n = L2v();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L3_IS() {
    Norm n = L3();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L4_IS() {
    Norm n = L4();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L5_IS() {
    Norm n = L5();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L6_IS() {
    Norm n = L6();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L7_IS() {
    Norm n = L7();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm L8_IS() {
    Norm n = L8();
    n.Rr = AssessmentRule::ImageScoring();
    return n;
  }
  static Norm SecondarySixteen(int i) {
    if (i <= 0 || i > 16) { throw std::runtime_error("Norm: i must be between 1 and 16"); }
    double R_GB_C = static_cast<double>( ((i - 1) >> 3) & 0b1 );
    double R_BG_C = static_cast<double>( ((i - 1) >> 2) & 0b1 );
    double R_BB_C = static_cast<double>( ((i - 1) >> 1) & 0b1 );
    double R_BB_D = static_cast<double>( ((i - 1) >> 0) & 0b1 );
    double P_BB = 0.0;
    if (R_BB_C == 1.0 && R_BB_D == 0.0) { P_BB = 1.0; }
    return Norm({{R_BB_D, R_BB_C, 1, R_BG_C, 1, R_GB_C, 0, 1}},
                AssessmentRule::KeepRecipient(),
                {{P_BB, 0, 0, 1}});
  }
  static Norm GenerousScoring(double benefit = 5.0) {
    double q = 1.0 / benefit;
    AssessmentRule gsco(std::array<double,8>{{q, 1.0, q, 1.0, q, 1.0, q, 1.0}});
    return Norm(gsco,
                AssessmentRule::KeepRecipient(),
                ActionRule::DISC());
  }
  bool IsGenerousScoring() const {
    if( Rr != AssessmentRule::KeepRecipient() || P != ActionRule::DISC() ) {
      return false;
    }
    if (Rd.good_probs[1] < 1.0 || Rd.good_probs[3] < 1.0 || Rd.good_probs[5] < 1.0 || Rd.good_probs[7] < 1.0) {
      return false;
    }
    if (Rd.good_probs[0] != Rd.good_probs[2] || Rd.good_probs[0] != Rd.good_probs[4] || Rd.good_probs[0] != Rd.good_probs[6]) {
      return false;
    }
    return true;
  }
  static std::vector<size_t> Deterministic3rdOrderWithR2NormIDs() {
    std::vector<size_t> ids;
    ids.reserve((1u << 19));  // half of total deterministic norms after symmetry removal
    for (int i = 0; i < (1 << 20); i++) {
      const Norm n = Norm::ConstructFromID(i);
      const int swapped = n.SwapGB().ID();
      if (n.ID() >= swapped) {
        ids.push_back(static_cast<size_t>(n.ID()));
      }
    }
    return ids;
  }
  static std::vector<Norm> Deterministic3rdOrderWithoutR2Norms() {
    std::vector<Norm> norms;
    for (int i = 0; i < 4096; i++) {
      const Norm n = Norm::ConstructFromIDwithoutR2(i);
      if (n.IDwithoutR2() >= n.SwapGB().IDwithoutR2()) {
        norms.push_back(n);
      }
    }
    return norms;
  }
  static std::vector<Norm> Deterministic2ndOrderWithoutR2Norms() {
    std::vector<Norm> norms;
    for (int i = 0; i < 4096; i++) {
      const Norm n = Norm::ConstructFromIDwithoutR2(i);
      if (n.IsSecondOrder() && n.IDwithoutR2() >= n.SwapGB().IDwithoutR2()) {
        norms.push_back(n);
      }
    }
    return norms;
  }
  static std::vector<Norm> Deterministic2ndOrderWithR2Norms() {
    std::vector<Norm> norms;
    for (int i = 0; i < (1<<20); i++) {
      const Norm n = Norm::ConstructFromID(i);
      if (n.IsSecondOrder() && n.ID() >= n.SwapGB().ID()) {
        norms.push_back(n);
      }
    }
    return norms;
  }

  static const std::vector<std::pair<int, std::string> > NormNames;
  std::string GetName() const {
    if (IsDeterministic()) {
      for (auto &p : NormNames) {
        if (p.first == ID() || p.first == SwapGB().ID() ) {
          return p.second;
        }
      }
      if (P.ID() == 0) { return "AllD"; }
      if (P.ID() == 15) { return "AllC"; }
    }
    if (IsGenerousScoring()) {
      double benefit = 1.0 / Rd.good_probs[0];
      std::ostringstream oss;
      oss << "GSCO-" << std::fixed << std::setprecision(1) << benefit;
      return oss.str();
    }
    std::string s = PR1_Name();
    if (!s.empty()) {
      return "similar to " + s;
    }
    return "";
  }
  static Norm ConstructFromName(const std::string &name) {
    auto found = std::find_if(Norm::NormNames.begin(), Norm::NormNames.end(), [&](auto &s) {
      return s.second == name;
    });

    std::regex re_gsco(R"(^GSCO-(\d+(?:\.\d+)?)$)");
    std::smatch matches;

    if (found != Norm::NormNames.end()) {
      return Norm::ConstructFromID(found->first);
    }
    else if (std::regex_match(name, matches, re_gsco)) {
      double benefit = std::stod(matches[1]);
      return Norm::GenerousScoring(benefit);
    }
    else {
      std::cerr << "Unknown norm: " << name << std::endl;
      std::cerr << "Available norms are: " << std::endl;
      for (auto &n : Norm::NormNames) {
        std::cerr << "\t" << n.second << std::endl;
      }
      std::cerr << "\t" << "GSCO-benefit" << std::endl;
      throw std::runtime_error("Unknown norm");
    }
  }
  std::string PR1_Name() const {  // return the name of {P,R1}
    // return the named norm that differs only in R2
    if (P.IsDeterministic() && Rd.IsDeterministic()) {
      int id = (Rd.ID() << 12) + P.ID();
      constexpr int mask = 0xFF00F;
      for (auto &p : NormNames) {
        if ((p.first & mask) == (id & mask)) {
          return p.second;
        }
      }
      constexpr Reputation G = Reputation::G, B = Reputation::B;
      constexpr Action C = Action::C, D = Action::D;
      if (  // L_prime
          P.CProb(G,G) == 1.0 &&
          P.CProb(G,B) == 0.0 &&
          P.CProb(B,G) == 1.0 &&
          Rd.GProb(G,G,C) == 1.0 &&
          Rd.GProb(G,G,D) == 0.0 &&
          Rd.GProb(G,B,C) == 0.0 &&
          Rd.GProb(G,B,D) == 0.0 &&
          Rd.GProb(B,G,C) == 1.0 &&
          Rd.GProb(B,G,D) == 0.0
          ) {
        return "L_prime";
      }
      else if (  // S_prime
          P.CProb(G,G) == 1.0 &&
          P.CProb(G,B) == 0.0 &&
          P.CProb(B,G) == 0.0 &&
          Rd.GProb(G,G,C) == 1.0 &&
          Rd.GProb(G,G,D) == 0.0 &&
          Rd.GProb(G,B,D) == 1.0 &&
          Rd.GProb(B,G,C) == 0.0 &&
          Rd.GProb(B,G,D) == 0.0
          ) {
        return "S_prime";
      }
      else if (  // S_prime_prime
          P.CProb(G,G) == 1.0 &&
          P.CProb(G,B) == 0.0 &&
          P.CProb(B,G) == 0.0 &&
          Rd.GProb(G,G,C) == 1.0 &&
          Rd.GProb(G,G,D) == 0.0 &&
          Rd.GProb(G,B,C) == 0.0 &&
          Rd.GProb(G,B,D) == 0.0 &&
          Rd.GProb(B,G,D) == 1.0
          ) {
        return "S_prime_prime";
      }
    }
    return "";
  }

  static Norm ParseNormString(const std::string& str, bool swap_gb = false) {
    std::regex re_d(R"(\d+)"); // regex for digits
    std::regex re_triplet(R"(^([0-9]+)-([0-9]+)-([0-9]+)$)"); // regex for Rd-Rr-P deterministic triplet
    std::regex re_x(R"(^0x[0-9a-fA-F]+$)");  // regex for digits in hexadecimal
    // regular expression for 20 (possibly floating point) numbers separated by space
    std::regex re_a(R"(^([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?:\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))){19}$)");
    Norm norm = Norm::AllC();
    if (std::regex_match(str, re_d)) {
      int id = std::stoi(str);
      norm = Norm::ConstructFromID(id);
    }
    else if (std::regex_match(str, re_triplet)) {
      std::smatch m;
      std::regex_match(str, m, re_triplet);
      // m[1]=Rd, m[2]=Rr, m[3]=P
      int rd = std::stoi(m[1]);
      int rr = std::stoi(m[2]);
      int p  = std::stoi(m[3]);
      norm = Norm(AssessmentRule::MakeDeterministicRule(rd),
                  AssessmentRule::MakeDeterministicRule(rr),
                  ActionRule::MakeDeterministicRule(p));
    }
    else if (std::regex_match(str, re_x)) {
      int id = std::stoi(str, nullptr, 16);
      norm = Norm::ConstructFromID(id);
    }
    else if (std::regex_match(str, re_a)) {
      std::istringstream iss(str);
      std::array<double,20> serialized = {};
      for (int i = 0; i < 20; ++i) {
        iss >> serialized[i];
      }
      norm = Norm::FromSerialized(serialized);
    }
    else {
      norm = Norm::ConstructFromName(str);
    }
    if (swap_gb) {
      norm = norm.SwapGB();
    }
    return norm;
  }
};

const std::vector<std::pair<int,std::string> > Norm::NormNames = {{
                                                                    {AllC().ID(), "AllC"},
                                                                    {AllD().ID(), "AllD"},
                                                                    {AllG().ID(), "AllG"},
                                                                    {AllB().ID(), "AllB"},
                                                                    {ImageScoring().ID(), "ImageScoring"},
                                                                    {L1().ID(), "L1"},
                                                                    {L1v().ID(), "L1v"},
                                                                    {L2().ID(), "L2"},
                                                                    {L2v().ID(), "L2v"},
                                                                    {L3().ID(), "L3"},
                                                                    {L4().ID(), "L4"},
                                                                    {L5().ID(), "L5"},
                                                                    {L6().ID(), "L6"},
                                                                    {L7().ID(), "L7"},
                                                                    {L8().ID(), "L8"},
                                                                    {L1_IS().ID(), "L1-IS"},
                                                                    {L1v_IS().ID(), "L1v-IS"},
                                                                    {L2_IS().ID(), "L2-IS"},
                                                                    {L2v_IS().ID(), "L2v-IS"},
                                                                    {L3_IS().ID(), "L3-IS"},
                                                                    {L4_IS().ID(), "L4-IS"},
                                                                    {L5_IS().ID(), "L5-IS"},
                                                                    {L6_IS().ID(), "L6-IS"},
                                                                    {L7_IS().ID(), "L7-IS"},
                                                                    {L8_IS().ID(), "L8-IS"},
                                                                    {SecondarySixteen(1).ID(), "S1"},
                                                                    {SecondarySixteen(2).ID(), "S2"},
                                                                    {SecondarySixteen(3).ID(), "S3"},
                                                                    {SecondarySixteen(4).ID(), "S4"},
                                                                    {SecondarySixteen(5).ID(), "S5"},
                                                                    {SecondarySixteen(6).ID(), "S6"},
                                                                    {SecondarySixteen(7).ID(), "S7"},
                                                                    {SecondarySixteen(8).ID(), "S8"},
                                                                    {SecondarySixteen(9).ID(), "S9"},
                                                                    {SecondarySixteen(10).ID(), "S10"},
                                                                    {SecondarySixteen(11).ID(), "S11"},
                                                                    {SecondarySixteen(12).ID(), "S12"},
                                                                    {SecondarySixteen(13).ID(), "S13"},
                                                                    {SecondarySixteen(14).ID(), "S14"},
                                                                    {SecondarySixteen(15).ID(), "S15"},
                                                                    {SecondarySixteen(16).ID(), "S16"},
                                                                }};
bool operator==(const Norm& n1, const Norm& n2) {
  return n1.P == n2.P && n1.Rd == n2.Rd && n1.Rr == n2.Rr;
}
bool operator!=(const Norm& n1, const Norm& n2) {
  return !(n1 == n2);
}

#endif
