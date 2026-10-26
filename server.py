import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for


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

PAST_COMPETITION_ERROR = "Cette compétition a déjà eu lieu, la réservation n'est pas possible."
INVALID_PLACES_ERROR = "Veuillez saisir un nombre de places valide (un entier supérieur à 0)."
CLUB_NOT_FOUND_ERROR = "Club introuvable, veuillez vous reconnecter."
COMPETITION_NOT_FOUND_ERROR = (
    "Compétition introuvable, veuillez choisir une compétition dans la liste."
)

FRENCH_MONTHS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


@app.template_filter('date_fr')
def date_fr(value):
    """Formate une date 'YYYY-MM-DD HH:MM:SS' en '27 mars 2020 à 10h00'."""
    try:
        dt = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return value
    month_name = FRENCH_MONTHS[dt.month - 1]
    return f"{dt.day} {month_name} {dt.year} à {dt.hour:02d}h{dt.minute:02d}"


@app.template_filter('sort_by_points')
def sort_by_points(club_list):
    """Retourne une nouvelle liste de clubs triée par points décroissants."""
    return sorted(club_list, key=lambda c: int(c['points']), reverse=True)


def isPastCompetition(competition):
    """Retourne True si la date de la compétition est déjà passée."""
    competitionDate = datetime.strptime(competition['date'], "%Y-%m-%d %H:%M:%S")
    return competitionDate < datetime.now()


app.jinja_env.globals['isPastCompetition'] = isPastCompetition


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/showSummary', methods=['POST'])
def showSummary():
    email = request.form.get('email', '').strip()
    if not email:
        flash("Veuillez saisir votre adresse e-mail.", "error")
        return redirect(url_for('index'))
    club = next((club for club in clubs if club['email'] == email), None)
    if club is None:
        flash("Désolé, cette adresse e-mail est introuvable.", "error")
        return redirect(url_for('index'))
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    foundClub = next((c for c in clubs if c['name'] == club), None)
    if foundClub is None:
        flash(CLUB_NOT_FOUND_ERROR, "error")
        return redirect(url_for('index'))
    foundCompetition = next((c for c in competitions if c['name'] == competition), None)
    if foundCompetition is None:
        flash(COMPETITION_NOT_FOUND_ERROR, "error")
        return render_template('welcome.html', club=foundClub, competitions=competitions)
    if isPastCompetition(foundCompetition):
        flash(PAST_COMPETITION_ERROR, "error")
        return render_template('welcome.html', club=foundClub, competitions=competitions)
    return render_template('booking.html', club=foundClub, competition=foundCompetition)


@app.route('/purchasePlaces', methods=['POST'])
def purchasePlaces():
    club = next((c for c in clubs if c['name'] == request.form.get('club')), None)
    if club is None:
        flash(CLUB_NOT_FOUND_ERROR, "error")
        return redirect(url_for('index'))
    competition = next((c for c in competitions
                        if c['name'] == request.form.get('competition')), None)
    if competition is None:
        flash(COMPETITION_NOT_FOUND_ERROR, "error")
        return render_template('welcome.html', club=club, competitions=competitions)
    try:
        placesRequired = int(request.form.get('places', ''))
    except ValueError:
        placesRequired = 0
    if placesRequired <= 0:
        flash(INVALID_PLACES_ERROR, "error")
        return render_template('welcome.html', club=club, competitions=competitions)
    if isPastCompetition(competition):
        flash(PAST_COMPETITION_ERROR, "error")
        return render_template('welcome.html', club=club, competitions=competitions)
    availablePlaces = int(competition['numberOfPlaces'])
    if placesRequired > availablePlaces:
        placeWord = "place" if availablePlaces <= 1 else "places"
        flash(f"Pas assez de places disponibles : il ne reste que {availablePlaces} "
              f"{placeWord} pour cette compétition.", "error")
        return render_template('welcome.html', club=club, competitions=competitions)
    clubPoints = int(club['points'])
    if placesRequired > clubPoints:
        pointWord = "point" if clubPoints <= 1 else "points"
        reqPlaceWord = "place" if placesRequired == 1 else "places"
        flash(f"Vous n'avez pas assez de points : vous avez {clubPoints} {pointWord} "
              f"et avez demandé {placesRequired} {reqPlaceWord}.", "error")
        return render_template('welcome.html', club=club, competitions=competitions)
    bookingKey = (club['name'], competition['name'])
    alreadyBooked = bookings.get(bookingKey, 0)
    if alreadyBooked + placesRequired > MAX_PLACES_PER_COMPETITION:
        flash(f"Vous ne pouvez pas réserver plus de {MAX_PLACES_PER_COMPETITION} places par compétition "
              f"(déjà réservées : {alreadyBooked}).", "error")
        return render_template('welcome.html', club=club, competitions=competitions)
    competition['numberOfPlaces'] = availablePlaces - placesRequired
    club['points'] = clubPoints - placesRequired
    bookings[bookingKey] = alreadyBooked + placesRequired
    if placesRequired == 1:
        flash('Réservation confirmée : 1 place réservée.', "success")
    else:
        flash(f'Réservation confirmée : {placesRequired} places réservées.', "success")
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/points', methods=['GET'])
def points():
    """Tableau public (sans connexion) des points de tous les clubs."""
    return render_template('points.html', clubs=clubs)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))
