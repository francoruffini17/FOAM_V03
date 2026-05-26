# Simulation Registry

All simulations share the same two-step loading protocol:
- **Step-0**: inflate internal gas cavities to pressure `P` (volume-dependent fluid cavity)
- **Step-1**: uniaxial compression ~75% in the **x-direction** (displacement = −15 on a 20-unit domain), recording S11, S12, S22 and x-face reaction forces RF2

The key variables across series are **mesh geometry**, **mesh type** (hexagonal vs. random), **boundary periodicity**, **Young's modulus E**, and **pre-inflation pressure P**.
Material: E (MPa), ν = 0.3, plane-stress (CPS3/CPS4), t = 1, gas: N₂ at 273 K, P₀ = 0.101325 MPa.

---

## Series Overview

| Series | Sim numbers | Mesh files | Mesh type | Periodic | E (MPa) | P (MPa) | # Sims | Ran? |
|--------|-------------|------------|-----------|----------|---------|---------|--------|------|
| SIM_000 | 000 | A004 | Hexagonal | None | 20 | 0.01 | 1 | ✅ |
| SIM_001 | 001–003 | A001–A003 | Hexagonal | None | 20 | 0.01 | 3 | ✅ |
| SIM_100 | 100 | A00A (test) | Hexagonal | None | 20 | 0.01 | 1 | ✅ |
| SIM_1000 | 1000–1039 | A010–A013 | Hexagonal | None | 20 | 0–0.64 (9 lvls) | ~36 | ❌ |
| SIM_1100 | 1100–1139 | A020–A023 | Hexagonal | None | 20 | 0–0.64 (9 lvls) | ~36 | ❌ |
| SIM_1200 | 1200–1208 | A020 | Hexagonal | None | 20 | 0–0.64 (9 lvls) | 9 | ❌ |
| SIM_1210 | 1210–1218 | A020 | Hexagonal | None | 20 | 0–0.64 (9 lvls) | 9 | ❌ |
| SIM_1300 | 1300–1308 | A030 | Hexagonal | lr | 20 | 0–0.64 (9 lvls) | 9 | ❌ |
| SIM_1310 | 1310–1318 | A030 | Hexagonal | lr | 20 | 0–0.64 (9 lvls) | 9 | ❌ |
| SIM_1320 | 1320–1328 | A031 | Hexagonal | lr | 20 | 0–0.64 (9 lvls) | 9 | ❌ |
| SIM_2000 | 2000–2008 | A2000 | Hexagonal | both | 20 | 0–0.64 (9 lvls) | 9 | ❌ |
| SIM_3000 | 3000–3228 | A3000, A3100, A3200 | Hexagonal | both | 20, 10, 5 | 0–1.28 (10 lvls) | 90 | ❌* |
| SIM_4000 | 4000–4002 | A3000 | Hexagonal | both | 20 | 0.64 | 3 | ❌ |
| SIM_5000 | 5010–5428 | R6000–R6004 | **Random** | both | 20, 10, 5 | 0–0.64 (9 lvls) | 135 | ✅ |
| SIM_6000 | 6100–6428 | R6010–R6014 | **Random** | both | 20, 10, 5 | 0–0.64 (9 lvls) | 135 | ✅ |
| SIM_9000 | 9000 | A020 | Hexagonal | None | 20 | 0 | 1 | ✅ |
| SIM_9001 | 9001 | TEST_P | Hexagonal | lr | 20 | 0 | 1 | ✅ |
| SIM_9002 | 9002 | A031 | Hexagonal | lr | 20 | 0.02 | 1 | ✅ |
| SIM_9003 | 9003 | A00B (rect) | Hexagonal | ul | 20 | 0.02 | 1 | ✅ |
| SIM_9004 | 9004 | A031 | Hexagonal | both | 20 | 0.02 | 1 | ✅ |
| SIM_9005 | 9005 | A991 | Hexagonal | both | 20 | 0.02 | 1 | ✅ |
| SIM_9998 | 9998 | A9998 | Hexagonal | both | 20 | 0.005 | 1 | ✅ |

*SIM_3000: creator scripts exist (`SIM_3000_inp_creator.py`, `SIM_3000_inp_creator_OnLY_9.py`) but no simulation folders found in `E001_Simulations/`.

