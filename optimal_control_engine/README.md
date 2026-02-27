# Energy-Constrained Optimal Control for Solar Electric Vehicles

A physics-informed optimal control framework that computes **time-optimal velocity policies** for solar electric vehicles subject to battery dynamics, power limits, terrain constraints, and stochastic environmental energy input.

This repository implements a **nonlinear constrained optimization system** combining high-fidelity physics simulation with trajectory optimization to derive energy-aware driving strategies for long-distance solar racing.

---

## Key Contributions

- Physics-consistent vehicle energy model incorporating aerodynamic drag, rolling resistance, gradient forces, and regenerative braking
- Battery-constrained trajectory optimization using nonlinear constrained programming (SLSQP)
- Solar irradiance modeling for endogenous energy generation
- Route preprocessing pipeline with elevation smoothing and spatial resampling
- Policy discretization using chunk-based velocity control with acceleration regularization
- Constraint-aware solver with diagnostic callback and feasibility analysis

---

## Problem Formulation

The task is posed as a **nonlinear optimal control problem**.

### Objective
- Minimize total travel time

### Decision Variables
- Race start time
- Piecewise velocity policy over spatial chunks

### State Dynamics
- Battery state of charge evolution
- Power flow balance between solar input, regenerative braking, and propulsion demand

### Constraints
- Minimum battery state of charge
- Maximum battery current
- Overcharge prevention
- Acceleration feasibility

---

## System Architecture

```
Route Data Pipeline → Physics Simulator → Constraint Engine → Nonlinear Optimizer → Velocity Policy
```

---

## Physics Model

The simulation models resistive forces:

- Aerodynamic drag proportional to velocity squared
- Rolling resistance
- Gravitational gradient forces

Electrical power is computed via drivetrain and regenerative efficiencies. Battery dynamics follow cumulative energy balance driven by solar input and propulsion demand.

---

## Optimization Method

The framework employs **Sequential Least Squares Programming (SLSQP)** due to:

- Nonlinear dynamics
- Inequality constraints
- High-dimensional decision space
- Need for efficient gradient-informed search

The solver iteratively refines velocity policies while respecting battery and hardware limits.

---

## Results

The optimizer discovers a policy characterized by:

- High steady-state cruising velocity
- Selective deceleration on steep gradients to avoid current violations
- Full utilization of battery capacity at finish
- Alignment of travel window with peak solar irradiance

---

## Repository Structure

```
src/
├── data_pipeline/
├── physics/
├── optimization/
├── simulation/
└── utils/
```

---

## Quantitative Performance

- **Optimal race time:** 3.48 hours  
- **Minimum battery SoC:** 3%  
- **Peak battery current:** 50 A  
- **Solar energy generated:** 4.56 kWh  
- **Electrical energy consumed:** 7.47 kWh  

---

## Numerical Stability & Robustness

- Gradient-safe haversine computation
- Floating point clipping for spherical geometry
- Constraint feasibility diagnostics
- Degenerate policy fallback generation

---

## Research Extensions

- Stochastic irradiance modeling
- Model predictive control formulation
- Reinforcement learning velocity policies
- Battery thermal coupling
- Multi-stage global optimization
