#ifndef EVOL_PRIVATE_REP_GAME_HPP
#define EVOL_PRIVATE_REP_GAME_HPP

#include <iostream>
#include <vector>
#include <random>
#include <Eigen/Dense>
#include "Norm.hpp"
#include "PrivRepGame.hpp"


class EvolPrivRepGame {
public:
  struct Parameters {
    Parameters() : N(30), t_init(1e3), t_measure(1e3), q(1.0), mu_impl(0.0), mu_percept(0.0), mu_assess1(0.05), mu_assess2(0.0), _seed(123456789ull) {};
    Parameters(size_t N, size_t t_init, size_t t_measure, double q, double mu_impl, double mu_percept, double mu_assess1, double mu_assess2, uint64_t seed) :
        N(N), t_init(t_init), t_measure(t_measure), q(q), mu_impl(mu_impl), mu_percept(mu_percept), mu_assess1(mu_assess1), mu_assess2(mu_assess2), _seed(seed) {};
    size_t N;  // population size
    size_t t_init, t_measure;  // simulation durations
    double q;  // observation probability
    double mu_impl;  // implementation error probability
    double mu_percept;  // perception error probability
    double mu_assess1, mu_assess2;  // assessment error probability
    uint64_t _seed;  // random number seed
    NLOHMANN_DEFINE_TYPE_INTRUSIVE_WITH_DEFAULT(Parameters, N, t_init, t_measure, q, mu_impl, mu_percept, mu_assess1, mu_assess2, _seed);
  };

  using norms_t = std::vector<Norm>;

  // rho[i][j] = fixation probability of a j-mutant into i-resident community
  static std::vector<std::vector<double>> FixationProbabilities(const norms_t& norms, const Parameters& param, double benefit, double beta) {
    size_t n_norms = norms.size();
    std::vector<std::vector<double>> rho(n_norms, std::vector<double>(n_norms, 0.0));

    for (size_t i = 0; i < n_norms; i++) {
      for (size_t j = i+1; j < n_norms; j++) {
        auto rho_ij_ji_pii_pij = FixationProbabilityAndPayoff(norms[i], norms[j], param, benefit, beta);
        rho[i][j] = std::get<0>(rho_ij_ji_pii_pij);
        rho[j][i] = std::get<1>(rho_ij_ji_pii_pij);
      }
    }

    return rho;
  }

  // cooperation probability of mono-morphic population
  static double MonomorphicCooperationLevel(const Norm& norm, const Parameters& param) {
    PrivateRepGame game({{norm, param.N}}, param._seed);
    game.Update(param.t_init, param.q, param.mu_impl, param.mu_percept, param.mu_assess1, param.mu_assess2, false);
    game.ResetCounts();
    game.Update(param.t_measure, param.q, param.mu_impl, param.mu_percept, param.mu_assess1, param.mu_assess2, false);
    double self_coop_level = game.NormCooperationLevels()[0][0];
    return self_coop_level;
  }

  // strategy-wise benefit & cost when two strategies coexist
  // ni: number of i-strategy players. the number of j-strategy players is param.N - ni
  // return : vector of pairs of benefit and cost for each norm
  struct benefit_cost_prob_t {
    double benefit_prob, cost_prob;
  };
  static std::pair<benefit_cost_prob_t, benefit_cost_prob_t> BenefitCostProbs(const Norm& str_i, size_t ni, const Norm& str_j, const Parameters& param) {
    PrivateRepGame game({{str_i, ni}, {str_j, param.N - ni}}, param._seed);
    game.Update(param.t_init, param.q, param.mu_impl, param.mu_percept, param.mu_assess1, param.mu_assess2, false);
    game.ResetCounts();
    game.Update(param.t_measure, param.q, param.mu_impl, param.mu_percept, param.mu_assess1, param.mu_assess2, false);

    auto coop_levles = game.IndividualCooperationLevels();
    double i_benefit_prob = 0.0, i_cost_prob = 0.0;
    for (size_t k = 0; k < ni; k++) {
      i_benefit_prob += coop_levles[k].first;
      i_cost_prob += coop_levles[k].second;
    }
    i_benefit_prob /= static_cast<double>(ni);
    i_cost_prob /= static_cast<double>(ni);
    double j_benefit_prob = 0.0, j_cost_prob = 0.0;
    for (size_t k = ni; k < param.N; k++) {
      j_benefit_prob += coop_levles[k].first;
      j_cost_prob += coop_levles[k].second;
    }
    j_benefit_prob /= static_cast<double>(param.N - ni);
    j_cost_prob /= static_cast<double>(param.N - ni);

    return {{i_benefit_prob, i_cost_prob}, {j_benefit_prob, j_cost_prob} };
  }

