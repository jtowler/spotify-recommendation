"""
Album recommendation from a playlist.

jtowler 02/02/2022
"""
import os
import sys
import time

from discogs_client.client import Client as Discogs
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd


def get_most_common_data(discogs_df: pd.DataFrame) -> dict:
    """
    Get the most commonly occurring combinations of parameters in the data.

    :param discogs_df: DataFrame containing the discogs data of releases.
    :return: dict containing the most common parameters
    """
    mode_data = discogs_df.drop(
        columns=["album", "artist", "num_for_sale", "lowest_price"]
    ).mode()
    return mode_data.iloc[0].to_dict()


def strip_brackets(string: str) -> str:
    """
    Remove text after first set of brackets.

    :param string: String to strip brackets from
    :return: string with brackets removed
    """

    puncs = [':', '(', '*']
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

    def get_discogs_info(title: str, artist: str) -> pd.DataFrame:
        album = strip_brackets(title)
        release = client.search(artist=artist, type='release', release_title=album)[0]
        main_rel = release.master.main_release
        market_stats = main_rel.marketplace_stats

        data = {
            'album': title,
            'artist': artist,
            "label": main_rel.labels[0].name,
            "genre": main_rel.genres[0],
            "style": main_rel.styles[0],
            "year": int(main_rel.year),
            "country": main_rel.country,
            "num_for_sale": market_stats.num_for_sale,
            "lowest_price": market_stats.lowest_price.value
        }

        return pd.DataFrame(data, index=[0])

    dfs = []
    for _, row in spotify_df.iterrows():
        album, artist = row['Album'], row['Artist']
        time.sleep(3)
        release_df = get_discogs_info(album, artist)
        dfs.append(release_df)
    return pd.concat(dfs, ignore_index=True)


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
    most_common = get_most_common_data(discogs_data)

    print(most_common)
