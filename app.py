from flask import Flask, request, render_template
from statistics import mean
import googlemaps
from geopy.distance import geodesic
import itertools

app = Flask(__name__)

def calculate_distance(point1, point2):
    return geodesic((point1['lat'], point1['lng']), (point2['lat'], point2['lng'])).meters

def convert_seconds_to_hms(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def get_individual_locations(gmaps, individuals):
    individual_locations = []
    for individual in individuals:
        geocode_result = gmaps.geocode(individual)
        individual_location = geocode_result[0]['geometry']['location']
        individual_locations.append(individual_location)
    return individual_locations

def calculate_max_distance(individual_locations):
    pairwise_locations = itertools.combinations(individual_locations, 2)
    return max(calculate_distance(loc1, loc2) for loc1, loc2 in pairwise_locations)

def get_location_scores(gmaps, individuals, individual_locations, chain_locations, avoid_tolls, avoid_highways):
    location_scores = []
    for chain, chain_location in chain_locations:
        individual_times = {}
        times = []
        for individual, individual_location in zip(individuals, individual_locations):
            result = gmaps.distance_matrix(origins=individual_location, destinations=[chain_location], mode='driving', avoid=get_avoid_string(avoid_tolls, avoid_highways))
            time = result['rows'][0]['elements'][0]['duration']['value']
            times.append(time)
            individual_times[individual] = convert_seconds_to_hms(time)
        
        total_time = sum(times)
        max_time = max(times)
        score = total_time * 0.75 + max_time * 0.25  
        location_scores.append((chain, int(score), individual_times))

    return location_scores

def get_avoid_string(avoid_tolls, avoid_highways):
    avoid_list = []
    if avoid_tolls:
        avoid_list.append("tolls")
    if avoid_highways:
        avoid_list.append("highways")
    return '|'.join(avoid_list)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        apikey = request.form.get('apikey')
        central_location = request.form.get('place')
        individuals = request.form.getlist('individual')
        avoid_tolls = bool(request.form.get('toll'))
        avoid_highways = bool(request.form.get('highway'))

        gmaps = googlemaps.Client(key=apikey)
        individual_locations = get_individual_locations(gmaps, individuals)

        centroid_lat = mean([location['lat'] for location in individual_locations])
        centroid_lng = mean([location['lng'] for location in individual_locations])
        centroid = {'lat': centroid_lat, 'lng': centroid_lng}

        max_distance = calculate_max_distance(individual_locations)
        max_distance = min(max_distance, 50000)

        places_result = gmaps.places_nearby(location=centroid, keyword=central_location, radius=max_distance)
        chain_locations = [(place['vicinity'], place['geometry']['location']) for place in places_result['results']]

        location_scores = get_location_scores(gmaps, individuals, individual_locations, chain_locations, avoid_tolls, avoid_highways)

        best_locations = sorted(location_scores, key=lambda x: x[1])

        return render_template('home.html', best_locations=best_locations)

    return render_template('home.html')

@app.route('/help', methods=['GET'])
def help():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True)