  // calculate fixation probability of mutant j against resident i from payoff vectors
  // pi_i[l]: payoff of resident i when l mutants exist
  // return: p_ij (fixation probability of j mutant against i residents), p_ji (fixation probability of i mutant against j residents)
  static std::pair<double,double> FixationProbabilityFromPayoffVectors(const std::vector<double>& pi_i, const std::vector<double>& pi_j, size_t N, double beta) {
    double rho_1_inv = 1.0;
    // p_ij = 1 / (1 + sum_{l' = 1}^{N-1}  prod_{l=1}^{l_prime} exp{-beta * (pi_j[l] - pi_i[l]) }
    for (size_t l_prime = 1; l_prime < N; l_prime++) {
      double prod = 1.0;
      for (size_t l = 1; l <= l_prime; l++) {
        prod *= exp(-beta * (pi_j[l] - pi_i[l]));
      }
      rho_1_inv += prod;
    }
    double rho_1 = 1.0 / rho_1_inv;

    double rho_2_inv = 1.0;
    for (size_t l_prime = 1; l_prime < N; l_prime++) {
      double prod = 1.0;
      for (size_t l = 1; l <= l_prime; l++) {
        prod *= exp(-beta * (pi_i[N-l] - pi_j[N-l]));
      }
      rho_2_inv += prod;
    }
    double rho_2 = 1.0 / rho_2_inv;
    return {rho_1, rho_2};
  }

  // first: fixation probability of mutant j against resident i
  //        i.e., the probability to change from i to j
  // second: fixation probability of mutant i against resident j
  //        i.e., the probability to change from j to i
  // third: payoff vector of i. pi_i[l] payoff of resident i when l mutants exist. pi_i[0] is not used
  // fourth: payoff vector of j. pi_j[l] payoff of mutant j when l mutants exist. pi_j[0] is not used
  static std::tuple<double,double,std::vector<double>,std::vector<double>> FixationProbabilityAndPayoff(const Norm& norm_i, const Norm& norm_j, const Parameters& param, double benefit, double beta) {
    const size_t N = param.N;
    std::vector<double> pi_i(N);  // pi_i[l]: payoff of resident i when l mutants exist
    std::vector<double> pi_j(N);  // pi_j[l]: payoff of mutant j when l mutants exist

    #pragma omp parallel for schedule(dynamic) default(none), shared(pi_i, pi_j, norm_i, norm_j, param, benefit, beta, N)
    for (size_t l = 1; l < N; l++) {
      Parameters param_l = param;
      param_l._seed += l;
      auto bc_probs = BenefitCostProbs(norm_i, N - l, norm_j, param_l);
      pi_i[l] = benefit * bc_probs.first.benefit_prob - bc_probs.first.cost_prob;
      pi_j[l] = benefit * bc_probs.second.benefit_prob - bc_probs.second.cost_prob;
    }

    auto [rho_1, rho_2] = FixationProbabilityFromPayoffVectors(pi_i, pi_j, N, beta);
    return {rho_1, rho_2, pi_i, pi_j};
  }

  // first: fixation probability of resident j against resident i
  //        i.e., the probability to change from i to j
  // second: fixation probability of resident i against resident j
  //        i.e., the probability to change from j to i
  static std::vector<std::pair<double,double>> FixationProbabilityBatch(const Norm& norm_i, const Norm& norm_j, const Parameters& param, const std::vector<std::pair<double,double>>& benefit_sigma_in_pairs) {
    const size_t N = param.N;
    // i_cost_probs[l], i_benefit_probs[l]: the probability that i donate or receive when l mutants exist
    // payoff_i[l] = benefit * receive[l] - i_cost_probs[l]
    std::vector<double> i_benefit_probs(N, 0.0), i_cost_probs(N, 0.0);
    // j_cost_probs[l], j_benefit_probs[l]: the probability that j donate or receive when l mutants exist
    // payoff_j[l] = benefit * j_benefit_probs[l] - j_cost_probs[l]
    std::vector<double> j_benefit_probs(N, 0.0), j_cost_probs(N, 0.0);

    #pragma omp parallel for schedule(dynamic) default(none), shared(i_benefit_probs, i_cost_probs, j_benefit_probs, j_cost_probs, norm_i, norm_j, param, benefit_sigma_in_pairs, N)
    for (size_t l = 1; l < N; l++) {
      Parameters param_l = param;
      param_l._seed += l;
      auto bc_probs = BenefitCostProbs(norm_i, N - l, norm_j, param_l);
      i_benefit_probs[l] = bc_probs.first.benefit_prob;
      i_cost_probs[l] = bc_probs.first.cost_prob;
      j_benefit_probs[l] = bc_probs.second.benefit_prob;
      j_cost_probs[l] = bc_probs.second.cost_prob;
    }

    std::vector<std::pair<double,double>> rho_pair_vec;
    for (const auto[benefit,sigma_in]: benefit_sigma_in_pairs) {
      std::vector<double> pi_i(N), pi_j(N);
      for (size_t l = 1; l < N; l++) {
        pi_i[l] = benefit * i_benefit_probs[l] - i_cost_probs[l];
        pi_j[l] = benefit * j_benefit_probs[l] - j_cost_probs[l];
      }
      auto [rho_1, rho_2] = FixationProbabilityFromPayoffVectors(pi_i, pi_j, N, sigma_in);

      rho_pair_vec.emplace_back(rho_1, rho_2);
    }
    return rho_pair_vec;
  }

