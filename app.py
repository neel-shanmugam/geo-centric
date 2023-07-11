from flask import Flask, request, render_template
from statistics import mean, pstdev
import googlemaps

app = Flask(__name__)
gmaps = googlemaps.Client(key='[API-KEY]]')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        chain = 'LA Fitness'
        person_locations = []
        persons = request.form.getlist('person')  # Get the list of people from form

        # Get the latitude and longitude of each person's location
        for person in persons:
            geocode_result = gmaps.geocode(person)
            person_location = geocode_result[0]['geometry']['location']
            person_locations.append(person_location)

        # Find the centroid of all locations
        centroid_lat = mean([location['lat'] for location in person_locations])
        centroid_lng = mean([location['lng'] for location in person_locations])
        centroid = {'lat': centroid_lat, 'lng': centroid_lng}
        print(centroid)

        # Find LA Fitness locations near the centroid
        places_result = gmaps.places_nearby(location=centroid, keyword=chain, radius=50000)
        chain_locations = [(place['vicinity'], place['geometry']['location']) for place in places_result['results']]
        print(chain_locations)

        min_time_deviation = float('inf')
        central_location = None

        for gym, gym_location in chain_locations:
            times = []
            for person_location in person_locations:
                result = gmaps.distance_matrix(origins=person_location, destinations=[gym_location], mode='driving')
                time = result['rows'][0]['elements'][0]['duration']['value']  # Use 'duration' for driving time
                times.append(time)
                print(gym, person_location, time)

            time_deviation = pstdev(times)  # Calculate standard deviation of times
            if time_deviation < min_time_deviation:
                min_time_deviation = time_deviation
                central_location = gym

        return render_template('home.html', result=central_location)

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
