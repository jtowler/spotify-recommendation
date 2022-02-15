"""
Album recommendation Flask app.

jtowler 11/02/2022
"""
from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session

from clients.discogs import DiscogsClient
from clients.spotify import SpotifyClient

app = Flask(__name__)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)


@app.route("/", methods=['GET', 'POST'])
def index():
    """
    Landing page + set API clients.

    :return: page populated with dropdown of Spotify playlists
    """
    print(request.method)
    if request.method == 'POST':
        limit = request.form.get('recommend_limit')
        playlist = request.form.get('playlist_name')
        playlists = session['spotify_client'].get_playlists()
        playlist_id = playlists[playlist]
        return redirect(url_for('recommend_albums', playlist=playlist_id, limit=limit))
    session['spotify_client'] = SpotifyClient()
    session['discogs_client'] = DiscogsClient()
    playlists = session['spotify_client'].get_playlists()
    playlist_names = playlists.keys()
    return render_template('index.html', playlist_names=playlist_names)


@app.route('/recommend/<playlist>')
@app.route('/recommend/<playlist>/<limit>')
def recommend_albums(playlist: str, limit='5') -> str:
    """
    Recommend albums from a spotify playlist search term

    :param playlist: playlist search term
    :param limit: number of albums to recommend
    :return: Page with recommended albums
    """
    limit = int(limit)

    playlist_id = session['spotify_client'].get_playlist_id(playlist)
    playlist_data = session['spotify_client'].album_playlist_df(playlist_id)
    most_common = session['discogs_client'].get_most_common_releases(playlist_data,
                                                                     session['spotify_client'],
                                                                     limit=limit)
    return render_template('recommend.html', df=most_common)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