Periodicity legend: `None` = free boundaries, `lr` = left-right periodic, `both` = fully periodic (left-right + top-bottom).

---

## Detailed Series Descriptions

### SIM_000 — Single baseline, no periodicity
- **Mesh**: `A004_hexagonal_mesh.mesh.json`, 1 realization, 20×20 scale
- **Loading**: P = 0.01 MPa inflation → x-compression −15
- **Purpose**: initial proof-of-concept / single-shot test

### SIM_001 — Mesh realization variability (no periodicity)
- **Meshes**: `A001`, `A002`, `A003` (3 realizations of the same hexagonal topology)
- **Loading**: P = 0.01 MPa → x-compression −15
- **Purpose**: check reproducibility across 3 different mesh realizations at fixed loading

### SIM_100 — Test mesh, single run
- **Mesh**: `A00A_Test_mesh.mesh.json`
- **Loading**: P = 0.01 MPa → x-compression −15
- **Purpose**: validation run on a dedicated test mesh geometry

### SIM_1000 — Pressure sweep, 4 mesh realizations, no periodicity
- **Meshes**: `A010`–`A013` (4 realizations)
- **E** = 20 MPa; **P** ∈ {0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64} MPa
- **Purpose**: systematic pressure-effect study on a first "medium-size" mesh family without boundary periodicity

### SIM_1100 — Pressure sweep, 4 larger mesh realizations, no periodicity
- **Meshes**: `A020`–`A023` (4 realizations, different geometry from A010 family)
- **E** = 20 MPa; same 9-pressure sweep as SIM_1000
- **Purpose**: repeat SIM_1000 study on a second mesh family to check geometry dependence

### SIM_1200 — Single mesh, pressure sweep, no periodicity
- **Mesh**: `A020` only (single realization)
- **E** = 20 MPa; 9-pressure sweep
- **Purpose**: isolate pressure effect on one mesh without realization scatter; reference for SIM_1100

### SIM_1210 — Single mesh, pressure sweep, no periodicity (created by SIM_9999 script)
- **Mesh**: `A020` (same as SIM_1200)
- **E** = 20 MPa; 9-pressure sweep
- **Purpose**: likely a re-run or variant of SIM_1200; note the creator script is named `SIM_9999_inp_creator.py` but internally starts at sim_num = 1210

### SIM_1300 — Pressure sweep, left-right periodic BCs
- **Mesh**: `A030_hexagonal_mesh.mesh.json`, periodic = `lr`
- **E** = 20 MPa; 9-pressure sweep
- **Purpose**: first left-right periodic series; removes free-edge effects on x-boundaries; enables comparison with SIM_1200 (same loading, no periodic)

### SIM_1310 — Pressure sweep, left-right periodic, mesh A030 (second creator)
- **Mesh**: `A030`, periodic = `lr`
- **E** = 20 MPa; 9-pressure sweep
- **Purpose**: separate creator script for A030 l-r periodic; likely a re-generation or variant of SIM_1300

### SIM_1320 — Pressure sweep, left-right periodic, mesh A031
- **Mesh**: `A031_hexagonal_mesh.mesh.json`, periodic = `lr`
- **E** = 20 MPa; 9-pressure sweep
- **Purpose**: left-right periodic study on a second mesh realization (`A031`) for statistical comparison with SIM_1310

### SIM_2000 — Fully periodic, single mesh, pressure sweep
- **Mesh**: `A2000_hexagonal_mesh.mesh.json`, periodic = `both`
- **E** = 20 MPa; 9-pressure sweep; compression via periodic DOF (BC_9999997)
- **Purpose**: first fully periodic series; eliminates all free-edge effects; enables proper bulk-modulus / homogenization analysis

### SIM_3000–3228 — Main hexagonal parametric study *(primary hexagonal dataset)*
- **Meshes**: `A3000`, `A3100`, `A3200` (3 hexagonal geometries, periodic = `both`)
- **E** ∈ {20, 10, 5} MPa; **P** ∈ {0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28} MPa
- **Total**: 3 meshes × 3 E × 10 P = **90 simulations**
- **Purpose**: primary hexagonal-foam dataset; full sweep of stiffness and inflation pressure across 3 mesh topologies; intended for force-chain analysis, homogenization, and comparison with random meshes

