# Field Workflow Map

This document outlines the complete operational lifecycle of spare-parts demand planning, planner overrides, constraint validation, fulfillment, and override learning.

## Complete Workflow Diagram

```
Equipment Failure
      ↓
Failure Signal
      ↓
Historical Demand
      ↓
Baseline Forecast
      ↓
Planner Review
      ↓
Planner Override
      ↓
Reason Code (R01–R10)
      ↓
Constraint Validation (Hard & Soft)
      ↓
Authorisation (Role Threshold Check)
      ↓
Final Demand Calculation
      ↓
Spare-Part Fulfillment & Logistics
      ↓
Actual Demand Realized
      ↓
Outcome Measurement (Error Comparison)
      ↓
Override Learning (Pattern Intelligence)
      ↓
Executive Dashboard & Policy Tuning
```

## Step-by-Step Stage Breakdown

### 1. Equipment Failure & Failure Signal
- An operational asset (e.g. Heavy Excavator EX-900 or Turbine GT-4000) experiences component failure or scheduled maintenance.
- Telemetry sensors or field technicians log a failure signal and request replacement parts.

### 2. Historical Demand & Baseline Forecast
- Historical consumption data is processed by the statistical engine.
- A **Moving Average Forecast** (or ML model) generates an unadjusted **Baseline Forecast**.

### 3. Planner Review & Override
- The domain expert planner reviews the baseline forecast alongside real-time field context.
- If the baseline is inaccurate due to known field conditions (e.g., sudden equipment cluster or customer emergency), the planner enters an **Override Quantity**.
- The planner **must select a mandatory Reason Code** (R01–R10) and optional justification comment.

### 4. Constraint Validation & Authorisation
- The **Hard Constraint Engine** validates mandatory rules:
  - Supplier Capacity limit check
  - Driver Safe Workload limit check (≤ 100% maximum safe hours)
  - Demand Non-Negativity check (Final Demand ≥ 0)
  - Mandated Reason Code present
- The **Authorisation Engine** checks user role limits:
  - Junior Planner: ≤ 20% adjustment limit
  - Senior Planner: ≤ 50% adjustment limit
  - Planning Manager: ≤ 100% adjustment limit
- Overrides exceeding role limits trigger `PENDING APPROVAL`.

### 5. Final Demand & Fulfillment
- Final Demand is calculated: `Final Demand = Baseline Forecast + Override Quantity`.
- Logistics plans dispatch using safe drivers and available transport assets.

### 6. Actual Demand & Outcome Measurement
- As actual consumption is recorded post-event:
  - `Baseline Error = |Baseline Forecast - Actual Demand|`
  - `Override Error = |Final Demand - Actual Demand|`
  - If `Override Error < Baseline Error` → `Override Improved = YES`.

### 7. Override Learning & Dashboard Feedback
- The system aggregates success rates by reason code, equipment type, part, region, and planner role.
- Insights identify high-performing reasons (e.g., R01 Equipment Failure) vs low-performing reasons needing policy review.
