from enum import Enum


# Basic Tags
EXTM3U = '#EXTM3U'
EXT_X_VERSION = '#EXT-X-VERSION'

# Media Segment Tags
EXTINF = '#EXTINF'
EXT_X_BYTERANGE = '#EXT-X-BYTERANGE'
EXT_X_DISCONTINUITY = '#EXT-X-DISCONTINUITY'
EXT_X_KEY = '#EXT-X-KEY'
EXT_X_MAP = '#EXT-X-MAP'
EXT_X_PROGRAM_DATE_TIME = '#EXT-X-PROGRAM-DATE-TIME'
EXT_X_DATERANGE = '#EXT-X-DATERANGE'

# Media Playlist Tags
EXT_X_TARGETDURATION = '#EXT-X-TARGETDURATION'
EXT_X_MEDIA_SEQUENCE = '#EXT-X-MEDIA-SEQUENCE'
EXT_X_DISCONTINUITY_SEQUENCE = '#EXT-X-DISCONTINUITY-SEQUENCE'
EXT_X_ENDLIST = '#EXT-X-ENDLIST'
EXT_X_PLAYLIST_TYPE = '#EXT-X-PLAYLIST-TYPE'
EXT_X_I_FRAMES_ONLY = '#EXT-X-I-FRAMES-ONLY'

# Master Playlist Tags
EXT_X_MEDIA = '#EXT-X-MEDIA'
EXT_X_STREAM_INF = '#EXT-X-STREAM-INF'
EXT_X_I_FRAME_STREAM_INF = '#EXT-X-I-FRAME-STREAM-INF'
EXT_X_SESSION_DATA = '#EXT-X-SESSION-DATA'
EXT_X_SESSION_KEY = '#EXT-X-SESSION-KEY'

# Media or Master Playlist Tags
EXT_X_INDEPENDENT_SEGMENTS = '#EXT-X-INDEPENDENT-SEGMENTS'
EXT_X_START = '#EXT-X-START'


class PlaylistType(Enum):
    MEDIA = 'MEDIA'
    MASTER = 'MASTER'


class EncryptionMethod(Enum):
    NONE = 'NONE'
    AES_128 = 'AES-128'
    SAMPLE_AES = 'SAMPLE-AES'


class SessionEncryptionMethod(Enum):
    AES_128 = 'AES-128'
    SAMPLE_AES = 'SAMPLE-AES'


class MediaPlaylistType(Enum):
    EVENT = 'EVENT'
    VOD = 'VOD'


class MediaType(Enum):
    AUDIO = 'AUDIO'
    VIDEO = 'VIDEO'
    SUBTITLES = 'SUBTITLES'
    CLOSED_CAPTIONS = 'CLOSED-CAPTIONS'


class YesNo(Enum):
    YES = 'YES'
    NO = 'NO'


class Yes(Enum):
    YES = 'YES'


class HdcpLevel(Enum):
    TYPE_0 = 'TYPE-0'
    NONE = 'NONE'


class Resolution(object):

    def __init__(self, s: str):
        p = s.split('x')
        if len(p) != 2:
            raise ValueError('Invalid resolution')
        w, h = p
        try:
            width = int(w)
            height = int(h)
        except ValueError:
            raise ValueError('Invalid resolution')
        self.width = width
        self.height = height