  // arg: transition probability matrix p
  //      p[i][j] : fixation probability of a j-mutant into i-resident
  // return: stationary distribution vector
  static std::vector<double> EquilibriumPopulationLowMut(const std::vector<std::vector<double>>& fixation_probs) {
    long S = static_cast<long>(fixation_probs.size());

    // construct transition matrix
    Eigen::MatrixXd T(S, S);

    for (long i = 0; i < S; i++) {
      double sum = 0.0;
      for (long j = 0; j < S; j++) {
        if (i == j) continue;
        T(j,i) = fixation_probs[i][j] / (1.0 - (double)S);
        sum += T(j, i);
      }
      T(i,i) = - sum;  // T(i,i) = 1.0 - sum; but we subtract I to calculate stationary distribution
    }
    for (long i = 0; i < S; i++) {  // normalization condition
      T(S - 1, i) += 1.0;
    }

    Eigen::VectorXd b(S);
    for (int i = 0; i < S - 1; i++) { b(i) = 0.0; }
    b(S - 1) = 1.0;

    Eigen::VectorXd x = T.colPivHouseholderQr().solve(b);

    std::vector<double> ans(S, 0.0);
    for (int i = 0; i < S; i++) {
      ans[i] = x(i);
    }
    return ans;
  }

  // arg: transition probability matrix p
  //      p[i][j] : fixation probability of a j-mutant into i-resident.
  // return: stationary distribution vector
  static std::vector<double> EquilibriumPopulationLowMutPowerMethod(const std::vector<std::vector<double>>& fixation_probs) {
    // calculate stationary distribution using the power method

    // Initialize the initial guess for the principal eigenvector
    size_t N = fixation_probs.size();
    std::vector<double> x(N, 1.0/static_cast<double>(N));

    // transposed A matrix
    // A_ij = fixation_probs[j][i] / (1.0 - static_cast<double>(N));
    std::vector<double> A(N*N, 0.0);
    for (size_t i = 0; i < N; i++) {
      double sum = 0.0;
      for (size_t j = 0; j < N; j++) {
        if (i == j) continue;
        A[j*N+i] = fixation_probs[i][j] / (static_cast<double>(N)-1.0);
        sum += A[j*N+i];
      }
      A[i*N+i] = 1.0 - sum;
    }

    constexpr size_t maxIterations = 100000;
    constexpr double tolerance = 1.0e-8;

    for (size_t t=0; t < maxIterations; t++) {
      if (t % 1000 == 0) {
        std::cerr << "iteration: " << t << std::endl;
      }
      // matrix multiplication
      std::vector<double> x_new(N, 0.0);
      for (size_t i = 0; i < N; i++) {
        double sum = 0.0;
        for (size_t j = 0; j < N; j++) {
          sum += A[i*N+j] * x[j];
        }
        x_new[i] = sum;
      }

      if (t % 10 == 9) {
        // normalization
        double norm = 0.0;
        for (size_t i = 0; i < N; i++) {
          norm += x_new[i];
        }
        for (size_t i = 0; i < N; i++) {
          x_new[i] /= norm;
        }

        // check convergence
        double max_diff = 0.0;
        for (size_t i = 0; i < N; i++) {
          double diff = std::abs(x_new[i] - x[i]);
          if (diff > max_diff) {
            max_diff = diff;
          }
        }
        if (max_diff < tolerance) {
          std::cerr << "converged at step " << t << std::endl;
          return x_new;
        }
      }

      x = x_new;
    }

    std::cerr << "didn't converge" << std::endl;
    return x;
  }

