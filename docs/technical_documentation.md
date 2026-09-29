# Technical Documentation

## Architecture Overview

The **Override Learning System for Spare-Parts Demand Planning** is built as a modular Python-based prototype featuring SQLite database storage, core analytical modules, automated constraint validation engines, and a Streamlit dashboard.

```
                           +------------------------+
                           |  Synthetic Data / CSV  |
                           +-----------+------------+
                                       |
                                       v
                           +------------------------+
                           |  src/database.py       |
                           |  SQLite (spare_parts)  |
                           +-----------+------------+
                                       |
     +---------------------------------+---------------------------------+
     |                                 |                                 |
     v                                 v                                 v
+-----------------------+   +-----------------------+   +-----------------------+
|  src/forecasting.py   |   | src/override_engine.py|   |src/constraint_engine. |
|  Moving Average / RF  |   | Reason Mapping & Auth |   | Hard/Soft Constraints |
+-----------+-----------+   +-----------+-----------+   +-----------+-----------+
            |                           |                           |
            +---------------------------+---------------------------+
                                        |
                                        v
                            +-----------------------+
                            |   src/evaluation.py   |
                            |  Outcome & Targets    |
                            +-----------+-----------+
                                        |
                                        v
                            +-----------------------+
                            |    src/learning.py    |
                            | Override Intelligence |
                            +-----------+-----------+
                                        |
                                        v
                            +-----------------------+
                            |  app/streamlit_app.py |
                            | Executive Dashboard   |
                            +-----------------------+
```

## Mathematical Formulas & Algorithms

### 1. Final Demand Calculation
$$\text{Final Demand} = \text{Baseline Forecast} + \text{Override Quantity}$$

### 2. Override Error Comparison
$$\text{Baseline Error} = |\text{Baseline Forecast} - \text{Actual Demand}|$$
$$\text{Override Error} = |\text{Final Demand} - \text{Actual Demand}|$$
$$\text{Override Improved} = \begin{cases} \text{YES} & \text{if } \text{Override Error} < \text{Baseline Error} \\ \text{NO} & \text{otherwise} \end{cases}$$

### 3. Forecast Accuracy Metrics
$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$
$$\text{WMAPE} = \frac{\sum_{i=1}^{n} |y_i - \hat{y}_i|}{\sum_{i=1}^{n} y_i} \times 100\%$$
$$\text{Bias} = \frac{1}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)$$

### 4. Multi-Objective Decision Score (0-100 scale)
$$\text{Score} = w_c \cdot S_{\text{cost}} + w_t \cdot S_{\text{time}} + w_e \cdot S_{\text{emissions}} + w_r \cdot S_{\text{reliability}}$$

Where:
- **Strategy A (Cost-focused)**: $w_c = 0.50, w_t = 0.20, w_e = 0.10, w_r = 0.20$
- **Strategy B (Reliability-focused)**: $w_c = 0.15, w_t = 0.15, w_e = 0.10, w_r = 0.60$

## Database Schema (SQLite `database/spare_parts.db`)

- **users**: `user_id` (PK), `user_name`, `role`, `max_override_pct`
- **parts**: `part_id` (PK), `part_name`, `inventory_level`, `safety_stock`, `supplier_capacity`, `lead_time_days`
- **equipment**: `equipment_id` (PK), `equipment_type`, `customer_id`, `region`
- **forecasts**: `forecast_id` (PK), `record_id` (UQ), `part_id` (FK), `equipment_id` (FK), `historical_demand`, `baseline_forecast`, `actual_demand`
- **overrides**: `override_id` (PK), `record_id` (FK), `planner_id`, `planner_role`, `override_quantity`, `reason_code`, `reason_comment`, `final_demand`, `approval_status`
- **constraints**: `constraint_id` (PK), `override_id` (FK), `hard_status`, `soft_status`, `violation_details`
- **drivers**: `driver_id` (PK), `driver_name`, `available_hours`, `assigned_hours`, `maximum_safe_hours`, `workload_percentage`, `safety_status`
- **deliveries**: `delivery_id` (PK), `record_id` (FK), `driver_id` (FK), `vehicle_type`, `delivery_distance_km`, `estimated_cost`, `estimated_emissions`
- **outcomes**: `outcome_id` (PK), `record_id` (FK), `baseline_error`, `override_error`, `override_improved`, `stockout_flag`, `service_level`
