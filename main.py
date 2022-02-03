"""
Album recommendation from a playlist.

jtowler 02/02/2022
"""
import os
import sys
from typing import List

from discogs_client.client import Client as Discogs
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd


def album_playlist_df(client: Spotify, playlist_id: str) -> pd.DataFrame:
    """
    Retrieve a DataFrame containg the albums from a given playlist id.

    :param client: Spotify client
    :param playlist_id: id of playlist to retrieve
    :return: DataFrame containing albums in playlist
    """
    response = client.playlist_items(playlist_id)
    data = pd.DataFrame(columns=['Album', 'Artist', 'Album Type'])
    for row in response['items']:
        track = row['track']
        artists = ', '.join(j['name'] for j in track['artists'])
        album = track['album']['name']
        album_type = track['album']['album_type']
        data.loc[len(data)] = [album, artists, album_type]
    return data.drop_duplicates()


def get_discogs_df(client: Discogs, spotify_df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment spotify album dataframe with info from Discogs API

    :param client: Discogs client
    :param spotify_df: Spotify album DataFrame
    :return: DataFrame containing augmented playlist album data
    """

    def get_discogs_info(title: str, artist: str) -> List[str]:
        release = client.search(artist=artist, type='release', release_title=title)[0]
        return [release.labels[0].name, release.genres[0], release.styles[0]]

    discogs_df = pd.DataFrame(columns=['Album', 'Artist', "Label", "Genre", "Style"])
    for _, row in spotify_df.iterrows():
        album, artist = row['Album'], row['Artist']
        extra_data = get_discogs_info(album.split()[0], artist)
        discogs_df.loc[len(discogs_df)] = [album, artist] + extra_data
    return spotify_df.merge(discogs_df, on=['Album', 'Artist'], how='left')


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        print("Need playlist argument")
        sys.exit(0)
    else:
        pl_id = args[1]

    sp_oauth = SpotifyOAuth(scope='playlist-modify-private playlist-modify-public')

    code = sp_oauth.get_auth_response()
    token = sp_oauth.get_access_token(code)
    sp = Spotify(auth=token['access_token'])

    discogs_client = Discogs('spotify-recommendations/0.1', user_token=os.environ['DISCOGS_TOKEN'])

    playlist_data = album_playlist_df(sp, pl_id)
    discogs_data = get_discogs_df(discogs_client, playlist_data.head())
    print(discogs_data.head())
