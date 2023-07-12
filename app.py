from flask import Flask, request, render_template
from statistics import mean
import googlemaps

app = Flask(__name__)
gmaps = googlemaps.Client(key='AIzaSyA2DuuGzGek-8JBvtt3W4yamRsAeudBvtM')

def convert_seconds_to_hms(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        fitness_center = 'LA Fitness'
        individual_locations = []
        individuals = request.form.getlist('individual')

        for individual in individuals:
            geocode_result = gmaps.geocode(individual)
            individual_location = geocode_result[0]['geometry']['location']
            individual_locations.append(individual_location)

        centroid_lat = mean([location['lat'] for location in individual_locations])
        centroid_lng = mean([location['lng'] for location in individual_locations])
        centroid = {'lat': centroid_lat, 'lng': centroid_lng}

        places_result = gmaps.places_nearby(location=centroid, keyword=fitness_center, radius=50000)
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
            location_scores.append((gym, score, individual_times))

        # Sort locations by score and select the top 5
        best_locations = sorted(location_scores, key=lambda x: x[1])[:5]

        return render_template('home.html', best_locations=best_locations)

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
