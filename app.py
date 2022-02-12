"""
Album recommendation Flask app.

jtowler 11/02/2022
"""
from flask import Flask, session
from flask_session import Session

from clients.discogs import DiscogsClient
from clients.spotify import SpotifyClient

app = Flask(__name__)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)


@app.route("/")
def index() -> str:
    """
    Landing page + set API clients.

    :return: welcome message string
    """
    session['spotify_client'] = SpotifyClient()
    session['discogs_client'] = DiscogsClient()
    return "Welcome to the album recommender."


@app.route('/<playlist>')
@app.route('/<playlist>/<limit>')
def recommend_albums(playlist: str, limit='5') -> str:
    """
    Recommend albums from a spotify playlist search term

    :param playlist: playlist search term
    :param limit: number of albums to recommend
    :return: html table of recommended albums
    """
    limit = int(limit)

    playlist_id = session['spotify_client'].get_playlist_id(playlist)
    playlist_data = session['spotify_client'].album_playlist_df(playlist_id)
    most_common_df = session['discogs_client'].get_most_common_releases(playlist_data, limit=limit)
    return most_common_df.to_html()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
