"""
Album recommendation from a playlist.

jtowler 02/02/2022
"""
import os
import sys
from typing import List
import time

from discogs_client.client import Client as Discogs
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd


def strip_brackets(string: str) -> str:
    """
    Remove text after first set of brackets.

    :param string: String to strip brackets from
    :return: string with brackets removed
    """

    puncs = [':', '(']
    punc_indices = [string.index(punc) for punc in puncs if punc in string]
    if len(punc_indices) > 0:
        index = min(punc_indices)
        string = string[:index]
    return string


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
        main_rel = release.master.main_release
        market_stats = main_rel.marketplace_stats
        return [main_rel.labels[0].name,
                main_rel.genres[0],
                main_rel.styles[0],
                main_rel.year,
                main_rel.country,
                market_stats.number_for_sale,
                market_stats.lowest_price]

    discogs_df = pd.DataFrame(
        columns=['Album', 'Artist', "Label", "Genre", "Style", "Year", "Country",
                 "Number for Sale", "Lowest Price"]
    )
    for _, row in spotify_df.iterrows():
        album, artist = row['Album'], row['Artist']
        time.sleep(3)
        extra_data = get_discogs_info(strip_brackets(album), artist)
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
