# ... Iteration 45/100 complete.
#      Current constraint violation: 0.000000
# Optimization terminated successfully    (Exit mode 0)
#             Current function value: 12534.54217216733
#             Iterations: 47
#             Function evaluations: 10367
#             Gradient evaluations: 47
# Optimization finished in 25.31 seconds.

# ================================================================================
# COMPREHENSIVE OPTIMIZATION ANALYSIS
# ================================================================================

# Optimization status: Optimization terminated successfully
# Final function value: 12534.54
# Iterations: 47
# Constraint violation: 0.000000

# Best solution found (violation: 0.000000):
#   Start hour: 10.38
#   Velocities: [ 96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  97.
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  96.3  96.3  96.3  96.3  96.3  79.1  49.1  19.1  49.1  69.8  96.3
#   96.3  86.7  96.3  96.3  96.3  96.3  96.3  96.3 101.7  98.5  97.7  98.5
#   96.3  96.3  96.3  97.   96.3  96.3  96.3  96.3  97.   96.3  96.3  97.7
#   96.3  96.3  96.3  96.3  96.3  97.   96.3  98.5  97.   97.7  97.7  97.
#   96.3  97.   97.   96.3  96.3  96.3  96.3  96.3  96.3  97.   96.3  96.3
#   96.3  99.2  96.3  96.3  96.3 100.   96.3  97.   96.3  96.3  96.3  97.7
#   97.   96.3  96.3  96.3  96.3  97.   96.3  96.3  96.3  96.3  96.3  96.3
#   96.3  97.   96.3  96.3  96.3  96.3  96.3  96.3 100.   96.3  96.3  95.2
#  100.9 109.6]

# DETAILED SIMULATION ANALYSIS:
#   Race time: 3.48 hours
#   Min SOC: 3.0% (limit: 3.0%)
#   Max SOC: 100.0% (limit: 102.0%)
#   Max battery current: 50.0A (limit: 50.0A)
#   Average velocity: 95.4 km/h

# ✅ --- Optimal Strategy Found ---
# Optimal Race Start Time: 10:23
# Minimized Race Time: 3.48 hours
# Total Solar Energy Generated: 4.56 kWh
# Total Electrical Energy Consumed: 7.47 kWh
# Final Battery Level: 3.0% (0.09 kWh)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import time
import requests

# ==============================================================================
# 1. SETUP: PARAMETERS AND INPUT DATA
# ==============================================================================

def get_vehicle_parameters():
    """Returns a dictionary of all vehicle and environmental constants."""
    return {
        # Vehicle Parameters (As per new requirements)
        "vehicle_mass": 330.0,
        "drag_area_CdA": 0.13,
        "coeff_rolling_resistance_Crr": 0.0045,
        "drivetrain_efficiency": 0.97,
        "regen_efficiency": 0.70, # ADDED: Efficiency of regenerative braking
        
        # Battery (As per new requirements)
        "battery_capacity_joules": 3 * 3.6e6, # 3 kWh
        "initial_SoC": 1.0,
        "min_SoC": 0.03,
        "max_SoC": 1.02, # ADDED: The battery cannot exceed 100% with a buffer
        "max_battery_current_a": 50.0,
        "battery_voltage_v": 120.0,

        # Solar Array (As per new requirements)
        "solar_panel_area": 5.85,
        "solar_panel_efficiency": 0.22,

        # Environmental
        "air_density": 1.225,
        "gravity": 9.81,
        
        # Acceleration limits for a smooth profile
        "max_acceleration_kph_per_chunk": 30.0,
        "max_deceleration_kph_per_chunk": 30.0,
    }

def get_synthetic_solar_irradiance(time_of_day_hours):
    """
    Calculates the solar irradiance (W/m^2) for a given time of day in south India in may/june using a sine wave.
    The optimizer will choose a start_hour to place the car's journey under the most powerful part of this curve, maximizing solar 
    energy gain. This is directly reflected in the "Environmental Conditions" graph where the orange irradiance curve peaks mid race.
    """

    # Sunrise/sunset times for Chennai in May/June are approx. 5:45 AM and 6:30 PM
    sunrise = 5.75  # 5:45 AM
    sunset = 18.5   # 6:30 PM
    
    # Peak solar irradiance in India on a clear day is around 1050 W/m^2
    peak_irradiance = 1050.0

    # Create a boolean mask for daylight hours
    daylight_hours = (time_of_day_hours >= sunrise) & (time_of_day_hours <= sunset)
    
    # Calculate the angle for the sinusoidal model based on daylight duration (sunrise to sunset) to a 0-pi range for the sine function.
    angle = np.pi * (time_of_day_hours - sunrise) / (sunset - sunrise)
    
    # Calculate irradiance, ensuring it's never negative
    sinusoidal_irradiance = peak_irradiance * np.sin(angle)
    sinusoidal_irradiance = np.maximum(0, sinusoidal_irradiance)
    
    # Apply the daylight mask
    irradiance = np.where(daylight_hours, sinusoidal_irradiance, 0.0)
    return irradiance


