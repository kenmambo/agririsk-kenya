# Contributing to AgriRisk Kenya

Thank you for your interest in contributing to **AgriRisk Kenya**! We welcome contributions from data scientists, software engineers, remote sensing specialists, agricultural economists, and humanitarian practitioners.

This project is an open-source research and decision-support prototype. We strive to maintain production-quality code, scientific rigor, and complete reproducibility.

---

## 1. Code of Conduct
We are committed to providing a welcoming, inclusive, and harassment-free environment. All contributors and participants are expected to uphold standards of mutual respect, constructive feedback, and academic honesty.

---

## 2. Getting Started

### Prerequisites
- Python 3.12+
- `uv` package manager ([astral-sh/uv](https://github.com/astral-sh/uv))
- Git

### Development Environment Setup
```bash
# Clone the repository
git clone https://github.com/kenmambo/agririsk-kenya.git
cd agririsk-kenya

# Sync virtual environment and dependencies
uv sync

# Install editable package
uv pip install -e .

# Run the test suite to verify baseline setup
uv run pytest
```

---

## 3. Contribution Workflow

1. **Check Existing Issues:** Before implementing a major change or feature, check open issues or open a new issue describing your proposed approach.
2. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Write Clean, Documented Code:**
   - Adhere to **PEP 8** style guidelines.
   - Include type hints for all public functions, classes, and methods.
   - Write clear docstrings explaining inputs, returns, and algorithmic logic.
4. **Ensure Strict Data Integrity & Zero Leakage:**
   - Any time-series processing must respect temporal ordering.
   - Forward rolling windows or future target leakage in feature engineering will cause pull requests to be rejected.
5. **Add Automated Unit Tests:**
   - Every new feature, data transformation, or model must include unit tests in `tests/`.
   - Run the full test suite before committing:
     ```bash
     uv run pytest tests/ -v
     ```
6. **Submit a Pull Request:**
   - Push your branch to GitHub and open a Pull Request against `main`.
   - Provide a clear PR description detailing:
     - The motivation / problem addressed.
     - The technical approach taken.
     - Verification steps and test outputs.

---

## 4. Repository Style & Architecture Guidelines
- **Modularity:** Keep core business logic inside `src/agririsk/`. Do not embed extensive feature processing or modeling directly inside Streamlit view scripts (`app/`).
- **Configuration over Hardcoding:** Put file paths, URLs, and external constants inside `config/data_sources.yaml` or `src/agririsk/core/constants.py`.
- **Scientific Humility:** Ensure all new documentation, reports, and UI elements clearly preserve the research disclaimer and avoid making unsupported claims of operational deployment or causal proof.

---

## 5. Contact & Questions
For questions, bug reports, or collaboration proposals, please open a GitHub Issue or reach out via [kenmambo](https://github.com/kenmambo).
