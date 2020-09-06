from fastapi import HTTPException
import asyncio
import logging
import itertools


logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, message):
        self.message = message


class BrowsingHandler:
    async def TrackInfo(self, trackId):
        track = await self.ytMusic._get_song(trackId)

        album_art_64, album_art_300, album_art_640 = sort_thumbnails(
            track["thumbnail"]["thumbnails"]
        )

        track_artists = track.get("artists", [track["author"]])
        album_artists = track_artists  # UNDEFINED so we use track_artists
        return {
            "track_id": track["videoId"],
            "track_name": track["title"],
            "track_artists": track_artists,
            # "track_number": 1,  # UNDEFINED
            "track_duration": int(track["lengthSeconds"]) * 1000,
            "album_art_640": album_art_640,
            "album_art_300": album_art_300,
            "album_art_64": album_art_64,
            # "album_id": "",  # UNDEFINED
            # "album_name": "",  # UNDEFINED
            "year": track["release"].split("-")[0] if "release" in track else "",
            "album_artists": album_artists,
            # "album_length": 1,  # UNDEFINED
            # "album_type": "album",  # UNDEFINED
        }

    
    async def ArrangeVideoIds(self, searchQueriesList, videoIdList, videoIdListIndex):
        youtubeResult = await self.ytMusic._search(searchQueriesList[videoIdListIndex], "songs")
        videoIdList[videoIdListIndex] = youtubeResult[0]["videoId"] #✅
    
    async def AsyncAlbumSearch(self, searchQueriesList, videoIdList):
        args = [(searchQueriesList, videoIdList, index) for index in range(0, len(videoIdList))]
        asyncSearchTasks = itertools.starmap(self.ArrangeVideoIds, args)
        await asyncio.gather(*asyncSearchTasks)

    async def AlbumInfo(self, albumId):
        response = await self.ytMusic._get_album(albumId)

        tracks = response["tracks"]

        videoIdList = ["" for index in range(0, len(tracks))]
        searchQueriesList = [track["title"] + " " + track["artists"] for track in tracks]
        await self.AsyncAlbumSearch(searchQueriesList, videoIdList)

        result = []
        for index in range(0, len(tracks)):
            track = tracks[index]
            result += [
                {
                    "track_id": videoIdList[index],
                    "track_name": track["title"],
                    "track_artists": [track["artists"]],
                    "track_number": int(track["index"]),
                    "track_duration": int(track["lengthMs"]),
                }
            ]
        return {"tracks": result}

    async def ArtistAlbums(self, artistId):
        # обьединить с singles
        artistJson = await self.ytMusic._get_artist(artistId)

        artistAlbums = []
        for album in artistJson["albums"]["results"]:
            album_art_64, album_art_300, album_art_640 = sort_thumbnails(
                album["thumbnails"]
            )
            artistAlbums += [
                {
                    "album_id": album["browseId"],
                    "album_name": album["title"],
                    "year": album["year"],
                    "album_artists": [artistJson["name"]],
                    "album_art_640": album_art_640,
                    "album_art_300": album_art_300,
                    "album_art_64": album_art_64,
                    # "album_length": 1,  # UNDEFINED
                    # "album_type": "album",  # UNDEFINED
                }
            ]
        return {"albums": artistAlbums}

    async def ArtistTracks(self, artistId):
        artistJson = await self.ytMusic._get_artist(artistId)

        artistTracks = []
        for track in artistJson["songs"]["results"]:
            track_artists = [a["name"] for a in track["artists"]]
            album_artists = track_artists  # UNDEFINED so we use track_artists
            album_art_64, album_art_300, album_art_640 = sort_thumbnails(
                track["thumbnails"]
            )
            artistTracks += [
                {
                    "track_id": track["videoId"],
                    "track_name": track["title"],
                    "track_artists": track_artists,
                    # "track_number": 1,  # UNDEFINED
                    # "track_duration": 1,  # UNDEFINED
                    "album_art_640": album_art_640,
                    "album_art_300": album_art_300,
                    "album_art_64": album_art_64,
                    "album_id": track["album"]["id"],
                    "album_name": track["album"]["name"],
                    # "year": "0000",  # UNDEFINED
                    "album_artists": album_artists,
                    # "album_length": 1,  # UNDEFINED
                    # "album_type": "album",  # UNDEFINED
                }
            ]
        return {"albums": artistTracks}

    async def ArrangeAlbumLength(self, albumIdList, albumLengthList, albumLengthListIndex):
        youtubeResult = await self.ytMusic._get_album(albumIdList[albumLengthListIndex])
        albumLengthList[albumLengthListIndex] = int(youtubeResult["trackCount"]) #✅

    async def AsyncAlbumLength(self, albumIdList, albumLengthList):
        args = [(albumIdList, albumLengthList, index) for index in range(0, len(albumIdList))]
        asyncSearchTasks = itertools.starmap(self.ArrangeAlbumLength, args)
        await asyncio.gather(*asyncSearchTasks)

    async def ArrangeTrackStuff(self, trackIdList, albumIdList, trackNumberList, yearList, albumLengthList, albumTypeList, albumLengthListIndex):
        youtubeResult = await self.ytMusic._get_album(albumIdList[albumLengthListIndex])
        for track in youtubeResult["tracks"]:
            if track["title"] == trackIdList[albumLengthListIndex]:
                trackNumberList[albumLengthListIndex] = int(track["index"]) #✅
                break
        yearList[albumLengthListIndex] = youtubeResult["releaseDate"]["year"] #✅
        albumLengthList[albumLengthListIndex] = int(youtubeResult["trackCount"]) #✅
        albumTypeList[albumLengthListIndex] = "single" if len(youtubeResult["tracks"]) == 1 else "album" #✅

    async def AsyncTrackStuff(self, trackIdList, albumIdList, trackNumberList, yearList, albumLengthList, albumTypeList):
        args = [(trackIdList, albumIdList, trackNumberList, yearList, albumLengthList, albumTypeList, index) for index in range(0, len(albumIdList))]
        asyncSearchTasks = itertools.starmap(self.ArrangeTrackStuff, args)
        await asyncio.gather(*asyncSearchTasks)
    
    async def SearchYoutube(self, keyword, mode):
        if mode == "album":
            youtubeResult = await self.ytMusic._search(keyword, "albums")
            
            albumIdList = [album["browseId"] for album in youtubeResult]
            albumLengthList = ["" for album in youtubeResult]
            await self.AsyncAlbumLength(albumIdList, albumLengthList)

            albums = []
            for index in range(0, len(youtubeResult)):
                album = youtubeResult[index]
                album_art_64, album_art_300, album_art_640 = sort_thumbnails(
                    album["thumbnails"]
                )
                albums += [
                    {
                        "album_id": album["browseId"],
                        "album_name": album["title"],
                        "year": album["year"],
                        "album_artists": [album["artist"]],
                        "album_art_640": album_art_640,
                        "album_art_300": album_art_300,
                        "album_art_64": album_art_64,
                        "album_length": albumLengthList[index],
                        "album_type": "album" if album["type"].lower() == "ep" else album["type"].lower(),
                    }
                ]
            return {"albums": albums}

        if mode == "track":
            youtubeResult = await self.ytMusic._search(keyword, "songs")

            albumIdList = [track["album"]["id"] for track in youtubeResult]
            trackIdList = [track["title"] for track in youtubeResult]
            trackNumberList = ["" for track in youtubeResult]
            yearList = ["" for track in youtubeResult]
            albumLengthList = ["" for track in youtubeResult]
            albumTypeList = ["" for track in youtubeResult]
            await self.AsyncTrackStuff(trackIdList, albumIdList, trackNumberList, yearList, albumLengthList, albumTypeList)

            tracks = []
            for index in range(0, len(youtubeResult)):
                track = youtubeResult[index]
                album_art_64, album_art_300, album_art_640 = sort_thumbnails(
                    track["thumbnails"]
                )
                track_artists = [a["name"] for a in track["artists"]]
                album_artists = track_artists
                tracks += [
                    {
                        "track_id": track["videoId"],
                        "track_name": track["title"],
                        "track_artists": track_artists,
                        "track_number": trackNumberList[index],
                        "track_duration": (
                            int(track["duration"].split(":")[0]) * 60
                            + int(track["duration"].split(":")[1])
                        )
                        * 1000,
                        "album_id": track["album"]["id"],
                        "album_name": track["album"]["name"],
                        "year": yearList[index],
                        "album_artists": album_artists,
                        "album_art_640": album_art_640,
                        "album_art_300": album_art_300,
                        "album_art_64": album_art_64,
                        "album_length": albumLengthList[index],
                        "album_type": albumTypeList[index],
                    }
                ]
            return {"tracks": tracks}

        if mode == "artist":
            youtubeResult = await self.ytMusic._search(keyword, "artists")

            artists = []
            for artist in youtubeResult:
                artist_art_64, artist_art_300, artist_art_640 = sort_thumbnails(
                    artist["thumbnails"]
                )
                artists += [
                    {
                        "artist_id": artist["browseId"],
                        "artist_name": artist["artist"],
                        "artist_art_640": artist_art_640,
                        "artist_art_300": artist_art_300,
                        "artist_art_64": artist_art_64,
                    }
                ]
            return {"artists": artists}


def sort_thumbnails(thumbnails):
    thumbs = {}
    for thumbnail in thumbnails:
        wh = thumbnail["width"] * thumbnail["height"]
        thumbs[wh] = thumbnail["url"]
    resolutions = sorted(list(thumbs.keys()))
    max = resolutions[-1]
    mid = resolutions[-2] if len(resolutions) > 2 else max
    min = resolutions[0]

    return (thumbs[min], thumbs[mid], thumbs[max])