def load_route_data(filename='route_data_resampled.csv'):
    """Loads, cleans, and prepares the route data."""
    df = pd.read_csv(filename)
    
    # --- Clean the GPS Data by removing duplicates ---
    is_duplicate = (df['latitude'].diff() == 0) & (df['longitude'].diff() == 0)
    df_cleaned = df[~is_duplicate].reset_index(drop=True)
    print(f"Cleaned route data: Removed {len(df) - len(df_cleaned)} duplicate GPS points.")
    
    # --- ADDED: Smooth the altitude data to remove noise ---
    # GPS altitude data is often noisy (jumps up and down). A rolling average with a window of 5 creates a more realistic and smoother 
    # gradient profile. This prevents the model from calculating extreme, unrealistic power spikes.
    df_cleaned['altitude_m_smoothed'] = df_cleaned['altitude_m'].rolling(window=5, center=True, min_periods=1).mean()

    # All subsequent calculations use the cleaned and smoothed data
    distances_m = haversine_distance(df_cleaned['latitude'].iloc[:-1].values, 
                                     df_cleaned['longitude'].iloc[:-1].values, 
                                     df_cleaned['latitude'].iloc[1:].values, 
                                     df_cleaned['longitude'].iloc[1:].values)
    
    df_cleaned['segment_distance_m'] = np.insert(distances_m, 0, 0)
    
    # Use the new SMOOTHED altitude for gradient calculation
    altitudes_m = df_cleaned['altitude_m_smoothed'].to_numpy()
    altitude_changes_m = np.diff(altitudes_m)

    sin_theta = np.divide(altitude_changes_m, distances_m, 
                          out=np.zeros_like(distances_m), 
                          where=distances_m!=0)
    
    df_cleaned['gradient_sin_theta'] = np.insert(np.nan_to_num(sin_theta), 0, 0)
    df_cleaned['cumulative_distance_m'] = df_cleaned['segment_distance_m'].cumsum()
    
    return df_cleaned

def haversine_distance(lat1, lon1, lat2, lon2):
    """Helper function to calculate distance between GPS points."""
    R = 6371000  # Earth radius in meters
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    
    # --- THIS IS THE DEFINITIVE FIX ---
    # Clip 'a' to handle potential floating-point inaccuracies where a > 1. This prevents taking the square root of a negative number.
    a = np.clip(a, 0, 1)
    
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

# ==============================================================================
# 2. PHYSICS AND ENERGY SIMULATION MODEL
# ==============================================================================

def check_array(name, arr):
    """A helper function to print stats and check for invalid numbers in an array."""
    # Check for NaN or Inf values. This is the most important check.
    if np.isnan(arr).any() or np.isinf(arr).any():
        print(f"  !!!!!! FATAL WARNING: NaN or Inf detected in '{name}'! !!!!!!")
        # Print details about where the invalid values are
        nan_count = np.isnan(arr).sum()
        inf_count = np.isinf(arr).sum()
        print(f"  -> Contains {nan_count} NaN(s) and {inf_count} Inf(s).")
        return True # Return True to indicate an error was found
    
    # If the array is valid, print its basic stats
    print(f"  [OK] Checking {name}: min={np.min(arr):.2f}, max={np.max(arr):.2f}, mean={np.mean(arr):.2f}")
    return False

