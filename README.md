# NVision Retirement Simulator

This repository contains the **NVision Retirement Simulator**, a free, open–source retirement planning dashboard inspired by the capabilities of **Boldin** (formerly NewRetirement).  The goal of this project is to allow individuals to build and evaluate personalised retirement plans without a subscription or proprietary data.  You can run the app locally with one command (`streamlit run app.py`), load and save scenarios, explore Roth conversion strategies and Monte Carlo probability of success, and export reports.

## Features

* **Monte Carlo engine** – simulate at least 1 000 random return paths to estimate the probability that a plan succeeds.  The engine models uncertainty in future market returns by drawing random annual returns instead of assuming a single average value.  This approach mirrors Boldin’s own Monte Carlo simulation, which runs thousands of trials with random returns to illustrate a range of possible outcomes rather than one fixed path【105533608753670†L128-L149】.

* **RMD and Social Security rules** – the calculators implement the new Required Minimum Distribution (RMD) ages enacted by the SECURE Act.  Starting in 2023 the age for first RMD rises to 73 and increases again to 75 in 2033; depending on birth year the required age is 73 for those born 1951‑1959 and 75 for those born 1960 or later【990996736051385†L120-L160】.  The Social Security module accepts your Primary Insurance Amount (PIA) and claiming age and applies early‑retirement reductions or delayed retirement credits to estimate annual benefits, similar to Boldin’s planner【54758672279077†L37-L49】.

* **Taxes** – simplified U.S. federal tax brackets for 2025 are embedded and applied progressively to ordinary income.  Long‑term capital gains are taxed using the 0 %, 15 % and 20 % brackets.  These brackets come from IRS guidance for 2025 (via the Tax Foundation)【284892234855781†L236-L243】.  The tables live in `retirement_planner/data/tax_tables.json` and can be edited to adjust for future years or different filing statuses.

* **Roth conversion modelling** – the system supports converting money from traditional (tax‑deferred) accounts to Roth accounts before RMD age.  Conversions add ordinary income in the year of the conversion and may either pay the tax from taxable savings or from the amount converted.  A simple Roth Conversion Explorer sweeps through different annual conversion caps and visualises the impact on taxes and probability of success.

* **Scenario management** – unlimited named scenarios are supported.  Each scenario records a full copy of all inputs (age, accounts, income, spending, assumptions, withdrawal policy and Roth conversion settings).  You can save to or load from JSON files, switch between scenarios, and compare outcomes side‑by‑side on the dashboard.  The comparison view shows key metrics such as chance of success, median/10th/90th percentile retirement income, lifetime taxes and terminal net‑worth.

* **Interactive Streamlit UI** – all inputs live in sidebar forms with validation and sensible defaults.  The main pages are:

  1. **Home** – displays your probability of success as a gauge, fan charts of projected account balances and income bands, and summary metrics.
  2. **Scenario Compare** – summarises each scenario’s key performance indicators in a sortable table and small multiple charts.
  3. **Roth Conversion Explorer** – allows you to vary conversion limits and tax payment options.  A heatmap shows how different conversion schedules affect lifetime taxes and success probability.
  4. **Ledger/Audit** – exposes a year‑by‑year ledger of starting balance, contributions, investment returns, withdrawals, RMDs, conversions and taxes by account.  You can export this ledger to CSV.

* **Exports** – charts can be saved as PNG files; tabular data can be exported as CSV; and a comprehensive **Plan Summary** PDF bundles the main charts and metrics into a single document.  All exports occur locally; no personal data leaves your machine.

* **Testing and Documentation** – core calculators are unit‑tested with `pytest`.  Every module includes docstrings and doctest examples to illustrate correct usage.  The simplified tax tables, RMD table and other assumptions are documented in `retirement_planner/data/tax_tables.json` and in this README.

## Installation and Running

Follow these steps to run the dashboard on a Windows computer.  All tools are free and open‑source; the only requirement is a working installation of **Python 3.11** or later.

