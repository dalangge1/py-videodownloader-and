__license__ = '''
Copyright 2010 Jake Wharton

py-video-downloader is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.

py-video-downloader is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY
 without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General
Public License along with py-video-downloader.  If not, see
<http://www.gnu.org/licenses/>.
'''

from videodownloader.providers import Provider
import re
import urllib
import urlparse

parse_params = lambda x: urlparse.parse_qs(urllib.unquote(x))

class YouTube(Provider):
    FORMAT_PRIORITY = ['37', '22', '45', '44', '35', '43', '18', '34', '5']
    FORMATS = {
        '5' : '320x240 H.263/MP3 Mono FLV',
        '13': '176x144 3GP/AMR Mono 3GP',
        '17': '176x144 3GP/AAC Mono 3GP',
        '18': '480x360/480x270 H.264/AAC Stereo MP4',
        '22': '1280x720 H.264/AAC Stereo MP4',
        '34': '320x240 H.264/AAC Stereo FLV',
        '35': '640x480/640x360 H.264/AAC Stereo FLV',
        '37': '1920x1080 H.264/AAC Stereo MP4',
        '43': '640x360 VP8/Vorbis Stereo MP4',
        '44': '854x480 VP8/Vorbis Stereo MP4',
        '45': '1280x720 VP8/Vorbis Stereo MP4',
    }

    def __init__(self, id, **kwargs):
        super(YouTube, self).__init__(id, **kwargs)

        #Load video meta information
        url  = 'http://www.youtube.com/get_video_info?video_id=%s' % self.id
        self._debug('YouTube', '__init__', 'Downloading "%s"...' % url)
        self._html = super(YouTube, YouTube)._download(url).read()

        #Get available formats
        self.formats = set()
        for match in re.finditer(r'itag%3D(\d+)', self._html):
            if match.group(1) not in YouTube.FORMATS.keys():
                print 'WARNING: Unknown format "%s" found.' % match.group(1)
            self.formats.add(match.group(1))
        self._debug('YouTube', '__init__', 'formats', ', '.join(self.formats))

        #Get video title if not explicitly set
        if self.title is id:
            match = re.search(r'&title=([^&]+)', self._html, re.DOTALL)
            if match:
                self.title = urllib.unquote_plus(match.group(1))
                self._debug('YouTube', '__init__', 'title', self.title)
        self._debug('YouTube', '__init__', 'title', self.title)

        #Get video filename if not explicity set
        self.filename = self.title if self.filename is None else self.filename
        self._debug('YouTube', '__init__', 'filename', self.filename)

        #Get proper file extension if a valid format was supplied
        if self.format is not None and self.format in YouTube.FORMATS.keys():
            self.fileext = YouTube.FORMATS[self.format][-3:].lower()
            self._debug('YouTube', '__init__', 'fileext', self.fileext)

        #Get magic data needed to download
        self.token = info('token')
        self._debug('YouTube', '__init__', 'token', self.token)

        #Video thumbnail
        self.thumbnail = info('thumbnail_url')
        self._debug('YouTube', '__init__', 'thumbnail', self.thumbnail)

        #Video duration (seconds)
        try:
            self.duration = int(info('length_seconds'))
        except ValueError, KeyError:
            #TODO: warn
            self.duration = -1
        self._debug('YouTube', '__init__', 'duration', self.duration)

        #Other YouTube-specific information
        self.author = info('author')
        self._debug('YouTube', '__init__', 'author', self.author)

        self.keywords = set(info('keywords').split(','))
        self._debug('YouTube', '__init__', 'keywords', ','.join(self.keywords))

        try:
            self.rating = float(info('avg_rating'))
        except ValueError, KeyError:
            #TODO: warn
            self.rating = -1.0
        self._debug('YouTube', '__init__', 'rating', self.rating)


    def get_download_url(self):
        #Validate format
        if self.format is None:
            self.format = self._get_best_format()
        elif self.format not in self.formats:
            raise ValueError('Invalid format "%s". Valid formats are "%s".' % (self.format, '", "'.join(self.formats)))

        #Check extension
        if self.fileext is None or self.fileext == Provider.DEFAULT_EXT:
            self.fileext = YouTube.FORMATS[self.format][-3:].lower()

        url = self.formats[self.format]

        self._debug('YouTube', 'get_download_url', 'url', url)
        return url

    def _get_best_format(self):
        for fmt_id in YouTube.FORMAT_PRIORITY:
            if fmt_id in self.formats and self.formats[fmt_id]:
                self._debug('YouTube', '_get_best_format', 'format', fmt_id)
                return fmt_id
        raise ValueError('Could not determine the best available format. YouTube has likely changed its page layout. Please contact the author of this script.')