### SIM_4000 — Numerical step-size sensitivity study
- **Mesh**: `A3000`, periodic = `both`; E = 20 MPa, P = 0.64 MPa (single condition)
- **Variants**: max increment size ∈ {0.001, 0.0001, 0.00001} → 3 simulations
- **Purpose**: verify numerical convergence; check sensitivity of results to Abaqus time-stepping

### SIM_5000–5428 — First random-mesh dataset *(primary random dataset 1)*
- **Meshes**: `R6000`–`R6004` (5 **random** foam mesh realizations, periodic = `both`)
- **E** ∈ {20, 10, 5} MPa; **P** ∈ {0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64} MPa
- **Total**: 5 meshes × 3 E × 9 P = **135 simulations** (present in `E001_Simulations/`)
- **Purpose**: repeat the SIM_3000 parametric study on random (disordered) foam structures; study effect of topological disorder

### SIM_6000–6428 — Second random-mesh dataset *(primary random dataset 2)*
- **Meshes**: `R6010`–`R6014` (5 **different** random mesh realizations, periodic = `both`)
- **E** ∈ {20, 10, 5} MPa; same 9-pressure sweep
- **Total**: 5 meshes × 3 E × 9 P = **135 simulations** (present in `E001_Simulations/`)
- **Purpose**: increase statistical sample of random meshes beyond SIM_5000; validate trends and measure realization-to-realization variability

### SIM_9000 — No-pressure test, constrained y-faces, no periodicity
- **Mesh**: `A020`, E = 20 MPa, P = 0 (no inflation)
- **Step-1 BCs**: x-negative fixed in y, x-positive displaced −15 in x, both y-faces pinned in x
- **Purpose**: special boundary-condition test with no gas; explores constrained compression (prevents lateral expansion); differs from all other series in Step-1 BCs

### SIM_9001–9005 — Individual test / debug runs

| SIM | Mesh | Periodic | P (MPa) | Notes |
|-----|------|----------|---------|-------|
| 9001 | `TEST_P` | lr | 0 | Test left-right periodicity on dedicated test mesh, no inflation |
| 9002 | `A031` | lr | 0.02 | Single test on A031 with l-r periodic |
| 9003 | `A00B_Test_mesh_rectangle` | ul | 0.02 | Test on rectangular test mesh with up-left periodicity |
| 9004 | `A031` | both | 0.02 | Same mesh as 9002 but full (both-direction) periodicity |
| 9005 | `A991` | both | 0.02 | Test on mesh A991, fully periodic |

**Purpose**: one-off tests during development of periodic boundary condition implementation.

### SIM_9998 — Single mesh A9998, fully periodic
- **Mesh**: `A9998_hexagonal_mesh.mesh.json`, periodic = `both`
- **E** = 20 MPa, P = 0.005 MPa
- **Purpose**: isolated test on a dedicated mesh; likely used to validate a specific geometry or check a new feature

---

## Assessment: Which Series Are Useful

| Series | Usefulness | Reason |
|--------|-----------|--------|
| SIM_000–100 | Low — prototype | Superseded by larger studies; useful only as minimal reproducible examples |
| SIM_1000–1320 | Low — never ran | Creator scripts exist but no simulation folders; hexagonal non-periodic series was abandoned in favour of periodic approach |
| SIM_2000 | Low — superseded | Single-mesh fully periodic; replaced by larger SIM_3000 sweep |
| SIM_3000–3228 | **High — main hex dataset** | Full E × P × mesh parametric study; never ran but intended as the hexagonal reference |
| SIM_4000 | Medium — numerical study | Useful for justifying step-size choices in SIM_3000/5000/6000 |
| SIM_5000–5428 | **High — main random dataset 1** | Ran successfully; 135 sims across 5 random meshes and full E/P range |
| SIM_6000–6428 | **High — main random dataset 2** | Ran successfully; 135 sims across a second set of 5 random meshes |
| SIM_9000–9005, 9998 | Low — debug/test | One-off tests; keep as reference for boundary condition variants |
