# ADR 002: Choice of Decimal over Float for SREN Compliance

## Context
SREN Law (NOR:ECOI2530768A) mandates a 0.00€ limit. Floating-point errors could lead to unauthorized data egress.

## Decision
We use `decimal.Decimal` for all financial and volumetric calculations.

## Consequences
While marginally slower than `float`, the overhead is < 0.1ms per TX. This is a non-issue compared to UCP latency. Scalability is ensured via the stateless Nature of the middleware.