def run_race_simulation(velocities_kph, route_df, params, start_hour):
    """
    Simulates the race. Includes the final fix for the time-wrapping solar calculation.
    """
    velocities_mps = velocities_kph / 3.6
    
    # --- Forces and Power ---
    # These three lines calculate the primary resistive forces acting on the vehicle.
    # F_drag increases with the square of velocity, making it the dominant force at high speeds.
    # F_rolling is a constant force from the tires.
    # F_gradient is the force of gravity on hills (can be positive for uphill or negative for downhill).
    F_drag = 0.5 * params['air_density'] * params['drag_area_CdA'] * velocities_mps**2
    F_rolling = params['coeff_rolling_resistance_Crr'] * params['vehicle_mass'] * params['gravity']
    F_gradient = params['vehicle_mass'] * params['gravity'] * route_df['gradient_sin_theta'].values
    F_resistive = F_drag + F_rolling + F_gradient
    # --- THIS IS THE NEW REGEN LOGIC ---
    # The required tractive force can now be positive (propulsion) or negative (braking)
    # For this model, we assume the optimizer sets a speed, and we calculate the force needed.
    # We'll treat F_resistive as the force needed to overcome the environment.
    # For a steady speed, tractive force must equal resistive force.
    F_tractive = F_resistive

    # Mechanical power is force times velocity
    # Mechanical power is the power required at the wheels. It can be positive (propulsion) or negative (braking/coasting downhill).
    P_mech_watts = F_tractive * velocities_mps

    # Electrical power calculation depends on the direction of energy flow
    # Now, we calculate the electrical power drawn from or returned to the battery (direction of energy flow)
    # If P_mech is positive, we are propelling and lose energy to drivetrain inefficiency.
    # If P_mech is negative, we are regenerating energy, but we lose some to regen inefficiency.
    # The 'np.where' command is a fast way to apply this condition across the whole race.
    propulsion_power = P_mech_watts / params['drivetrain_efficiency']
    regen_power = P_mech_watts * params['regen_efficiency'] # Note: P_mech will be negative here
    P_elec_watts = np.where(P_mech_watts >= 0, propulsion_power, regen_power)
    
    # --- Battery Current ---
    # Current going out of the battery (discharging) is positive, into the battery (charging) is negative
    battery_current_a = P_elec_watts / params['battery_voltage_v']
    
    # --- Time and Energy Simulation---
    # Calculate the time spent in each tiny route segment. (We add a very small number (1e-9) to the denominator to prevent division by 
    # zero if velocity is 0)
    segment_distances = route_df['segment_distance_m'].values
    delta_t_s = segment_distances / (velocities_mps + 1e-9)
    total_time_s = np.sum(delta_t_s)
    
    # Creates a timestamp for every point in the race to calculate the correct solar power. (The modulo operator (%) handles races 
    # that might cross midnight)
    time_of_day_hours = start_hour + np.cumsum(delta_t_s) / 3600.0
    time_of_day_wrapped = time_of_day_hours % 24
    
    # Calculate the power generated by the solar panels at each point in time.
    P_solar_watts = get_synthetic_solar_irradiance(time_of_day_wrapped) * \
                    params['solar_panel_area'] * \
                    params['solar_panel_efficiency']
                    
    # The net power is the final energy balance for the battery. P_net = (Power in from solar or from regen) - (power out to motor)
    P_net_watts = P_solar_watts - P_elec_watts
    
    # Convert power (Joules/sec) to energy (Joules) for each segment by multiplying by time (delta_t_s).
    delta_energy_joules = P_net_watts * delta_t_s
    initial_energy = params['battery_capacity_joules'] * params['initial_SoC']

    # The State of Charge (SoC) at any point is the initial energy plus the cumulative sum of all energy changes up to that point. 
    # This generates the green line in the SoC graph.
    cumulative_energy_joules = initial_energy + np.cumsum(delta_energy_joules)
    soc_profile = cumulative_energy_joules / params['battery_capacity_joules']
    
    power_profile = {'solar_gen_W': P_solar_watts, 'elec_cons_W': P_elec_watts}
    
    return total_time_s, soc_profile, power_profile, battery_current_a, delta_t_s

# ==============================================================================
# 3. OPTIMIZATION SETUP
# ==============================================================================

# ==============================================================================
# ENHANCED DEBUGGING SYSTEM
# ==============================================================================

