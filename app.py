# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
from email.policy import default
import json
from math import fabs
from urllib import response
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm as Form
from forms import *
from flask_migrate import Migrate
# from models import Venue, Artist, Show
from models import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
# migrate = Migrate(app, db)
db.create_all()

# DONE: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost:5432/fyyurdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# track modifications should be set to false
# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
# DONE: implement any missing fields, as a database migration using Flask-Migrate


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # DONE: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    error = False
    try:
        venues = Venue.query.with_entities(Venue.city, Venue.state, Venue.id).distinct()
        data = []
        for venue in venues:
            city = venue.city
            state = venue.state
            specific_venues = Venue.query.filter((Venue.city == city) & (Venue.state == state)).all()
            temp_data = []
            for item in specific_venues:
                temp_data.append({
                    "id": item.id,
                    "name": item.name,
                    "num_upcoming_shows": 1
                })
            data.append({"city": city, "state": state, "venues": temp_data})
    
    except:
        db.session.rollback
        error = True
    finally:
        db.session.close
    if error:
        flash('An error occurred.')
    else:
        pass
    return render_template('index.html', result=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    # use db.session here?
    values_returned = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    count = len(values_returned)
    data = []
    for item in values_returned:
        data.append({
            "id": item.id,
            "name": item.name,
            "num_upcoming_shows": len(
                Show.query.filter(Show.venue_id == item.id).filter(Show.start_time > datetime.now()).all())
        })
        response = {"count": count, "data": data}
    # response={
    #   "count": 1,
    #   "data": [{
    #     "id": 2,
    #     "name": "The Dueling Pianos Bar",
    #     "num_upcoming_shows": 0,
    #   }]
    # }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # DONE: replace with real venue data from the venues table, using venue_id
    error = False
    try:
        specific_venue = Venue.query.get(venue_id)
        particular_shows = Show.query.filter(Show.venue_id == venue_id).order_by(Show.artist_id)
        past_shows = []
        upcoming_shows = []
        for show in particular_shows:
            artist_id = show.artist_id
            data_artist = {
                "artist_id": artist_id,
                "artist_name": Artist.query.get(artist_id).name,
                "artist_image_link": Artist.query.get(artist_id).image_link,
                "start_time": show.start_time
            }
            if show.start_time < datetime.now():
                past_shows.append(data_artist)
            elif show.start_time > datetime.now():
                upcoming_shows.append(data_artist)
        data = {
            "id": specific_venue.id,
            "name": specific_venue.name,
            "genres": specific_venue.genres,
            "address": specific_venue.address,
            "city": specific_venue.city,
            "state": specific_venue.state,
            "phone": specific_venue.phone,
            "website": specific_venue.website,
            "facebook_link": specific_venue.facebook_link,
            "seeking_talent": specific_venue.seeking_talent,
            "seeking_description": specific_venue.seeking_description,
            "image_link": specific_venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
        }

    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        pass
    else:
        pass
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # DONE: insert form data as a new Venue record in the db, instead
    # DONE: modify data to be the data object returned from db insertion
    error = False
    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        image_link = request.form.get("image_link")
        genres = ",".join(request.form.get('genres'))
        facebook_link = request.form.get("facebook_link")
        website_link = request.form.get("website_link")
        if request.form.get('seeking_talent'):
            Venue.seeking_talent = True
        else:
            Venue.seeking_talent = False
        seeking_description = request.form.get("seeking_description")

        created_venue = Venue(name=name, city=city,
                              state=state, address=address, phone=phone, image_link=image_link,
                              genres=genres, facebook_link=facebook_link,
                              website_link=website_link,
                              seeking_description=seeking_description)

        db.session.add(created_venue)
        db.session.commit()

    except:
        db.session.rollback()
        error = True

    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # DONE: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash(f'An error occurred. Venue {(Venue.query.get(venue_id)).name} could not be deleted.')
    else:
        flash(f'Venue {(Venue.query.get(venue_id)).name} was successfully deleted!')
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # DONE: replace with real data returned from querying the database
    data = Artist.query.all()
    # data=[]
    # for artist in all_artists:
    #   data.append({"id":artist.id, "name":artist.name})
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    values_returned = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    count = len(values_returned)
    data = []
    for item in values_returned:
        data.append({
            "id": item.id,
            "name": item.name,
            "num_upcoming_shows": len(
                Show.query.filter(Show.artist_id == item.id).filter(Show.start_time > datetime.now()).all())
        })
    response = {"count": count, "data": data}

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # DONE: replace with real artist data from the artist table, using artist_id
    error = False
    try:
        specific_artist = Artist.query.get(artist_id)
        particular_shows = Show.query.filter(Show.artist_id == artist_id).order_by(Show.artist_id)
        past_shows = []
        upcoming_shows = []
        for show in particular_shows:
            venue_id = show.venue_id
            data_venue = {
                "venue_id": venue_id,
                "venue_name": Venue.query.get(venue_id).name,
                "venue_image_link": Venue.query.get(venue_id).image_link,
                "start_time": show.start_time
            }
            if show.start_time < datetime.now():
                past_shows.append(data_venue)
            elif show.start_time > datetime.now():
                upcoming_shows.append(data_venue)
        data = {
            "id": specific_artist.id,
            "name": specific_artist.name,
            "genres": specific_artist.genres,
            "city": specific_artist.city,
            "state": specific_artist.state,
            "phone": specific_artist.phone,
            "website": specific_artist.website,
            "facebook_link": specific_artist.facebook_link,
            "seeking_venue": specific_artist.seeking_venue,
            "seeking_description": specific_artist.seeking_description,
            "image_link": specific_artist.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
        }
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred.')
    else:
        pass
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.image_link = request.form['image_link']
        artist.genres = ",".join(request.form.get('genres'))
        artist.facebook_link = request.form['facebook_link']
        artist.website_link = request.form['website_link']
        if 'seeking_venue' in request.form['seeking_venue']:
            artist.seeking_venue = True
        else:
            artist.seeking_venue = False
        artist.seeking_description = request.form['seeking_description']
        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.image_link = request.form['image_link']
        venue.genres = ",".join(request.form.get('genres'))
        venue.facebook_link = request.form['facebook_link']
        venue.website_link = request.form['website_link']
        venue.seeking_talent = request.form['seeking_talent']
        venue.seeking_description = request.form['seeking_description']
        db.session.add(venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        image_link = request.form['image_link']
        genres = ",".join(request.form.get('genres'))
        facebook_link = request.form['facebook_link']
        website_link = request.form['website_link']
        if request.form.get('seeking_venue'):
            seeking_venue = True
        seeking_description = request.form['seeking_description']
        created_artist = Artist(name=name, city=city, state=state, phone=phone,
                                image_link=image_link, genres=genres, facebook_link=facebook_link,
                                website_link=website_link, seeking_venue=seeking_venue,
                                seeking_description=seeking_description)
        db.session.add(created_artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    show_all = Show.query.all()
    for show in show_all:
        artist_id = show.artist_id
        venue_id = show.venue_id
        data.append({
            "venue_id": venue_id,
            "venue_name": Venue.query.get(venue_id).name,
            "artist_id": artist_id,
            "artist_name": Artist.query.get(artist_id).name,
            "artist_image_link": Artist.query.get(artist_id).image_link,
            "start_time": show.start_time
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error_venue = False
    error_artist = False
    try:
        venue_id = request.form['venue_id']
        artist_id = request.form['artist_id']
        start_time = request.form['start_time']
        possible_venue = Venue.query.get(venue_id)
        possible_artist = Artist.query.get(artist_id)
        # Adding records to show
        created_show = Show(venue_id=possible_venue.id, artist_id=possible_artist.id, start_time=start_time)
        db.session.add(created_show)
        db.session.commit()
    except:
        db.session.rollback()
        if possible_venue is None:
            error_venue = True
        if possible_artist is None:
            error_artist = True
    finally:
        db.session.close()
    if error_venue == True:
        flash('An error occurred. Show could not be listed. Make sure venue_id is correct.')

    if error_artist == True:
        flash('An error occurred. Show could not be listed. Make sure artist_id is correct.')
    if error_venue == False and error_artist == False:
        flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
