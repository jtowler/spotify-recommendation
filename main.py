"""
Album recommendation from a playlist.

jtowler 02/02/2022
"""
import os
import sys
import time

from discogs_client import Master
from discogs_client.client import Client as Discogs
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from thefuzz.fuzz import partial_ratio


def get_playlist_id(client: Spotify, search: str) -> str:
    """
    Get the Spotify playlist ID from a search term.

    :param client: Spotify client
    :param search: search term to identify playlist with
    :return: ID of selected playlist
    """
    response = client.current_user_playlists()
    playlist_dict = {i['name']: i['id'] for i in response['items']}
    scores = {i: partial_ratio(search, i) for i in playlist_dict.keys()}
    max_key = max(scores, key=scores.get)
    return playlist_dict[max_key]


def get_most_common_data(discogs_df: pd.DataFrame) -> dict:
    """
    Get the most commonly occurring combinations of parameters in the data.

    :param discogs_df: DataFrame containing the discogs data of releases.
    :return: dict containing the most common parameters
    """
    mode_data = discogs_df.drop(
        columns=["release_title", "artist", "num_for_sale", "lowest_price"]
    ).mode()
    return mode_data.iloc[0].to_dict()


def release_to_dataframe(release: Master) -> pd.DataFrame:
    """
    Convert a discogs release to a DataFrame

    :param release: Discogs master release

    :return: release data as a DataFrame
    """
    main_rel = release.main_release
    market_stats = main_rel.marketplace_stats
    num_for_sale = market_stats.num_for_sale
    if num_for_sale == 0:
        lowest_price = None
    else:
        lowest_price = market_stats.lowest_price.value

    data = {
        'release_title': main_rel.title,
        'artist': main_rel.artists[0].name,
        "label": main_rel.labels[0].name,
        "genre": main_rel.genres[0],
        "style": main_rel.styles[0],
        "year": int(main_rel.year),
        "country": main_rel.country,
        "num_for_sale": num_for_sale,
        "lowest_price": lowest_price
    }

    return pd.DataFrame(data, index=[0])


def get_most_common_releases(client: Discogs,
                             playlist_df: pd.DataFrame,
                             limit: int = 5) -> pd.DataFrame:
    """
    Get the top results using the most common attributes in the given playlist

    :param client: Discogs client
    :param playlist_df: DataFrame of albums to recommend from
    :param limit: number of releases to return
    :return: DataFrame with the recommended releases
    """
    discogs_data = get_discogs_df(discogs_client, playlist_df.head())
    most_common = get_most_common_data(discogs_data)

    releases = client.search(type='master', format='album', **most_common)
    if releases.count < limit:
        limit = releases.count

    dfs = []
    for i in range(limit):
        dfs.append(release_to_dataframe(releases[i]))
    return pd.concat(dfs, ignore_index=True)


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


def album_playlist_df(client: Spotify, pl_id: str) -> pd.DataFrame:
    """
    Retrieve a DataFrame containg the albums from a given playlist id.

    :param client: Spotify client
    :param pl_id: id of playlist to retrieve
    :return: DataFrame containing albums in playlist
    """
    response = client.playlist_items(pl_id)
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

    def get_discogs_info(**kwargs) -> pd.DataFrame:
        kwargs['release_title'] = strip_brackets(kwargs['release_title'])
        release = client.search(type='master', format='album', **kwargs)[0]
        return release_to_dataframe(release)

    dfs = []
    for _, row in spotify_df.iterrows():
        album, artist = row['Album'], row['Artist']
        release_df = get_discogs_info(release_title=album, artist=artist)
        time.sleep(3)
        dfs.append(release_df)
    return pd.concat(dfs, ignore_index=True)


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        print("Need playlist argument")
        sys.exit(0)
    else:
        PLAYLIST_NAME = args[1]

    if len(args) > 2:
        NUM_ALBUMS = int(args[2])
    else:
        NUM_ALBUMS = 5

    sp_oauth = SpotifyOAuth(scope='playlist-modify-private playlist-modify-public')

    code = sp_oauth.get_auth_response()
    token = sp_oauth.get_access_token(code)
    sp = Spotify(auth=token['access_token'])

    discogs_client = Discogs('spotify-recommendations/0.1', user_token=os.environ['DISCOGS_TOKEN'])

    playlist_id = get_playlist_id(sp, PLAYLIST_NAME)
    playlist_data = album_playlist_df(sp, playlist_id)
    most_common_df = get_most_common_releases(discogs_client, playlist_data, limit=NUM_ALBUMS)

    print(most_common_df)
