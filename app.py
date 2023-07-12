from flask import Flask, request, render_template
from statistics import mean
import googlemaps
from geopy.distance import geodesic

app = Flask(__name__)

def calculate_distance(point1, point2):
    return geodesic((point1['lat'], point1['lng']), (point2['lat'], point2['lng'])).meters

def convert_seconds_to_hms(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        apikey = request.form.get('apikey')
        fitness_center = request.form.get('place')
        individual_locations = []
        individuals = request.form.getlist('individual')

        gmaps = googlemaps.Client(key=apikey)

        for individual in individuals:
            geocode_result = gmaps.geocode(individual)
            individual_location = geocode_result[0]['geometry']['location']
            individual_locations.append(individual_location)

        centroid_lat = mean([location['lat'] for location in individual_locations])
        centroid_lng = mean([location['lng'] for location in individual_locations])
        centroid = {'lat': centroid_lat, 'lng': centroid_lng}

        max_distance = max(calculate_distance(loc1, loc2) for loc1 in individual_locations for loc2 in individual_locations)

        places_result = gmaps.places_nearby(location=centroid, keyword=fitness_center, radius=max_distance)
        fitness_locations = [(place['vicinity'], place['geometry']['location']) for place in places_result['results']]

        location_scores = []
        for gym, gym_location in fitness_locations:
            individual_times = {}
            times = []
            for individual, individual_location in zip(individuals, individual_locations):
                result = gmaps.distance_matrix(origins=individual_location, destinations=[gym_location], mode='driving')
                time = result['rows'][0]['elements'][0]['duration']['value']
                times.append(time)
                individual_times[individual] = convert_seconds_to_hms(time)

            total_time = sum(times)
            max_time = max(times)
            score = total_time * 0.7 + max_time * 0.3  # weight total driving time more than maximum individual driving time
            location_scores.append((gym, int(score), individual_times))

        # Sort locations by score and select the top 5
        best_locations = sorted(location_scores, key=lambda x: x[1])[:5]

        return render_template('home.html', best_locations=best_locations)

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