  // Evolutionary game between X and AllC and AllD
  // optimized for the three-species system
  // return self-cooperation-level, rho, equilibrium population
  static std::tuple<double,std::vector<std::vector<double>>,std::vector<double>> EquilibriumCoopLevelAllCAllD(const Norm& norm, const Parameters& param, double benefit, double beta) {
    const size_t N = param.N;
    std::vector<double> pi_x_allc(N, 0.0), pi_allc_x(N, 0.0), pi_x_alld(N, 0.0), pi_alld_x(N, 0.0);
    double self_coop_level;
    // pi_x_allc[l] : payoff of X against AllC when there are l AllC and (N-l) residents
    // pi_allc_x[l]   : payoff of AllC against X when there are l AllC and (N-l) residents
    // pi_x_alld[l] : payoff of X against AllD when there are l AllD and (N-l) residents
    // pi_alld_x[l]   : payoff of AllD against X when there are l AllD and (N-l) residents

    const Norm allc = Norm::AllC();
    const Norm alld = Norm::AllD();

    #pragma omp parallel for schedule(dynamic) default(none), shared(pi_x_allc, pi_allc_x, pi_x_alld, pi_alld_x, norm, self_coop_level, N, allc, alld, param, benefit, beta)
    for (size_t i = 0; i < 2*N-1; i++) {
      if (i == 0) {  // monomorphic population of X
        self_coop_level = EvolPrivRepGame::MonomorphicCooperationLevel(norm, param);
        pi_x_allc[0] = pi_x_alld[0] = self_coop_level * (benefit - 1.0);
      }
      else if (i < N) {   // [1, ..., N-1]
        size_t l = i;
        // (N-l) X vs l AllC
        auto [bc_probs_x, bc_probs_allc] = EvolPrivRepGame::BenefitCostProbs(norm, N - l, allc, param);
        pi_x_allc[l] = bc_probs_x.benefit_prob * benefit - bc_probs_x.cost_prob;
        pi_allc_x[l] = bc_probs_allc.benefit_prob * benefit - bc_probs_allc.cost_prob;
      }
      else if (i >= N) {  // [N-1, ..., 2N-2]
        // (N-l) X vs l AllD
        size_t l = i - N + 1;
        auto [bc_probs_x, bc_probs_alld] = EvolPrivRepGame::BenefitCostProbs(norm, N - l, alld, param);
        pi_x_alld[l] = bc_probs_x.benefit_prob * benefit - bc_probs_x.cost_prob;
        pi_alld_x[l] = bc_probs_alld.benefit_prob * benefit - bc_probs_alld.cost_prob;
      }
    }
    // IC(pi_x_allc, pi_allc_x, pi_x_alld, pi_alld_x);

    // calculate the fixation probabilities
    std::vector<std::vector<double>> rho(3, std::vector<double>(3, 0.0));

    auto [rho_x_to_allc, rho_allc_to_x] = EvolPrivRepGame::FixationProbabilityFromPayoffVectors(pi_x_allc, pi_allc_x, N, beta);
    rho[0][1] = rho_x_to_allc;
    rho[1][0] = rho_allc_to_x;

    auto [rho_x_to_alld, rho_alld_to_x] = EvolPrivRepGame::FixationProbabilityFromPayoffVectors(pi_x_alld, pi_alld_x, N, beta);
    rho[0][2] = rho_x_to_alld;
    rho[2][0] = rho_alld_to_x;

    std::vector<double> pi_allc_alld(N, 0.0), pi_alld_allc(N, 0.0);
    // pi_allc_alld: payoff of AllC against AllD when there are l AllC and (N-l) AllD
    // pi_alld_allc: payoff of AllD against AllC when there are l AllC and (N-l) AllD
    for (size_t l = 1; l < N; l++) {
      pi_allc_alld[l] = static_cast<double>(l-1)/static_cast<double>(N-1) * benefit - 1.0;
      pi_alld_allc[l] = static_cast<double>(l)/static_cast<double>(N-1) * benefit;
    }
    auto [rho_allc_to_alld, rho_alld_to_allc] = EvolPrivRepGame::FixationProbabilityFromPayoffVectors(pi_allc_alld, pi_alld_allc, N, beta);
    rho[1][2] = rho_allc_to_alld;
    rho[2][1] = rho_alld_to_allc;

    // calculate the equilibrium populations
    auto eq = EvolPrivRepGame::EquilibriumPopulationLowMut(rho);

    return std::make_tuple(self_coop_level, rho, eq);
  };
};


#endif // EVOL_PRIVATE_REP_GAME_HPP
