from statistics import mean
import googlemaps
from geopy.distance import geodesic
import itertools
from flask import Flask, render_template, request, redirect, url_for
import pyrebase
from sklearn.cluster import DBSCAN


app = Flask(__name__)

firebaseConfig = {
    "apiKey": "AIzaSyDnAhT2xI-U4HdExhBqLYmAoxB1zKTyY4w",
    "authDomain": "geocentric-703b9.firebaseapp.com",
    "databaseURL": "https://geocentric-703b9-default-rtdb.firebaseio.com/",
    "projectId": "geocentric-703b9",
    "storageBucket": "geocentric-703b9.appspot.com",
    "messagingSenderId": "946418748546",
    "appId": "1:946418748546:web:804c5b5281d6bee1c1789b"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

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
    user = auth.current_user
    if request.method == 'POST':
        apikey = request.form.get('apikey')
        central_location = request.form.get('place')
        individuals = request.form.getlist('individual')
        avoid_tolls = bool(request.form.get('toll'))
        avoid_highways = bool(request.form.get('highway'))

        gmaps = googlemaps.Client(key=apikey)
        individual_locations = get_individual_locations(gmaps, individuals)
        locations_array = [[location['lat'], location['lng']] for location in individual_locations]

        dbscan = DBSCAN(eps=0.01, min_samples=2)
        clusters = dbscan.fit_predict(locations_array)

        cluster_centroids = []
        for cluster_label in set(clusters):
            cluster_points = [locations_array[i] for i, label in enumerate(clusters) if label == cluster_label]
            centroid_lat = mean([point[0] for point in cluster_points])
            centroid_lng = mean([point[1] for point in cluster_points])
            cluster_centroids.append({'lat': centroid_lat, 'lng': centroid_lng})
        centroid = {'lat': centroid_lat, 'lng': centroid_lng}

        max_distance = calculate_max_distance(individual_locations)
        max_distance = min(max_distance, 50000)

        places_result = gmaps.places_nearby(location=centroid, keyword=central_location, radius=max_distance)
        chain_locations = [(place['vicinity'], place['geometry']['location']) for place in places_result['results']]

        location_scores = get_location_scores(gmaps, individuals, individual_locations, chain_locations, avoid_tolls, avoid_highways)

        best_locations = sorted(location_scores, key=lambda x: x[1])

        if user:
            # store the search in firestore
            search_data = {
                'user_id': user['localId'],
                'apikey': apikey,
                'central_location': central_location,
                'individuals': individuals,
                'avoid_tolls': avoid_tolls,
                'avoid_highways': avoid_highways,
                'best_locations': best_locations
            }
            db.child('searches').push(search_data)

        return render_template('home.html', best_locations=best_locations, user=user)

    return render_template('home.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            auth.sign_in_with_email_and_password(email, password)
            return redirect(url_for('home'))
        except:
            return render_template('login.html', message="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            auth.create_user_with_email_and_password(email, password)
            return redirect(url_for('home'))
        except:
            return render_template('register.html', message="Unable to create account")
    user = auth.current_user
    return render_template('register.html', user=user)

@app.route('/logout')
def logout():
    auth.current_user = None
    user = auth.current_user
    return redirect(url_for('home'))

@app.route('/history', methods=['GET'])
def history():
    user = auth.current_user
    if user:
        all_searches = db.child('searches').get().val()
        user_searches = [search for search in all_searches.values() if search['user_id'] == user['localId']]
    else:
        user_searches = []

    return render_template('history.html', search_history=user_searches, user=user)


@app.route('/help', methods=['GET'])
def help():
    user = auth.current_user
    return render_template('help.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
