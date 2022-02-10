"""
Helper functions.

jtowler 09/02/2022
"""
import pandas as pd
from discogs_client import Master


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
