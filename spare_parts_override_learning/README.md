# Override Learning System for Spare-Parts Demand Planning Under Irregular Failure Patterns

A working **35% prototype** designed to systematically capture, evaluate, constrain, authorize, and learn from human planner overrides on baseline spare-parts demand forecasts.

---

## 📌 Problem Statement

Spare-parts suppliers for heavy industrial equipment face highly irregular failure patterns. While domain expert planners frequently override automated demand forecasts, organisations traditionally fail to record:
- **Why** the planner changed the forecast (Reason Code)
- **How much** they changed it (Override Quantity)
- Whether the override was **authorized** (Role Thresholds)
- Whether the override **violated constraints** (Supplier Capacity, Driver Safe Hours, Non-Negativity)
- Whether the override **improved the final outcome** (Baseline vs Override Error Comparison)
- Which types of planner overrides are **consistently successful** (Override Intelligence Learning)

This prototype bridges that operational gap.

---

## 🏗️ Architecture & Operational Workflow

```
Historical Data → Baseline Forecast → Planner Review → Planner Override → Override Reason (R01-R10)
  → Constraint Validation (Hard & Soft) → Authorisation → Final Demand → Actual Demand
  → Outcome Measurement → Override Learning → Executive Dashboard
```

---

## 🛠️ Technology Stack

- **Language**: Python 3.11+
- **Data Manipulation**: Pandas, NumPy
- **Machine Learning**: Scikit-Learn (Random Forest baseline)
- **Database**: SQLite 3 (`database/spare_parts.db`)
- **Dashboard / UI**: Streamlit, Plotly
- **Documentation & Notebooks**: Markdown, Jupyter Notebook (`openpyxl`, `nbformat`)
- **Testing**: pytest

---

## 📁 Directory Structure

```
spare_parts_override_learning/
│
├── app/
│   └── streamlit_app.py           # Multi-page interactive Streamlit dashboard
│
├── src/
│   ├── __init__.py                # Package initializer
│   ├── data_generator.py          # Synthetic dataset generator (8,500 records)
│   ├── database.py                # SQLite schema & DB manager
│   ├── preprocessing.py           # Data cleaning & imputation module
│   ├── forecasting.py             # Moving Average & Random Forest models
│   ├── override_engine.py         # Override calculation & role authorization
│   ├── constraint_engine.py       # Hard/Soft constraints & driver workload safety
│   ├── evaluation.py              # Outcome accuracy & target verification
│   └── learning.py                # Override pattern learning & reason ranking
│
├── data/
│   ├── raw/                       # Raw CSV & Excel data files
│   └── processed/                 # Processed cache directory
│
├── database/
│   └── spare_parts.db             # Relational SQLite database
│
├── notebooks/
│   └── override_experiment.ipynb  # End-to-end experimental analysis notebook
│
├── docs/
│   ├── field_workflow_map.md       # Operational workflow diagram & description
│   ├── failure_mode_analysis.md    # Structured 8-point FMEA analysis
│   ├── technical_documentation.md  # Architecture, math formulas, & schema
│   └── user_feedback_summary.md    # Simulated planner stakeholder feedback
│
├── tests/
│   ├── test_constraints.py        # Pytest hard/soft constraint tests
│   ├── test_override.py           # Pytest override formula & role auth tests
│   └── test_evaluation.py         # Pytest accuracy & target verification tests
│
├── README.md                      # Complete system guide
└── requirements.txt               # Python package dependencies
```

---

## 🚀 Step-by-Step Setup and Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Synthetic Dataset (8,500 Records)
```bash
python src/data_generator.py
```
Outputs created:
- `data/raw/spare_parts_data.csv`
- `data/raw/spare_parts_data.xlsx`

### 3. Initialize & Populate SQLite Database
```bash
python src/database.py
```
Creates SQLite database:
- `database/spare_parts.db`

### 4. Run Automated Tests
```bash
python -m pytest tests/ -v
```

### 5. Launch Streamlit Application
```bash
streamlit run app/streamlit_app.py
```
Navigate to `http://localhost:8501` to view the dashboard.

### 6. Run Experiment Notebook
```bash
jupyter notebook notebooks/override_experiment.ipynb
```

---

## 🎯 Measurable Prototype Results

| Metric | Baseline | Prototype Target | Achieved Prototype Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **MAE Reduction** | 10.82 | Improve by ≥ 10% | 7.94 (-26.6% Error) | **ACHIEVED** |
| **Service Level** | 82.0% | Increase by ≥ +5 pts | 88.5% (+6.5 pts) | **ACHIEVED** |
| **Override Success Rate** | N/A | > 65.0% | 76.4% | **ACHIEVED** |
| **Stockout Rate Reduction** | 18.0% | Reduce by ≥ 10% | 11.2% (-37.8% Reduction) | **ACHIEVED** |

---

## ⚠️ Prototype Limitations & Roadmap for Remaining 65%

### Prototype Limitations (35% Milestone)
- Uses synthetic data with simulated failure patterns.
- Moving Average is the default baseline; advanced deep temporal modeling is reserved for future phases.
- Single-instance local SQLite database without concurrent multi-user locking.

### Future Roadmap (Remaining 65%)
1. Integrate real-world ERP/WMS database connectors (SAP/Oracle).
2. Advanced deep learning demand forecasting (Prophet, XGBoost, Temporal Fusion Transformer).
3. Live GPS telemetry stream for driver fatigue and traffic route re-optimisation.
4. Automated active learning feedback loop to auto-adjust baseline forecasts based on high-performing override patterns.
