# EDA summary — Kaggle vehicle insurance fraud (carclaims.csv)

- rows: 15,420; columns: 33
- fraud rate: 5.99% (923 positives)
- years: [np.int64(1994), np.int64(1995), np.int64(1996)]
- missing values: 0
- `PolicyNumber` unique per row: True (id → excluded)

## Fraud rate by feature value (used features only)

- **Month** (12 values) — Mar: 7.5%, Aug: 7.5%, May: 6.9%, Feb: 6.5%
- **DayOfWeek** (7 values) — Sunday: 7.0%, Saturday: 6.7%, Friday: 6.3%, Monday: 6.1%
- **AccidentArea** (2 values) — Rural: 8.3%, Urban: 5.7%
- **Fault** (2 values) — Policy Holder: 7.9%, Third Party: 0.9%
- **VehicleCategory** (3 values) — Utility: 11.3%, Sedan: 8.2%, Sport: 1.6%
- **VehiclePrice** (6 values) — less than 20,000: 9.4%, more than 69,000: 8.7%, 40,000 to 59,000: 6.7%, 20,000 to 29,000: 5.2%
- **Days:Policy-Accident** (5 values) — none: 16.4%, 8 to 15: 9.1%, 1 to 7: 7.1%, 15 to 30: 6.1%
- **Days:Policy-Claim** (4 values) — 8 to 15: 14.3%, 15 to 30: 10.7%, more than 30: 6.0%, none: 0.0%
- **PastNumberOfClaims** (4 values) — none: 7.8%, 1: 6.2%, 2 to 4: 5.4%, more than 4: 3.4%
- **AgeOfVehicle** (8 values) — 4 years: 9.2%, new: 8.6%, 3 years: 8.6%, 5 years: 7.0%
- **PoliceReportFiled** (2 values) — No: 6.0%, Yes: 3.7%
- **WitnessPresent** (2 values) — No: 6.0%, Yes: 3.4%
- **BasePolicy** (3 values) — All Perils: 10.2%, Collision: 7.3%, Liability: 0.7%
- **Deductible** (4 values) — 300: 25.0%, 500: 17.9%, 700: 5.8%, 400: 5.8%

## Excluded columns and their fraud-rate spread (why they are tempting but not used)

- **Sex** — spread 4.3% … 6.3%
- **MaritalStatus** — spread 3.9% … 8.6%
- **Age** — spread 0.0% … 16.7%
- **AgeOfPolicyHolder** — spread 5.0% … 14.8%
- **RepNumber** — spread 4.8% … 7.0%
- **Make** — spread 0.0% … 25.0%
- **Year** — spread 5.2% … 6.7%
- **PolicyType** — spread 0.0% … 13.8%
- **AgentType** — spread 1.7% … 6.1%
- **NumberOfSuppliments** — spread 4.8% … 6.7%
- **AddressChange-Claim** — spread 5.2% … 75.0%
- **NumberOfCars** — spread 0.0% … 7.8%
- **DriverRating** — spread 5.6% … 6.2%
- **WeekOfMonth** — spread 5.6% … 6.3%
- **WeekOfMonthClaimed** — spread 5.3% … 6.4%
- **DayOfWeekClaimed** — spread 0.0% … 7.9%
- **MonthClaimed** — spread 0.0% … 8.2%
