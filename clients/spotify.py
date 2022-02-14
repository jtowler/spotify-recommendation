"""
Spotify Client

jtowler 09/02/2022
"""
import pandas as pd
from spotipy import SpotifyOAuth, Spotify
from thefuzz.fuzz import partial_ratio


class SpotifyClient:
    """
    Wrapper around spotify client for the extraction of playlist data.
    """

    def __init__(self):
        sp_oauth = SpotifyOAuth(scope='playlist-modify-private playlist-modify-public')

        code = sp_oauth.get_auth_response()
        token = sp_oauth.get_access_token(code)
        self.client = Spotify(auth=token['access_token'])

    def get_playlists(self) -> dict:
        """
        Get the Spotify playlist ID from a search term.

        :return: dictionary of playlist name: ID
        """
        response = self.client.current_user_playlists()
        return {i['name']: i['id'] for i in response['items']}

    def get_playlist_id(self, search: str, playlist: dict = None) -> str:
        """
        Get the Spotify playlist ID from a search term.

        :param search: search term to identify playlist with
        :param playlist: playlist dictionary, if missing get from spotify client
        :return: ID of selected playlist
        """
        if playlist is None:
            playlist_dict = self.get_playlists()
        else:
            playlist_dict = playlist
        scores = {i: partial_ratio(search, i) for i in playlist_dict.keys()}
        max_key = max(scores, key=scores.get)
        return playlist_dict[max_key]

    def album_playlist_df(self, pl_id: str) -> pd.DataFrame:
        """
        Retrieve a DataFrame containg the albums from a given playlist id.

        :param pl_id: id of playlist to retrieve
        :return: DataFrame containing albums in playlist
        """
        response = self.client.playlist_items(pl_id)
        data = pd.DataFrame(columns=['Album', 'Artist', 'Album Type'])
        for row in response['items']:
            track = row['track']
            artists = ', '.join(j['name'] for j in track['artists'])
            album = track['album']['name']
            album_type = track['album']['album_type']
            data.loc[len(data)] = [album, artists, album_type]
        return data.drop_duplicates()

    def get_spotify_link(self, artist: str, album: str) -> str:
        """
        Search for link to the spotify album page

        :param artist: artist to search for
        :param album: album to search for
        :return: Spotify link
        """
        query = f'artist:{artist} album:{album}'
        response = self.client.search(q=query, type='album')
        items = response['albums']['items']
        if len(items) == 0:
            return ''
        for i in items:
            if i['album_type'] == 'album':
                return i['external_urls']['spotify']
        return ''
