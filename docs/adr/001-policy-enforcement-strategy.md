# ADR 001: Policy Enforcement at Logic Level (SREN Compliance)

## Context
Compliance with NOR:ECOI2530768A (Zero-Egress) cannot be reliably offloaded to standard Cloud Service Providers (CSPs) due to legacy billing propagation delays.

## Decision
We enforce the SREN policy directly within the UCP middleware via `Decimal` precision auditing. 

## Rationale
By the time an AWS Cost Explorer alert triggers, the legal violation is already consummated. Our middleware prevents the egress *before* the packet leaves the sovereign perimeter.

## Note to Reviewers
Attempting to bypass this via a simple Load Balancer rule will fail to address the "Signal Ownership" requirement of the SREN Law. The audit must be semantic, not just volumetric.
