from flask import Flask, request, render_template
from statistics import mean, pstdev
import googlemaps

app = Flask(__name__)
gmaps = googlemaps.Client(key='[API-KEY]]')

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

        least_time_deviation = float('inf')
        central_place = None
        individual_times = {}

        for gym, gym_location in fitness_locations:
            times = []
            for individual, individual_location in zip(individuals, individual_locations):
                result = gmaps.distance_matrix(origins=individual_location, destinations=[gym_location], mode='driving')
                time = result['rows'][0]['elements'][0]['duration']['value']
                times.append(time)
                individual_times[individual] = time

            time_deviation = pstdev(times)
            if time_deviation < least_time_deviation:
                least_time_deviation = time_deviation
                central_place = gym

        return render_template('home.html', result=central_place, individual_times=individual_times)

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