class AdvancedOptimizationCallback:
    """
    A comprehensive callback that tracks constraints and identifies exactly why optimization fails.
    """
    def __init__(self, max_iterations, constraint_func, constraint_args, bounds, params):
        self.iteration_count = 0
        self.max_iterations = max_iterations
        self.constraint_func = constraint_func
        self.constraint_args = constraint_args
        self.bounds = bounds
        self.params = params
        self.last_valid_x = None
        self.best_constraint_violation = float('inf')
        self.constraint_history = []
        
    def __call__(self, xk):
        """This method is called by the optimizer at each iteration."""
        self.iteration_count += 1
        
        # Check constraints and get detailed violation info
        constraint_violations, violation_details = self.analyze_constraints(xk)
        total_violation = np.sum(np.abs(constraint_violations[constraint_violations < 0]))
        
        # Store the best solution found so far
        if total_violation < self.best_constraint_violation:
            self.best_constraint_violation = total_violation
            self.last_valid_x = xk.copy()
            self.best_violation_details = violation_details
        
        if self.iteration_count % 5 == 0:
            print(f"  ... Iteration {self.iteration_count}/{self.max_iterations} complete.")
            print(f"     Current constraint violation: {total_violation:.6f}")
            
            # Print worst violations every 10 iterations
            if self.iteration_count % 10 == 0 and violation_details:
                worst_violation = violation_details[0]
                print(f"     Worst violation: {worst_violation['type']} - {worst_violation['value']:.4f}")

    def analyze_constraints(self, xk):
        """Analyze exactly which constraints are violated and why."""
        constraints = self.constraint_func(xk, *self.constraint_args)
        violation_details = []
        
        # Analyze SOC constraints
        soc_constraints = constraints[:len(constraints)//3]  # First third are SOC constraints
        min_soc_violations = soc_constraints[soc_constraints < 0]
        if len(min_soc_violations) > 0:
            worst_violation = np.min(min_soc_violations)
            violation_details.append({
                'type': 'Minimum SOC Violation',
                'value': worst_violation,
                'message': f"Battery drops to {self.params['min_SoC'] + worst_violation:.3f} (limit: {self.params['min_SoC']})"
            })
        
        # Analyze Max SOC constraints  
        max_soc_constraints = constraints[len(constraints)//3:2*len(constraints)//3]
        max_soc_violations = max_soc_constraints[max_soc_constraints < 0]
        if len(max_soc_violations) > 0:
            worst_violation = np.min(max_soc_violations)
            violation_details.append({
                'type': 'Maximum SOC Violation', 
                'value': worst_violation,
                'message': f"Battery exceeds {self.params['max_SoC'] - worst_violation:.3f} (limit: {self.params['max_SoC']})"
            })
        
        # Analyze current constraints
        current_constraints = constraints[2*len(constraints)//3:]
        current_violations = current_constraints[current_constraints < 0]
        if len(current_violations) > 0:
            worst_violation = np.min(current_violations)
            violation_details.append({
                'type': 'Battery Current Violation',
                'value': worst_violation, 
                'message': f"Current exceeds {self.params['max_battery_current_a'] - worst_violation:.1f}A (limit: {self.params['max_battery_current_a']}A)"
            })
        
        # Sort by worst violation
        violation_details.sort(key=lambda x: x['value'])
        
        return constraints, violation_details

    def print_final_diagnostic(self, result):
        """Print comprehensive diagnostic information when optimization fails."""
        print("\n" + "="*80)
        print("COMPREHENSIVE OPTIMIZATION FAILURE ANALYSIS")
        print("="*80)
        
        print(f"\nOptimization status: {result.message}")
        print(f"Final function value: {result.fun:.2f}")
        print(f"Iterations: {result.nit}")
        print(f"Constraint violation: {self.best_constraint_violation:.6f}")
        
        if self.last_valid_x is not None:
            print(f"\nBest solution found (violation: {self.best_constraint_violation:.6f}):")
            print(f"  Start hour: {self.last_valid_x[0]:.2f}")
            print(f"  Velocities: {self.last_valid_x[1:].round(1)}")
            
            if hasattr(self, 'best_violation_details') and self.best_violation_details:
                print(f"\nCONSTRAINT VIOLATIONS IN BEST SOLUTION:")
                for i, violation in enumerate(self.best_violation_details[:3]):  # Top 3 violations
                    print(f"  {i+1}. {violation['type']}: {violation['message']}")
            
            # Run simulation on best solution to get detailed diagnostics
            self.detailed_simulation_analysis(self.last_valid_x)
        else:
            print("\n❌ NO VALID SOLUTION FOUND - Constraints too strict or initial guess infeasible")
            self.analyze_initial_feasibility()
    
    def detailed_simulation_analysis(self, xk):
        """Run simulation on the solution and analyze why constraints are violated."""
        start_hour = xk[0]
        chunk_velocities = xk[1:]
        route_df, params, chunk_size_m = self.constraint_args
        
        velocities_kph = map_chunk_velocities_to_segments(chunk_velocities, route_df, chunk_size_m)
        total_time_s, soc_profile, power_profile, battery_current, delta_t_s = run_race_simulation(
            velocities_kph, route_df, params, start_hour
        )
        
        print(f"\nDETAILED SIMULATION ANALYSIS:")
        print(f"  Race time: {total_time_s/3600:.2f} hours")
        print(f"  Min SOC: {np.min(soc_profile)*100:.1f}% (limit: {params['min_SoC']*100}%)")
        print(f"  Max SOC: {np.max(soc_profile)*100:.1f}% (limit: {params['max_SoC']*100}%)") 
        print(f"  Max battery current: {np.max(battery_current):.1f}A (limit: {params['max_battery_current_a']}A)")
        print(f"  Average velocity: {np.mean(velocities_kph):.1f} km/h")
        
        # Identify exactly where violations occur
        if np.min(soc_profile) < params['min_SoC']:
            min_idx = np.argmin(soc_profile)
            print(f"  ❌ SOC violation at segment {min_idx}, distance: {route_df['cumulative_distance_m'].iloc[min_idx]/1000:.1f}km")
        
        if np.max(soc_profile) > params['max_SoC']:
            max_idx = np.argmax(soc_profile) 
            print(f"  ❌ SOC overcharge at segment {max_idx}, distance: {route_df['cumulative_distance_m'].iloc[max_idx]/1000:.1f}km")
            
        if np.max(battery_current) > params['max_battery_current_a']:
            current_idx = np.argmax(battery_current)
            print(f"  ❌ Current violation at segment {current_idx}, distance: {route_df['cumulative_distance_m'].iloc[current_idx]/1000:.1f}km")
    
    def analyze_initial_feasibility(self):
        """Check if the initial guess and bounds are feasible."""
        print(f"\nINITIAL FEASIBILITY ANALYSIS:")
        
        # Check bounds
        print(f"  Start hour bounds: {self.bounds[0]}")
        print(f"  Velocity bounds: {self.bounds[1][0]} to {self.bounds[-1][1]} km/h")
        
        # Check if constraints are physically possible
        route_df, params, chunk_size_m = self.constraint_args
        total_distance = route_df['cumulative_distance_m'].iloc[-1]
        min_energy_required = total_distance * params['vehicle_mass'] * params['gravity'] * params['coeff_rolling_resistance_Crr'] / params['drivetrain_efficiency']
        battery_capacity_joules = params['battery_capacity_joules'] * (params['initial_SoC'] - params['min_SoC'])
        
        print(f"  Total distance: {total_distance/1000:.1f} km")
        print(f"  Minimum energy required: {min_energy_required/3.6e6:.2f} kWh")
        print(f"  Usable battery capacity: {battery_capacity_joules/3.6e6:.2f} kWh")
        
        if min_energy_required > battery_capacity_joules:
            print("  ❌ PHYSICAL IMPOSSIBILITY: Required energy exceeds battery capacity!")
            print("     Solution: Increase battery capacity or reduce distance/rolling resistance")


def map_chunk_velocities_to_segments(chunk_velocities, route_df, chunk_size_m):
    """
    Translates the optimizer's simple strategy into a detailed race profile.
    The optimizer works with a small number of "chunk_velocities" (e.g., ~100) for speed. This function maps each of those 
    velocities to the many thousands of high-resolution segments in the route data. For example, it sets the velocity for all segments
    between 0m and 1500m to the first chunk_velocity, and so on. This is why the blue 'Velocity Profile' in the graph looks like a 
    series of flat steps.
    """
    # Get the cumulative distance for each high-resolution segment
    cumulative_dist = route_df['cumulative_distance_m'].values
    
    # Determine which chunk each segment belongs to by its distance
    segment_chunk_indices = np.floor(cumulative_dist / chunk_size_m).astype(int)
    segment_chunk_indices = np.clip(segment_chunk_indices, 0, len(chunk_velocities) - 1)
    
    # Use the indices to create the full-length velocity profile from the chunk velocities
    full_velocity_profile = chunk_velocities[segment_chunk_indices]
    
    # NEW: Create smooth acceleration from 0 km/h over the first 100 meters
    acceleration_zone = cumulative_dist <= 100.0  # First 100 meters
    if np.any(acceleration_zone):
        # Get the target velocity after acceleration zone
        target_velocity = full_velocity_profile[~acceleration_zone][0] if len(full_velocity_profile[~acceleration_zone]) > 0 else full_velocity_profile[-1]
        
        # Create linear acceleration from 0 to target velocity
        dist_in_zone = cumulative_dist[acceleration_zone]
        max_dist_in_zone = np.max(dist_in_zone)
        if max_dist_in_zone > 0:
            acceleration_factor = dist_in_zone / max_dist_in_zone
            full_velocity_profile[acceleration_zone] = acceleration_factor * target_velocity
    
    return full_velocity_profile

def objective_function(decision_vars, route_df, params, chunk_size_m): # No interpolator
    """
    This is the function the optimizer tries to minimise. It has one simple goal: run the simulation with a given set of decision
    variables (start time and velocities) and return the total race time. The optimizer's entire job is to find the input "decision_vars" 
    that results in the smallest possible return value from this function.
    """

    start_hour = decision_vars[0]
    chunk_velocities = decision_vars[1:]
    velocities_kph = map_chunk_velocities_to_segments(chunk_velocities, route_df, chunk_size_m)
    total_time_s, _, _, _, _ = run_race_simulation(
        velocities_kph, route_df, params, start_hour
    )
    return total_time_s

# ==============================================================================
# IMPROVED CONSTRAINT FUNCTION WITH BETTER DEBUGGING
# ==============================================================================

def constraint_function(decision_vars, route_df, params, chunk_size_m):
    """
    The constraint function with better error handling and validation.
    """
    try:
        start_hour = decision_vars[0]
        chunk_velocities = decision_vars[1:]
        
        # Validate inputs
        if start_hour < 0 or start_hour > 24:
            raise ValueError(f"Invalid start hour: {start_hour}")
        
        if np.any(chunk_velocities < 0):
            raise ValueError("Negative velocities detected")
        
        velocities_kph = map_chunk_velocities_to_segments(chunk_velocities, route_df, chunk_size_m)
        
        _, soc_profile, _, battery_current_profile, _ = run_race_simulation(
            velocities_kph, route_df, params, start_hour
        )
        
        # The SciPy optimizer requires constraints to be in the form 'g(x) >= 0'. A positive result means the constraint is satisfied, 
        # a negative result means the constraint is violated

        # Constraint 1: SoC must be ABOVE the minimum. (SoC - min_SoC >= 0)
        # This prevents the battery from draining too much. In the graph, the optimizer drives the SoC right down to this limit to use 
        # all available energy, finishing with the SoC at exactly 3.0%.
        c1_min_soc = soc_profile - params['min_SoC']
        
        # Constraint 2: SoC must be BELOW the maximum. (max_SoC - SoC >= 0)
        # This prevents overcharging the battery from solar and regenerative braking.  
        c2_max_soc = params['max_SoC'] - soc_profile
        
        # Constraint 3: Battery current must be below the maximum. (max_current - current >= 0)
        # This protects the battery hardware. It forces the optimizer to slow the car down on steep hills where the power demand would 
        # otherwise cause a huge current draw. This is the reason for the big velocity dip at ~192km in the graph, which
        # corresponds to the steepest hill as shown in the gradient, in the 'Environmental Conditions' plot.
        c3_battery_current = params['max_battery_current_a'] - battery_current_profile
        
        return np.hstack([c1_min_soc, c2_max_soc, c3_battery_current])
        
    except Exception as e:
        print(f"❌ Constraint function error: {e}")
        # Return a large violation to guide optimizer away from problematic regions
        return np.array([-1000.0])
    
def acceleration_constraint(decision_vars, params):
    """
    Ensures the velocity profile is physically realistic. This constraint prevents the optimizer from choosing impossible speed changes,
    like jumping from 20 km/h to 120 km/h between two adjacent 1.5km chunks. It makes the final velocity profile smoother and more driveable.
    """
    # Unpack only the chunk velocities, ignoring the start time
    chunk_velocities = decision_vars[1:]
    
    # Calculate the difference between each adjacent velocity chunk
    velocity_changes = np.diff(chunk_velocities) # e.g., [v2-v1, v3-v2, ...]
    
    # Constraint 1: Acceleration limit (must be >= 0)
    # max_accel - (v_next - v_prev) >= 0
    c_accel = params['max_acceleration_kph_per_chunk'] - velocity_changes
    
    # Constraint 2: Deceleration limit (must be >= 0)
    # (v_next - v_prev) - (-max_decel) >= 0  -->  v_change + max_decel >= 0
    c_decel = velocity_changes + params['max_deceleration_kph_per_chunk']
    
    # Stack both constraint arrays into one. The optimizer will check them all.
    return np.hstack([c_accel, c_decel])

# ==============================================================================
# 4. MAIN EXECUTION BLOCK
# ==============================================================================

if __name__ == '__main__':
    # --- Load Inputs ---
    vehicle_params = get_vehicle_parameters()
    route_data = load_route_data()
    
    # --- Define Optimization Problem ---
    # The CHUNK_SIZE_M is a critical trade-off.
    # Smaller chunks -> more decision variables -> higher precision strategy, but much slower optimization and more jumpy velocity graphs.
    # Larger chunks -> fewer variables -> faster optimization, a less jumpy velocity graph, but a less detailed/optimal strategy.
    # 1500m is a reasonable balance. I did quite a lot of trials, checked a lot of graphs. lower than 1500 is causing very minimal 
    # benefits in time optimisation (the lowest it got was at 200 chunks, around 3.45 hours but the velocity profile was really jumpy and 
    # isn't feasible to do every 200 metres). I tried to implement acceleration constraints (not by prevening excessive speed differences 
    # between chunks, but by actually calculating acceleration and preventing it from exceeding 0.2, however my laptop's charger 
    # stopped working and I only have a 2 hour battery life left to complete these comments asap)
    CHUNK_SIZE_M = 1500
    num_chunks = int(np.ceil(route_data['cumulative_distance_m'].iloc[-1] / CHUNK_SIZE_M))
    
    print("--- AgniRath Race Strategy Optimization ---")
    print(f"Route distance: {route_data['cumulative_distance_m'].iloc[-1] / 1000:.1f} km")
    print(f"Optimizing {num_chunks} velocity chunks + 1 start time variable.")
    
    # Better initial guess - start slower and ramp up
    initial_start_hour = 9.0
    initial_velocities = np.linspace(20.0, 60.0, num_chunks)  # Gradual increase
    initial_guess = np.insert(initial_velocities, 0, initial_start_hour)
    
    start_hour_bounds = (8.0, 12.0)
    velocity_bounds = [(0.0, 130.0) for _ in range(num_chunks)]  # Allow starting at 0
    bounds = [start_hour_bounds] + velocity_bounds
    
    args_tuple = (route_data, vehicle_params, CHUNK_SIZE_M)
    soc_constraint_def = {'type': 'ineq', 'fun': constraint_function, 'args': args_tuple}
    accel_constraint_def = {'type': 'ineq', 'fun': acceleration_constraint, 'args': (vehicle_params,)}
    
    # --- Setup the ADVANCED Progress Callback ---
    MAX_ITER = 100
    progress_callback = AdvancedOptimizationCallback(
        max_iterations=MAX_ITER,
        constraint_func=constraint_function,
        constraint_args=args_tuple,
        bounds=bounds,
        params=vehicle_params
    )
    
    # --- Run the Optimizer ---
    print("\nStarting optimization with enhanced debugging...")
    start_time = time.time()
    
    try:

        # The optimizer (SLSQP - sequential least squares programming) is well suited for problems with both bounds (like 0-130 km/h) 
        # and complex, non linear constraints (like our SoC and current limits).
        # The core process is a loop:
        # 1. It starts with an initial guess for the race strategy ("initial_guess").
        # 2. At each step, it analyzes the current strategy to find the most promising direction for improvement (the "gradient").
        #    It uses this information to build a temporary, simplified mathematical model of the complex physics.
        # 3. It then proposes an updated, slightly faster strategy by finding the optimal solution to that simplified model.
        # 4. Most importantly, it checks this new strategy against our defined constraints (hard physical rules of the race): 
        #    did the battery SoC drop too low, or did the motor current get too high, etc?
        # 5. If a limit is hit, it adjusts the strategy to that limit, extracting the maximum possible performance without 
        #    breaking the rule.
        
        # This cycle repeats until it finds the optimal balance (a point where going any faster is physically impossible according to the 
        # rules we've set), which yields the final, optimal strategy.

        # Why SLSQP is the right choice for this problem:
        # 1. The physics and constraints are non-linear (like drag is related to square of velocity, solar input is a sine wave, etc). 
        #    Simpler methods like linear programming would fail because they require all relationships to be straight lines, 
        #    which isn't true here. The power needed to overcome drag is even more non linear, scaling with the cube of velocity 
        #    (P ~ v^3), making this problem impossible for linear solvers.
        # 2. Following constraints is of utmost importance. The race isn't about going as fast as possible; it's about going as fast 
        #    as possible without running out of battery or damaging the motor or breaking any of the other hard constraints. 
        #    SLSQP is specifically designed to handle these types of complex, non linear constraints, unlike simpler algorithms 
        #    like basic gradient descent, which is "blind" to constraints. An unconstrained algorithm would happily advise a strategy 
        #    that drains the battery to -20% or goes above the max discharg current, as it only seeks to minimize time, regardless of 
        #    physical reality.
        # 3. Efficiency is very important, the optimizer has to adjust over 200 variables (one start time + many velocity chunks) while 
        #    following all the constraints. A global search method like a genetic algorithm would also work but would be extremely slow, 
        #    trying thousands of random combinations. SLSQP is much more efficient because it uses calculus (gradients) to make informed
        #    steps toward the best solution instead of guessing randomly or doing a grid search. Infact, a grid search is computationally 
        #    impossible; even testing 10 speeds for each of our 200 chunks would mean 10^200 combinations. 
        # 4. It's a local optimizer (it finds the local minimum closest to its starting point), which is the right trade off. It's not 
        #    guaranteed to find the absolute best solution on the entire map (the global optimum). Global optimizers like
        #    genetic algorithms are better at this, but are far, far slower. For this problem, the "solution landscape" 
        #    (a map linking every possible strategy to its final race time) is likely smooth enough that the first valley found 
        #    is the best one (smooth means a small change in the strategy (like increasing one velocity chunk by 1 km/h) 
        #    leads to a small, predictable change in the race time), making SLSQP's speed and efficiency the winning choice.

        result = minimize(
            objective_function,
            initial_guess,
            args=args_tuple,
            method='SLSQP',
            bounds=bounds,
            constraints=[soc_constraint_def, accel_constraint_def],
            callback=progress_callback,
            options={'disp': True, 'maxiter': MAX_ITER, 'ftol': 1e-7}
        )
        
    except Exception as e:
        print(f"❌ Optimization crashed: {e}")
        result = None
    
    end_time = time.time()
    print(f"Optimization finished in {end_time - start_time:.2f} seconds.")
    
    # --- COMPREHENSIVE RESULTS ANALYSIS ---
    if result is not None:
        progress_callback.print_final_diagnostic(result)
        
        solution_x = None
        if result.success:
            print("\n✅ --- Optimal Strategy Found ---")
            solution_x = result.x
        elif progress_callback.last_valid_x is not None:
            print("\n⚠️ --- Optimization Timed Out: Using Best Intermediate Solution Found ---")
            solution_x = progress_callback.last_valid_x
        else:
            print("\n❌ Optimization failed and no valid intermediate solution was found.")
            # Try a fallback: simple constant velocity strategy
            print("Attempting fallback strategy...")
            fallback_velocity = 40.0  # Conservative fallback
            fallback_guess = np.insert(np.full(num_chunks, fallback_velocity), 0, 10.0)
            fallback_constraints = constraint_function(fallback_guess, *args_tuple)
            
            if np.all(fallback_constraints >= 0):
                print("✅ Fallback strategy is feasible, using it.")
                solution_x = fallback_guess
            else:
                print("❌ Fallback strategy also violates constraints.")
                print("Please relax your constraints (increase min_SoC or max_current).")
        
        if solution_x is not None:





            optimal_start_hour = solution_x[0]
            optimal_chunk_velocities = solution_x[1:]
            
            optimal_velocities_kph = map_chunk_velocities_to_segments(
                optimal_chunk_velocities, route_data, CHUNK_SIZE_M
            )
            
            final_time_s, final_soc, final_power, final_battery_current, final_delta_t_s = run_race_simulation(
                optimal_velocities_kph, route_data, vehicle_params, optimal_start_hour
            )
            
            final_time_hr = final_time_s / 3600.0
            print(f"Optimal Race Start Time: {int(optimal_start_hour)}:{int((optimal_start_hour % 1) * 60):02d}")
            print(f"Minimized Race Time: {final_time_hr:.2f} hours")
            
            total_solar_energy_generated_J = np.sum(final_power['solar_gen_W'] * final_delta_t_s)
            total_electrical_energy_consumed_J = np.sum(final_power['elec_cons_W'] * final_delta_t_s)
            final_battery_energy_J = final_soc[-1] * vehicle_params['battery_capacity_joules']

            print(f"Total Solar Energy Generated: {total_solar_energy_generated_J / 3.6e6:.2f} kWh")
            print(f"Total Electrical Energy Consumed: {total_electrical_energy_consumed_J / 3.6e6:.2f} kWh")
            print(f"Final Battery Level: {final_soc[-1]*100:.1f}% ({final_battery_energy_J / 3.6e6:.2f} kWh)")
            
            # --- ENHANCED VISUALIZATION ---
            # This final block of code is dedicated to plotting the results. Each subplot visualizes a key aspect of the optimal 
            # strategy found by the optimizer, allowing us to understand the relationship between speed, terrain, solar power, 
            # and battery usage. This is what generates the 4 panel graph I provided.
            distance_km = route_data['cumulative_distance_m'] / 1000.0
            
            plt.style.use('seaborn-v0_8-darkgrid')
            # CHANGED: Switched to a 2x2 grid for better layout
            fig, ax = plt.subplots(2, 2, figsize=(18, 10), sharex=True)
            fig.suptitle('Optimal Race Strategy Analysis', fontsize=16)
            
            # 1. Velocity Profile
            ax[0, 0].plot(distance_km, optimal_velocities_kph, label='Optimal Velocity', color='dodgerblue')
            ax[0, 0].set_ylabel('Velocity (km/h)')
            ax[0, 0].set_title('Velocity Profile')
            ax[0, 0].legend()
            
            # 2. State of Charge (SoC)
            ax[1, 0].plot(distance_km, final_soc * 100, label='Battery SoC', color='limegreen')
            ax[1, 0].set_ylabel('State of Charge (%)')
            ax[1, 0].set_title('Battery State of Charge')
            ax[1, 0].axhline(y=vehicle_params['min_SoC']*100, color='r', linestyle='--', label=f"{vehicle_params['min_SoC']*100}% Limit")
            ax[1, 0].set_xlabel('Distance (km)')
            ax[1, 0].legend()
            
            # 3. Power Balance
            ax[0, 1].plot(distance_km, final_power['solar_gen_W'] / 1000, label='Solar Power Generated', color='gold')
            ax[0, 1].plot(distance_km, final_power['elec_cons_W'] / 1000, label='Electrical Power Consumed', color='salmon', alpha=0.8)
            ax[0, 1].set_ylabel('Power (kW)')
            ax[0, 1].set_title('Power Balance')
            ax[0, 1].legend()

            # 4. ADDED: Environmental Conditions
            gradient_degrees = np.rad2deg(np.arcsin(route_data['gradient_sin_theta']))
            irradiance_w_m2 = final_power['solar_gen_W'] / (vehicle_params['solar_panel_area'] * vehicle_params['solar_panel_efficiency'])

            ax_env = ax[1, 1]
            ax_solar = ax_env.twinx() # Create a second y-axis

            ax_env.plot(distance_km, gradient_degrees, label='Road Gradient', color='grey', alpha=0.9)
            ax_env.set_ylabel('Gradient (Degrees)', color='grey')
            ax_env.tick_params(axis='y', labelcolor='grey')
            ax_env.set_title('Environmental Conditions')
            ax_env.set_xlabel('Distance (km)')

            ax_solar.plot(distance_km, irradiance_w_m2, label='Solar Irradiance', color='orange', linestyle='--')
            ax_solar.set_ylabel('Irradiance (W/m²)', color='orange')
            ax_solar.tick_params(axis='y', labelcolor='orange')

            # To get legends from both axes to show up
            lines, labels = ax_env.get_legend_handles_labels()
            lines2, labels2 = ax_solar.get_legend_handles_labels()
            ax_solar.legend(lines + lines2, labels + labels2, loc=0)
            
            plt.tight_layout(rect=(0, 0, 1, 0.96))
            plt.show()
