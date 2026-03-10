#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <optional>
#ifdef _OPENMP
#include <omp.h>
#endif
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <sstream>
#include <vector>

#include <nlohmann/json.hpp>

#include "CliJsonUtils.hpp"
#include "Norm.hpp"

struct RecoveryParams {
  size_t N;
  size_t max_t;
  size_t num_samples;
  uint64_t _seed;
};

size_t Index(size_t observer, size_t target, size_t N) {
  return observer * N + target;
}

class ImageMatrix {
public:
  explicit ImageMatrix(size_t N) : N_(N), M_(N * N, Reputation::G), num_bad_(0) {}

  void ResetToSingleBadEntry() {
    std::fill(M_.begin(), M_.end(), Reputation::G);
    num_bad_ = 0;
    if (N_ < 2) {
      throw std::runtime_error("population_size must be at least 2");
    }
    Set(0, 1, Reputation::B);
  }

  Reputation Get(size_t observer, size_t target) const {
    return M_[Index(observer, target, N_)];
  }

  void Set(size_t observer, size_t target, Reputation value) {
    size_t idx = Index(observer, target, N_);
    Reputation old = M_[idx];
    if (old == value) {
      return;
    }
    if (old == Reputation::B) {
      num_bad_--;
    }
    if (value == Reputation::B) {
      num_bad_++;
    }
    M_[idx] = value;
  }

  bool AllGood() const { return num_bad_ == 0; }

private:
  size_t N_;
  std::vector<Reputation> M_;
  size_t num_bad_;
};

Reputation SampleReputation(double g_prob, std::mt19937_64 &rng, std::uniform_real_distribution<double> &dist01) {
  if (g_prob >= 1.0) {
    return Reputation::G;
  }
  if (g_prob <= 0.0) {
    return Reputation::B;
  }
  return (dist01(rng) < g_prob) ? Reputation::G : Reputation::B;
}

std::optional<size_t> RunRecoverySample(const Norm &norm, const RecoveryParams &params, uint64_t seed) {
  const size_t N = params.N;
  std::mt19937_64 rng(seed);
  std::uniform_real_distribution<double> dist01(0.0, 1.0);
  std::uniform_int_distribution<size_t> dist_agent(0, N - 1);
  std::uniform_int_distribution<size_t> dist_agent2(1, N - 1);

  ImageMatrix image(N);
  image.ResetToSingleBadEntry();

  for (size_t t = 1; t <= params.max_t; ++t) {
    size_t donor = dist_agent(rng);
    size_t recip = (donor + dist_agent2(rng)) % N;

    Reputation donor_self = image.Get(donor, donor);
    Reputation donor_view_rec = image.Get(donor, recip);
    const double c_prob = norm.P.CProb(donor_self, donor_view_rec);
    const Action action = ((c_prob == 1.0) || (dist01(rng) < c_prob)) ? Action::C : Action::D;

    for (size_t obs = 0; obs < N; ++obs) {
      double g_prob_donor = norm.Rd.GProb(image.Get(obs, donor), image.Get(obs, recip), action);
      Reputation donor_rep = SampleReputation(g_prob_donor, rng, dist01);
      image.Set(obs, donor, donor_rep);

      double g_prob_recip = norm.Rr.GProb(image.Get(obs, donor), image.Get(obs, recip), action);
      Reputation recip_rep = SampleReputation(g_prob_recip, rng, dist01);
      image.Set(obs, recip, recip_rep);
    }

    if (image.AllGood()) {
      return t;
    }
  }

  return std::nullopt;
}

RecoveryParams LoadParams(const nlohmann::json &params_json) {
  RecoveryParams params;
  params.N = params_json.at("N").get<size_t>();
  params.max_t = params_json.at("max_t").get<size_t>();
  params.num_samples = params_json.at("num_samples").get<size_t>();
  params._seed = params_json.at("_seed").get<uint64_t>();

  if (params.N < 2) {
    throw std::runtime_error("N must be at least 2");
  }
  if (params.max_t == 0) {
    throw std::runtime_error("max_t must be positive");
  }
  if (params.num_samples == 0) {
    throw std::runtime_error("num_samples must be positive");
  }
  return params;
}

