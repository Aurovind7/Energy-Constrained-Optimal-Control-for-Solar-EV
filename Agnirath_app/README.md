# AgniRath: Solar Car Race Strategy Optimizer

This project determines the optimal speed profile for a solar car to minimize race time between Chennai and Bangalore, subject to the vehicle's physical and electrical limits.

---

## Model Description

The model finds the optimal strategy by coupling a detailed physics simulation with a powerful non linear optimizer (Scipy's SLSQP).

### 1. High Fidelity Route Preparation
The model's foundation is a high resolution route profile. Raw route geometry and elevation are fetched from the OpenRouteService API and then **resampled** into a uniform series of **100 meter segments**. This ensures that physics calculations are consistent and accurate across the entire race.

### 2. Physics & Energy Simulation
For any given velocity profile, the simulation calculates the consequences based on these core physics:
* **Forces:** The total resistive force (F_resistive) is the sum of **Aerodynamic Drag** (F_drag ∝ v^2), **Rolling Resistance** (F_rolling), and **Gravitational Force** (F_gradient) on hills.
* **Power:** Electrical power (P_elec) is calculated from the mechanical power required at the wheels, accounting for separate efficiencies for propulsion and regenerative braking.
* **Energy Balance:** The battery's State of Charge (SoC) is tracked across the race using the net power for each time step: E_new = E_old + (P_solar - P_elec) ⋅ Δt

### 3. Optimization
* **Objective:** To **minimize total race time**.
* **Decision Variables:** The optimizer controls the "start_hour" (to maximize solar gain) and a series of "chunk_velocities" (a target speed for each 1.5 km segment of the race).
* **Constraints:** The strategy must obey these physical rules:
    * Battery SoC must remain above a 3% minimum.
    * Battery current draw cannot exceed its 50A hardware limit.
    * Overcharging the battery is not allowed.
    * Acceleration between chunks is limited for a smooth profile.

---

## Key Assumptions

The model is a simplification of reality based on these key assumptions:

#### Vehicle Model
* Vehicle parameters (mass, drag area, efficiencies, etc) are constant.
* Battery and solar panel performance are not affected by temperature.
* The battery provides the nominal voltage regardless of SoC or load.

#### Environmental Model
* The solar irradiance is based on a **perfectly clear day**, modeled as a smooth sine wave with no cloud cover.
* There is **no wind** resistance or assistance.
* Air density is constant throughout the route.

#### Driving & Route Model
* The vehicle travels at a **constant speed** within each micro segment.
* The model does not account for traffic, stop signs, or slowing for sharp turns.
* Altitude data is smoothed to remove GPS noise, representing a more gradual road profile.

---

## Optimal Strategy Insights

The resulting strategy is not simply to drive as fast as possible. The optimizer's key insight is to drive at a high, steady speed but also to **slow down for steep uphills**. This maneuver, seen as a sharp dip in the velocity profile, is a trade off to avoid violating the battery's maximum current limit, saving significant energy and preventing any damage to the battery for a minimal time penalty. The strategy also uses all available battery capacity, finishing the race precisely at the 3.0% SoC floor.