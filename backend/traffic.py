import random


def arrival_times(rate: float, duration: float, seed: int = 42):
    """Poisson arrivals generated deterministically from a seeded RNG."""
    rng = random.Random(seed)
    t, arrivals = 0.0, []
    while rate > 0:
        t += rng.expovariate(rate)
        if t > duration:
            break
        arrivals.append(t)
    return arrivals
