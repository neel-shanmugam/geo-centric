GeoCentric is a Flask-based web application that utilizes the Google Maps API to help groups find the most centrally located chain (like a favorite restaurant, gym, etc.) among their members. The application determines this central location by finding the place that minimizes the standard deviation of travel times from each individual to the chain location.

This is perfect for friends, colleagues, or teams who are spread out geographically but want to find a common meeting spot that is fair in terms of travel time.

The project is available at http://www.geocentric.pythonanywhere.com. The project can also be ran using the following instructions.

Prerequisites
- Python 3.8+
- Flask
- Google Maps Python Client

Getting Started
Clone the repository:

git clone https://github.com/<username>/GeoCentric.git

cd GeoCentric

Install the required Python packages:
pip install flask googlemaps

Run the Flask application:
python3 app.py

Now, you should be able to see your application running at http://127.0.0.1:5000/ in your web browser.

Usage
Input a Google Maps API Key.
Enter a location of interest.
Enter the addresses of all individuals.
Click on the 'Submit' button.
The application will display the most centrally located chain, considering all provided addresses.
Please note, for the demo purposes, the chain is hardcoded to 'LA Fitness'. You can modify this as per your requirements.

Contributing
Please feel free to fork this repo, make changes, submit pull requests. For major changes, please open an issue first and discuss it with the other authors.
