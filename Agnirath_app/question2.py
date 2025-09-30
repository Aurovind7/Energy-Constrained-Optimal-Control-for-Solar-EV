import requests
import pandas as pd
import math

# --- CONFIGURATION ---
# Replace with your actual OpenRouteService API key
ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImY5ZTdhMDU1ZmY3MTQ3Y2FiNGY3MzZkYmQ3MTNhMzhhIiwiaCI6Im11cm11cjY0In0='
# Coordinates for Chennai (start) and Bangalore (end)
START_COORDS = [80.2707, 13.0827]  # [longitude, latitude]
END_COORDS = [77.5946, 12.9716]    # [longitude, latitude]



def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the earth.
    Returns the distance in meters.
    """
    R = 6371000  # Radius of Earth in meters
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def resample_route(points, interval_m=100.0):
    """
    Resamples a list of GPS points to a fixed distance interval. The route data from an API can have inconsistent spacing (Eg: long distances on
    a straight highway, short distances on curvy roads). For our physics simulation to be accurate and consistent, we need data points at regular
    intervals. This function uses linear interpolation to create a new set of points, for example, every 100 meters along the original path.
    """
    resampled_points = [points[0]]
    distance_carried_over = 0.0
    for i in range(1, len(points)):
        prev_point = points[i-1]
        curr_point = points[i]
        segment_distance = haversine_distance(prev_point[0], prev_point[1], curr_point[0], curr_point[1])
        total_distance_this_segment = distance_carried_over + segment_distance

        # A single original segment might be much longer than our desired interval (Eg: a 500m straight road, but we want points every 100m).
        # This 'while' loop will place as many new points as needed inside this one segment.
        while total_distance_this_segment >= interval_m:
            # Calculate how far we need to travel along the current segment to reach the next interval point.
            distance_needed = interval_m - distance_carried_over
            # Determine the fraction (ratio) of the way along the current segment where the new point lies.
            ratio = distance_needed / segment_distance

            # --- Linear Interpolation ---
            # Create the new point's coordinates by moving along the line between the previous and current point by the calculated ratio.
            new_lat = prev_point[0] + ratio * (curr_point[0] - prev_point[0])
            new_lon = prev_point[1] + ratio * (curr_point[1] - prev_point[1])
            new_point = [new_lat, new_lon]
            resampled_points.append(new_point)

            # Now, our "previous" point for the next iteration becomes the new point we just created.
            prev_point = new_point
            # Recalculate the remaining distance in the segment.
            segment_distance = haversine_distance(prev_point[0], prev_point[1], curr_point[0], curr_point[1])
            # Reset the carried over distance because we just completed a full interval.
            distance_carried_over = 0.0
            total_distance_this_segment = segment_distance

        # After the loop, the remaining distance is carried over to the next segment from the original route.
        distance_carried_over = total_distance_this_segment
    return resampled_points




# --- STEP 1: Get Route Geometry ---
print("Step 1: Fetching route geometry from OpenRouteService...")

# We change the endpoint to explicitly request GeoJSON format
route_url = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson'

# The body now only needs the coordinates
body = {
    "coordinates": [START_COORDS, END_COORDS]
}
headers = {
    'Authorization': ORS_API_KEY,
    'Content-Type': 'application/json'
}

response = requests.post(route_url, json=body, headers=headers)
response.raise_for_status()
data = response.json()

# The path to the coordinates is different in the GeoJSON format
route_geometry = data['features'][0]['geometry']['coordinates']
print(f"Successfully fetched {len(route_geometry)} points for the route.")

# The API returns points in [longitude, latitude] format.
# Our internal convention and the haversine function use [latitude, longitude].
# This line swaps the order for every point to match our convention.
route_points_lat_lon = [[point[1], point[0]] for point in route_geometry]




print("\nStep 1.5: Resampling route to a 100m interval...")
resampled_route_lat_lon = resample_route(route_points_lat_lon, 100)
print(f"Resampled route to {len(resampled_route_lat_lon)} points.")



# --- STEP 2: Get Elevation Data (with Batching) ---
print("\nStep 2: Fetching elevation data for resampled points in batches...")
elevation_url = 'https://api.openrouteservice.org/elevation/line'

# Create the [lon, lat] list needed for the API
resampled_route_lon_lat_for_api = [[point[1], point[0]] for point in resampled_route_lat_lon]

elevations = []
batch_size = 500  # Set a batch size well within the API limits

# --- API Batching Logic ---
# The elevation API has a limit on how many points it can process in a single request. To get elevation for our thousands of resampled points, 
# we must break the request into smaller "batches" and send them one by one. This loop iterates through the master list of points in 
# chunks of "batch_size".

# Loop through the points in chunks of 'batch_size'
for i in range(0, len(resampled_route_lon_lat_for_api), batch_size):
    # Get the current batch of points
    batch = resampled_route_lon_lat_for_api[i:i + batch_size]

    # Format the request body for this batch
    body = {
        "format_in": "geojson",
        "geometry": {
            "coordinates": batch,
            "type": "LineString"
        }
    }

    print(f"  - Fetching batch {i//batch_size + 1}...")
    response = requests.post(elevation_url, json=body, headers=headers)
    response.raise_for_status()
    elevation_data = response.json()

    # Extract the elevation from each point in the response and add to our master list
    batch_elevations = [point[2] for point in elevation_data['geometry']['coordinates']]
    elevations.extend(batch_elevations)

print(f"Successfully fetched {len(elevations)} elevation points in total.")




def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculates the initial bearing between two points in degrees."""
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dLon = lon2_rad - lon1_rad
    y = math.sin(dLon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dLon)
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = (math.degrees(bearing_rad) + 360) % 360
    return bearing_deg

# --- STEP 3: Calculate Bearings ---
print("\nStep 3: Calculating bearing for each road segment...")
bearings = []
for i in range(len(resampled_route_lat_lon) - 1):
    lat1, lon1 = resampled_route_lat_lon[i]
    lat2, lon2 = resampled_route_lat_lon[i+1]
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    bearings.append(bearing)

# A bearing is calculated between two points (a start and an end). The very last point in our route has no "next" point, so we can't calculate 
# its bearing. A reasonable assumption is that the car continues in the same direction as the previous segment, so we just duplicate the last 
# calculated bearing.
bearings.append(bearings[-1])
print("Successfully calculated bearings.")




# --- STEP 4: Combine and Save to CSV ---
print("\nStep 4: Combining data and saving to route_data.csv...")

# This is the final assembly step. We combine all the processed data streams (coordinates, altitude, bearing) into a single, structured 
# pandas DataFrame. This CSV file is the input for our main race optimization script (question3.py). Each row represents a consistent step 
# along the race track.

df = pd.DataFrame({
    'latitude': [p[0] for p in resampled_route_lat_lon],
    'longitude': [p[1] for p in resampled_route_lat_lon],
    'altitude_m': elevations,
    'bearing_deg': bearings
})

# Save the DataFrame to a CSV file
df.to_csv('route_data_resampled.csv', index=False)
print("All done! Data saved to route_data_resampled.csv.")
print("\nData Preview:")
print(df.head())