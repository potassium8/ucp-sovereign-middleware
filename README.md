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

## ⚖️ Standards & Compliance
- **NIS2 Framework:** Structured logging with UUID transaction correlation for immutable audit trails.
- **Resilience:** Circuit-breaker logic (Fail-Safe) on Cloud Billing ingestion to prevent data leakage during API outages.
- **Precision:** Binary-to-decimal valuation using ISO/IEC 80000-13 standards.

## Architecture
Using a Hexagonal Architecture to isolate Business Logic (French Law) from Infrastructure.

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