1. **Install Python** – if you do not already have Python 3.11+, download and install it from [python.org](https://www.python.org/downloads/).  During installation ensure that you tick the option to add Python to your system PATH.

2. **Download the project** – clone this repository or download the ZIP archive and extract it to a folder, e.g. `C:\retirement_planner`.

3. **Create a virtual environment (optional but recommended)** – open a Command Prompt or PowerShell window and run:

   ```sh
   cd C:\retirement_planner
   python -m venv venv
   .\venv\Scripts\activate
   ```

   Activating a virtual environment isolates the project’s dependencies from other Python packages on your system.

4. **Install dependencies** – with the virtual environment activated, install the required packages using pip:

   ```sh
   pip install -r requirements.txt
   ```

5. **Run the app** – start the Streamlit server with a single command:

   ```sh
   streamlit run app.py
   ```

   Your default web browser should open automatically to `http://localhost:8501`.  If it does not, manually visit that address.  The dashboard will load with a sample plan pre‑populated; you can explore the interface immediately or edit inputs in the sidebar to create your own scenario.

6. **Saving and loading plans** – use the **Save/Load** buttons at the bottom of the sidebar to export your current scenario to a JSON file or import a previously saved plan.  The file is stored locally on your computer.

7. **Testing** – to run the unit tests (optional), execute the following command from the project directory:

   ```sh
   pytest -v
   ```

## Repository Structure

```
RetirementSimulator/
├── app.py               # Streamlit application entry point
├── retirement_planner/  # Core package housing calculators and components
│   ├── __init__.py
│   ├── calculators/     # Financial calculators (taxes, RMD, Social Security, Monte Carlo, Roth)
│   │   ├── __init__.py
│   │   ├── taxes.py
│   │   ├── rmd.py
│   │   ├── social_security.py
│   │   ├── monte_carlo.py
│   │   └── roth.py
│   ├── components/      # UI components and charts for Streamlit
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── charts.py
│   └── data/
│       ├── tax_tables.json  # Simplified federal and state tax brackets (editable)
│       └── sample_plan.json # Example scenario demonstrating full functionality
├── tests/               # Unit tests for calculators
│   ├── __init__.py
│   ├── test_taxes.py
│   ├── test_rmd.py
│   ├── test_social_security.py
│   ├── test_monte_carlo.py
│   └── test_roth.py
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation (this file)
```

## Assumptions and Simplifications

This project strives to balance realism with computational efficiency.  The following simplifications are made:

* Returns are assumed to follow a normal distribution around a user‑specified mean with built‑in volatility assumptions for each account type.  Accounts can optionally be correlated 100 % to reflect broad market movements, consistent with Boldin’s update to have all accounts move together【105533608753670†L252-L277】.

* The tax engine uses simplified federal brackets for single filers in 2025【284892234855781†L236-L243】.  Additional schedules (married filing jointly, head of household) and detailed provisions like the Alternative Minimum Tax, self‑employment tax, and deductions beyond the standard deduction are outside the scope of this demonstration.  State taxes are loaded from `retirement_planner/data/tax_tables.json` and default to the 2025 Michigan flat tax; you can edit this file for other states.

* Social Security calculations accept a Primary Insurance Amount (PIA) rather than building a full earnings history.  The model applies reductions or credits for claiming early or delaying beyond full retirement age【54758672279077†L37-L49】.  Spousal and survivor benefits are simplified: the surviving spouse receives the larger of their own or their spouse’s benefit after the first death.

* Required Minimum Distributions use the Uniform Lifetime Table that became effective in 2022 and apply the new start ages dictated by the SECURE Act【990996736051385†L120-L160】.  This table and logic can be extended for future regulatory changes.

* Roth conversion strategies are modelled heuristically to illustrate the concept.  A more sophisticated optimisation (e.g. the greedy algorithm referenced by Boldin’s Roth Conversion Explorer【751282549032066†L130-L174】) is beyond the scope of this example but could be added.

These design choices keep the system fast (<3 s for 1 000 Monte Carlo paths) and transparent.  Because all code and data are open, you can refine the logic or plug in more detailed models according to your preferences.

## Acknowledgements

This project drew inspiration from Boldin’s retirement planning platform.  Their publicly available articles describing the purpose and mechanics of Monte Carlo simulations【105533608753670†L128-L149】, the new SECURE Act RMD start ages【990996736051385†L120-L160】 and the treatment of Social Security benefits【54758672279077†L37-L49】 helped guide the high‑level specifications.  However, all code in this repository is original and free to use or modify.
