"""Exact one-sided binomial confidence bounds (conditional on independent trials)."""
import math


def precision_lower(correct: int, total: int, confidence: float = .95) -> float:
    if not 0 <= correct <= total or not 0 < confidence < 1:
        raise ValueError("invalid counts or confidence")
    if correct == 0:
        return 0.0
    if correct == total:
        return (1 - confidence) ** (1 / total)
    # P(X >= correct | p) = alpha. Sum the usually short failure-count tail
    # in log space to avoid overflowing binomial coefficients.
    failures = total - correct
    def tail(p):
        logs = [math.lgamma(total + 1) - math.lgamma(j + 1) - math.lgamma(total - j + 1)
                + j * math.log1p(-p) + (total - j) * math.log(p)
                for j in range(failures + 1)]
        top = max(logs)
        return math.exp(top) * sum(math.exp(v - top) for v in logs)
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if tail(mid) < 1 - confidence:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
