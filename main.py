"""
Album recommendation from a playlist.

jtowler 02/02/2022
"""
import sys
from clients.spotify import SpotifyClient
from clients.discogs import DiscogsClient

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

    spotify_client = SpotifyClient()
    discogs_client = DiscogsClient()

    playlist_id = spotify_client.get_playlist_id(PLAYLIST_NAME)
    playlist_data = spotify_client.album_playlist_df(playlist_id)
    most_common_df = discogs_client.get_most_common_releases(playlist_data, limit=NUM_ALBUMS)

    print(most_common_df)
