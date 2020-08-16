from youtubesearchpython import SearchVideos
import youtube_dl
import json
from urllib.request import urlopen
from urllib.request import Request
import os
import youtube_dl
from mutagen.mp4 import MP4, MP4Cover
from flask import make_response, Response


class YoutubeHandler:

    def SaveAudio(self, videoId, trackId):
        ydl_opts = {
            'format': '140',
            'cookiefile': 'cookies.txt',
            'outtmpl': f'{trackId}.m4a',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={videoId}'])
        print(f'[download] Track download successful for track ID: {trackId}.')

    def SaveMetaData(self, trackInfoJSON):

        print('[metadata] Getting album art: ' + trackInfoJSON['album_art_640'])

        albumArtBinary = urlopen(trackInfoJSON['album_art_640']).read()

        print('[metadata] Album art retrieved.')

        trackId = trackInfoJSON['track_id']

        audioFile = MP4(f'{trackId}.m4a')

        audioFile["covr"]    = [MP4Cover(albumArtBinary, imageformat=MP4Cover.FORMAT_JPEG)]
        audioFile['\xa9nam'] = trackInfoJSON['track_name']
        audioFile['\xa9alb'] = trackInfoJSON['album_name']
        audioFile['\xa9ART'] = '/'.join(trackInfoJSON['track_artists'])
        audioFile['aART']    = '/'.join(trackInfoJSON['album_artists'])
        audioFile['\xa9day'] = trackInfoJSON['year']
        audioFile['trkn']    = [(trackInfoJSON['track_number'], trackInfoJSON['album_length'])]
        audioFile['\xa9cmt'] = 'https://open.spotify.com/track/46qPfZshPjoitCKdKVD6k7/' + trackInfoJSON['track_id']
        audioFile.save()

        print(f'[metadata] Successfully added meta data to track ID: {trackId}.')

    def SearchYoutube(self, keyword, offset, mode, maxResults):
        if keyword != None:
            search = SearchVideos(keyword, offset, mode, maxResults)
            return Response(search.result(), headers = {'Content-Type' : 'application/json'}, status = 200)
        else:
            return make_response('bad request', 400)

    def TrackDownload(self, trackId, trackName):

        if trackId != None:
            try:
                trackInfo = self.TrackInfo(trackId).json
                print(f'[info] Successfully retrieved metadata of track ID: {trackId}.')       
                artists = ' '.join(trackInfo['album_artists'])
                videoId = self.SearchYoutube('lyrics ' + trackInfo['track_name'].split('(')[0].strip().split('-')[0].strip() + ' ' + artists, 1, 'json', 1).json['search_result'][0]['id']
                
                print(f'[search] Search successful. Video ID: {videoId}.') 

                self.SaveAudio(videoId, trackId)
                self.SaveMetaData(trackInfo)
                audioFile = open(f'{trackId}.m4a', 'rb')
                audioBinary = audioFile.read()
                audioFile.close()
                print(f'[server] Sending audio binary for track ID: {trackId}')
                
                response = make_response(audioBinary, 200)
                response.headers['Content-Length'] = len(audioBinary)
                response.headers['Content-Type'] = 'audio/mp4'
                return response
            except:
                return make_response('internal server error', 500)
        
        elif trackName != None:
            try:
                videoId = self.SearchYoutube(trackName, 1, 'json', 1).json['search_result'][0]['id']
                self.SaveAudio(videoId, 'generic')
                audioBinary = open('generic.m4a', 'rb').read()
                os.remove(os.path.join(os.path.dirname, 'generic.m4a'))
                response = make_response(audioBinary, 200)
                response.headers['Content-Length'] = len(audioBinary)
                response.headers['Content-Type'] = 'audio/mp4'
            except:
                return make_response('internal server error', 500)
        else:
            return make_response('bad request', 400)