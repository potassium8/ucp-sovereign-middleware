# UCP Sovereign Middleware & SREN Auditor

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Legal](https://img.shields.io/badge/Compliance-NOR%3AECOI2530768A-red)

**WARNING**
This middleware enforces strict adherence to Article 27 of Law n° 2024-449 (SREN). Any cloud provider configuration detecting egress fees > 0.00€ will result in a hard blocking of UCP (Universal Commerce Protocol) agent transactions.

## Context
As Universal Commerce Protocol (UCP) becomes the standard for Agentic Commerce, organizations risk losing control over their data "signal" and incurring massive hidden costs through unmonitored egress.

This repository implements a Sovereign Interception Layer. It ensures that your catalogue data is only exposed to Agents (Google, OpenAI) if:
1. The infrastructure guarantees Zero-Egress Fees (as per Arrêté du 17/11/2025).
2. The Agent's intent provides a positive ROI vs. Data Leakage risk.

## Standards & Compliance
- **NIS2 Framework:** Structured logging with UUID transaction correlation for immutable audit trails.
- **Resilience:** Circuit-breaker logic (Fail-Safe) on Cloud Billing ingestion to prevent data leakage during API outages.
- **Precision:** Binary-to-decimal valuation using ISO/IEC 80000-13 standards.

## Architecture
Using a Hexagonal Architecture to isolate Business Logic (French Law) from Infrastructure.

## Technical Deep Dive & FAQ

1. Why use Decimal instead of float?

In most applications, floating-point errors are acceptable. In statutory compliance, they are not. Law NOR:ECOI2530768A mandates a 0.00€ limit. A 10^-9 rounding error could technically constitute a violation. We use decimal.Decimal with a precision of 28 to ensure our audit is legally irrefutable.

2. What about the 1.02 overhead constant?

Network billing is based on "on-wire" data. Sending 1GB of application payload results in ~1.02GB of billed traffic due to TCP/IP headers and TLS 1.3 encapsulation/padding. Our middleware integrates this 2% safety margin to detect threshold breaches before they are processed by the Cloud Provider's billing engine.

3. Isn't Hexagonal Architecture overkill?

No. Sovereignty requires provider independence. By decoupling the SREN Enforcement Logic from the Billing Adapters, the middleware remains Cloud-Agnostic. Moving from AWS to a Sovereign Cloud (Scaleway/OVH) requires zero changes to the core compliance engine.

4. How do you handle API Latency?

To prevent the middleware from becoming a bottleneck, the BillingProvider implements a TTL-based Cache. Billing rates are refreshed every 60 seconds, reducing the overhead per transaction to < 0.1ms while maintaining real-time protection.

```mermaid
sequenceDiagram
    participant GoogleAgent as Google UCP Agent
    participant Firewall as Sovereign Middleware
    participant Policy as SREN Policy Engine
    participant AWS as Cloud Billing

    GoogleAgent->>Firewall: Request Catalog Ingestion (Intent: BUY)
    Firewall->>AWS: Check Egress Rate
    AWS-->>Firewall: Rate = 0.09 EUR/GB
    Firewall->>Policy: Validate against NOR:ECOI2530768A
    Policy-->>Firewall: VIOLATION DETECTED
    Firewall-->>GoogleAgent: 403 FORBIDDEN (Legal Reason: Data Sovereignty)
