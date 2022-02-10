"""
Discogs Client

jtowler 09/02/2022
"""
import os
import time

import pandas as pd
from discogs_client.client import Client

from utils import release_to_dataframe, strip_brackets, get_most_common_data


class DiscogsClient:
    """
    Wrapper around discogs client for the extraction of album data.
    """
    def __init__(self):
        self.client = Client('spotify-recommendations/0.1', user_token=os.environ['DISCOGS_TOKEN'])

    def get_most_common_releases(self,
                                 playlist_df: pd.DataFrame,
                                 limit: int = 5) -> pd.DataFrame:
        """
        Get the top results using the most common attributes in the given playlist

        :param playlist_df: DataFrame of albums to recommend from
        :param limit: number of releases to return
        :return: DataFrame with the recommended releases
        """
        discogs_data = self.get_discogs_df(playlist_df.head())
        most_common = get_most_common_data(discogs_data)

        releases = self.client.search(type='master', format='album', **most_common)
        num_releases = releases.count

        dfs = []
        index = 0

        while len(dfs) < limit and index < num_releases:
            release_df = release_to_dataframe(releases[index])
            overlap = len(playlist_df[(playlist_df['Artist'].isin(release_df['artist'])) &
                                      (playlist_df['Album'].isin(release_df['release_title']))])

            if overlap == 0:
                dfs.append(release_df)
            index += 1
        return pd.concat(dfs, ignore_index=True)

    def get_discogs_df(self, spotify_df: pd.DataFrame) -> pd.DataFrame:
        """
        Augment spotify album dataframe with info from Discogs API

        :param spotify_df: Spotify album DataFrame
        :return: DataFrame containing augmented playlist album data
        """

        def get_discogs_info(**kwargs) -> pd.DataFrame:
            kwargs['release_title'] = strip_brackets(kwargs['release_title'])
            release = self.client.search(type='master', format='album', **kwargs)[0]
            return release_to_dataframe(release)

        dfs = []
        for _, row in spotify_df.iterrows():
            album, artist = row['Album'], row['Artist']
            release_df = get_discogs_info(release_title=album, artist=artist)
            time.sleep(3)
            dfs.append(release_df)
        return pd.concat(dfs, ignore_index=True)
