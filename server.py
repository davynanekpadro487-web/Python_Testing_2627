import json
from flask import Flask,render_template,request,redirect,flash,url_for


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

MAX_PLACES_PER_COMPETITION = 12
# Places déjà réservées : {(nom du club, nom de la compétition): nombre de places}
bookings = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    email = request.form.get('email', '').strip()
    if not email:
        flash("Please enter your email.")
        return redirect(url_for('index'))
    club = next((club for club in clubs if club['email'] == email), None)
    if club is None:
        flash("Sorry, that email was not found.")
        return redirect(url_for('index'))
    return render_template('welcome.html',club=club,competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub,competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])
    if placesRequired > int(competition['numberOfPlaces']):
        flash(f"Not enough places available: only {competition['numberOfPlaces']} "
              f"places left for this competition.")
        return render_template('welcome.html', club=club, competitions=competitions)
    if placesRequired > int(club['points']):
        flash(f"You do not have enough points: you have {club['points']} points "
              f"and requested {placesRequired} places.")
        return render_template('welcome.html', club=club, competitions=competitions)
    bookingKey = (club['name'], competition['name'])
    alreadyBooked = bookings.get(bookingKey, 0)
    if alreadyBooked + placesRequired > MAX_PLACES_PER_COMPETITION:
        flash(f"You cannot book more than {MAX_PLACES_PER_COMPETITION} places per competition "
              f"(already booked: {alreadyBooked}).")
        return render_template('welcome.html', club=club, competitions=competitions)
    competition['numberOfPlaces'] = int(competition['numberOfPlaces'])-placesRequired
    club['points'] = int(club['points']) - placesRequired
    bookings[bookingKey] = alreadyBooked + placesRequired
    flash(f'Great-booking complete! You booked {placesRequired} places.')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))