int main(int argc, char *argv[]) {
  std::queue<std::string> args;
  nlohmann::json params = nlohmann::json::object();

  for (int i = 1; i < argc; ++i) {
    std::string current(argv[i]);
    if (CliJsonUtils::ConsumeJsonOption(argc, argv, i, "-j", params)) {
      continue;
    } else {
      args.emplace(current);
    }
  }

  nlohmann::json default_params = {
    {"N", 50},
    {"max_t", 10'000},
    {"num_samples", 10'000},
    {"_seed", 123456789ull}
  };

  try {
    CliJsonUtils::ValidateObjectKeys(params, CliJsonUtils::JsonKeys(default_params));
    CliJsonUtils::ApplyJsonDefaults(params, default_params);
  }
  catch (const std::exception& e) {
    std::cerr << "[Error] " << e.what() << std::endl;
    return 1;
  }

  if (args.size() != 1) {
    std::cerr << "Usage: " << argv[0] << " [-j params.json] norm" << std::endl;
    std::cerr << "Parameters: N, _seed, max_t, num_samples" << std::endl;
    return 1;
  }

  try {
    RecoveryParams parsed_params = LoadParams(params);
    Norm norm = Norm::ParseNormString(args.front(), false);

    std::cerr << "Running recovery analysis with parameters:" << std::endl;
    std::cerr << params.dump(2) << std::endl;

    std::vector<size_t> successes;
    successes.reserve(parsed_params.num_samples);

#if defined(_OPENMP)
#pragma omp parallel
    {
      std::vector<size_t> local_successes;
      local_successes.reserve(parsed_params.num_samples / omp_get_num_threads() + 1);
#pragma omp for schedule(static)
      for (size_t sample = 0; sample < parsed_params.num_samples; ++sample) {
        uint64_t sample_seed = parsed_params._seed + sample * 7919ull;
        auto recovery_time = RunRecoverySample(norm, parsed_params, sample_seed);
        if (recovery_time) {
          local_successes.push_back(*recovery_time);
        }
      }
#pragma omp critical
      successes.insert(successes.end(), local_successes.begin(), local_successes.end());
    }
#else
    for (size_t sample = 0; sample < parsed_params.num_samples; ++sample) {
      uint64_t sample_seed = parsed_params._seed + sample * 7919ull;
      auto recovery_time = RunRecoverySample(norm, parsed_params, sample_seed);
      if (recovery_time) {
        successes.push_back(*recovery_time);
      }
    }
#endif

    nlohmann::json output;
    output["num_samples"] = parsed_params.num_samples;
    output["num_recoveries"] = successes.size();
    output["max_t"] = parsed_params.max_t;

    if (!successes.empty()) {
      double sum = 0.0;
      for (size_t t : successes) {
        sum += static_cast<double>(t);
      }
      const double mean = sum / static_cast<double>(successes.size());
      output["avg_recovery_time"] = mean;
      if (successes.size() > 1) {
        double variance = 0.0;
        for (size_t t : successes) {
          double diff = static_cast<double>(t) - mean;
          variance += diff * diff;
        }
        variance /= static_cast<double>(successes.size() - 1);
        output["std_err_recovery_time"] = std::sqrt(variance / static_cast<double>(successes.size()));
      } else {
        output["std_err_recovery_time"] = nullptr;
      }
    } else {
      output["avg_recovery_time"] = nullptr;
      output["std_err_recovery_time"] = nullptr;
    }

    std::cout << output.dump(2) << std::endl;
  } catch (const std::exception &ex) {
    std::cerr << "[Error] " << ex.what() << std::endl;
    return 1;
  }

  return 0;
}
