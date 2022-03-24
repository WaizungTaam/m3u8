from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from dateutil.parser import isoparse as iso8601_parse

from . import constant
from .error import ParseError


class Attr(object):

    def __init__(self, name: str, attr: str, type: type,
                 required: bool = False):
        self.name = name
        self.attr = attr
        self.type = type
        self.required = required


def unquote(s: str) -> str:
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def convert_value(s: str, attr: Attr) -> Any:
    t = attr.type
    try:
        if t is str:
            return unquote(s)
        elif t is datetime:
            return iso8601_parse(unquote(s))
        else:
            return t(s)
    except Exception:
        raise ParseError(f'Invalid {t.__name__}: {s}')


def convert_list(s: str, attrs: List[Attr]) -> List[Any]:
    values = [p.strip() for p in s.split(',')]
    for i in range(min(len(values), len(attrs))):
        values[i] = convert_value(values[i], attrs[i])
    return values


def split_kv(s: str) -> List[Tuple[str, str]]:
    expect_key = True
    expect_value = False
    quoted = False
    tokens: List[str] = []
    token = ''
    for c in s:
        if expect_key:
            if quoted:
                raise ParseError('Illegal attribute')
            if c == '=':
                tokens.append(token.strip())
                token, expect_key, expect_value = '', False, True
            else:
                if not (c.isupper() or c.isdigit() or c == '-'):
                    raise ParseError('Invalid attribute name')
                token += c
        elif expect_value:
            if quoted:
                if c == '"':
                    quoted = False
                token += c
            else:
                if c == ',':
                    tokens.append(token.strip())
                    token, expect_key, expect_value = '', True, False
                else:
                    if c == '"':
                        quoted = True
                    token += c
    if expect_value:
        tokens.append(token)
    if len(tokens) % 2 != 0:
        raise ParseError('Illegal attribute')
    result: List[Tuple[str, str]] = []
    for i in range(0, len(tokens), 2):
        result.append((tokens[i], tokens[i+1]))
    return result


def convert_dict(s: str, attrs: List[Attr]) -> Dict[str, Any]:
    attr_map = {a.attr: a for a in attrs}
    values: Dict[str, Any] = {}
    for k, v in split_kv(s):
        if k not in attr_map:
            continue
        a = attr_map[k]
        values[a.name] = convert_value(v, a)
    for a in attrs:
        if a.required and a.name not in values:
            raise ParseError(f'Missing {a.attr}')
    return values


class Tag(object):

    name: str = ''
    playlist_type: Optional[constant.PlaylistType] = None
    attrs: List[Attr] = []

    @classmethod
    def _extract(cls, line: str) -> str:
        return line[len(cls.name)+1:].strip()

    @classmethod
    def loads(cls, line: str) -> 'Tag':
        raise NotImplementedError


class Version(Tag):
    name = constant.EXT_X_VERSION
    attrs = [
        Attr('version', 'VERSION', int, required=True),
    ]

    def __init__(self, version: int):
        self.version = version

    @classmethod
    def loads(cls, line: str) -> 'Version':
        return cls(convert_value(cls._extract(line), cls.attrs[0]))


class ExtInf(Tag):
    name = constant.EXTINF
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('duration', 'DURATION', float, required=True),
        Attr('title', 'TITLE', str),
    ]

    def __init__(self, duration: float, title: Optional[str] = None):
        self.duration = duration
        self.title = title

    @classmethod
    def loads(cls, line: str) -> 'ExtInf':
        return cls(*convert_list(cls._extract(line), cls.attrs))


class ByteRange(Tag):
    name = constant.EXT_X_BYTERANGE
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('length', 'LENGTH', int, required=True),
        Attr('start', 'START', int),
    ]

    def __init__(self, length: int, start: Optional[int] = None):
        self.length = length
        self.start = start

    @classmethod
    def loads(cls, line: str) -> 'ByteRange':
        s = cls._extract(line)
        p = s.split('@')
        if len(p) == 1:
            return cls(convert_value(p[0], cls.attrs[0]))
        elif len(p) == 2:
            return cls(convert_value(p[0], cls.attrs[0]),
                       convert_value(p[1], cls.attrs[1]))
        else:
            raise ParseError('Unknown BYTERANGE')


class Discontinuity(Tag):
    name = constant.EXT_X_DISCONTINUITY
    playlist_type = constant.PlaylistType.MEDIA

    def __init__(self, present: bool = False):
        self.present = present

    @classmethod
    def loads(cls, line: str) -> 'Discontinuity':
        return cls(True)


class Key(Tag):
    name = constant.EXT_X_KEY
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('method', 'METHOD', constant.EncryptionMethod, required=True),
        Attr('uri', 'URI', str),
        Attr('iv', 'IV', int),
        Attr('key_format', 'KEYFORMAT', str),
        Attr('key_format_versions', 'KEYFORMATVERSIONS', str),
    ]

    def __init__(self,
                 method: constant.EncryptionMethod,
                 uri: Optional[str] = None,
                 iv: Optional[int] = None,
                 key_format: Optional[str] = None,
                 key_format_versions: Optional[str] = None):
        self.method = method

        if self.method == constant.EncryptionMethod.NONE:
            if not all(v is None for v in [uri, iv, key_format, key_format]):
                raise ParseError('Unknown attributes for NONE encryption')
        else:
            if uri is None:
                raise ParseError(f'Missing URI for {self.method}')

        self.uri = uri
        self.iv = iv
        self.key_format = key_format
        self.key_format_versions = key_format_versions

    @classmethod
    def loads(cls, line: str) -> 'Key':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class Map(Tag):
    name = constant.EXT_X_MAP
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('uri', 'URI', str, required=True),
        Attr('byte_range', 'BYTERANGE', str),
        # TODO: Considser parsing BYTERANGE with lenght[@start]
    ]

    def __init__(self, uri: str, byte_range: Optional[str] = None):
        self.uri = uri
        self.byte_range = byte_range

    @classmethod
    def loads(cls, line: str) -> 'Map':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class ProgramDateTime(Tag):
    name = constant.EXT_X_PROGRAM_DATE_TIME
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('date_time', 'DATETIME', datetime, required=True),
    ]

    def __init__(self, date_time: datetime):
        self.date_time = date_time

    @classmethod
    def loads(cls, line: str) -> 'ProgramDateTime':
        return cls(convert_value(cls._extract(line), cls.attrs[0]))


class DateRange(Tag):
    name = constant.EXT_X_DATERANGE
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('id', 'ID', str, required=True),
        Attr('start_date', 'START-DATE', datetime, required=True),
        Attr('class_', 'CLASS', str),
        Attr('end_date', 'END-DATE', datetime),
        Attr('duration', 'DURATION', float),
        Attr('planned_duration', 'PLANNED-DURATION', float),
        Attr('end_on_next', 'END-ON-NEXT', constant.Yes),
        # TODO: SCTE35 and X-<client-attribute>
    ]

    def __init__(self,
                 id: str,
                 start_date: datetime,
                 class_: Optional[str] = None,
                 end_date: Optional[datetime] = None,
                 duration: Optional[float] = None,
                 planned_duration: Optional[float] = None,
                 end_on_next: Optional[constant.Yes] = None):
        self.id = id
        self.start_date = start_date
        self.class_ = class_
        self.end_date = end_date
        self.duration = duration
        self.planned_duration = planned_duration
        self.end_on_next = end_on_next

        if self.end_on_next == constant.Yes.YES:
            if self.class_ is None:
                raise ParseError('Missing CLASS for END-ON-NEXT=YES')
            if self.duration is not None or self.end_date is not None:
                raise ParseError('Invalid attributes for END-ON-NEXT=YES')
        if self.end_date is not None and self.duration is not None:
            delta = timedelta(seconds=self.duration)
            if self.start_date + delta != self.end_date:
                raise ParseError('Incorrect END-DATE or DURATION')

    @classmethod
    def loads(cls, line: str) -> 'DateRange':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class TargetDuration(Tag):
    name = constant.EXT_X_TARGETDURATION
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('duration', 'DURATION', int, required=True),
    ]

    def __init__(self, duration: int):
        self.duration = duration

    @classmethod
    def loads(cls, line: str) -> 'TargetDuration':
        return cls(convert_value(cls._extract(line), cls.attrs[0]))


class MediaSequence(Tag):
    name = constant.EXT_X_MEDIA_SEQUENCE
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('number', 'NUMBER', int, required=True),
    ]

    def __init__(self, number: int):
        self.number = number

    @classmethod
    def loads(cls, line: str) -> 'MediaSequence':
        return cls(convert_value(cls._extract(line), cls.attrs[0]))


class DiscontinuitySequence(Tag):
    name = constant.EXT_X_DISCONTINUITY_SEQUENCE
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('number', 'NUMBER', int, required=True),
    ]

    def __init__(self, number: int):
        self.number = number

    @classmethod
    def loads(cls, line: str) -> 'DiscontinuitySequence':
        return cls(convert_value(cls._extract(line), cls.attrs[0]))


class EndList(Tag):
    name = constant.EXT_X_ENDLIST
    playlist_type = constant.PlaylistType.MEDIA

    def __init__(self, present: bool = False):
        self.present = present

    @classmethod
    def loads(cls, line: str) -> 'EndList':
        return cls(True)


class PlaylistType(Tag):
    name = constant.EXT_X_PLAYLIST_TYPE
    playlist_type = constant.PlaylistType.MEDIA
    attrs = [
        Attr('type', 'TYPE', constant.MediaPlaylistType, required=True),
    ]

    def __init__(self, type: constant.MediaPlaylistType):
        self.type = type

    @classmethod
    def loads(cls, line: str) -> 'PlaylistType':
        return cls(convert_value(cls._extract(line), cls.attrs[0]))


class IFramesOnly(Tag):
    name = constant.EXT_X_I_FRAMES_ONLY
    playlist_type = constant.PlaylistType.MEDIA

    def __init__(self, present: bool = False):
        self.present = present

    @classmethod
    def loads(cls, line: str) -> 'IFramesOnly':
        return cls(True)


class Media(Tag):
    name = constant.EXT_X_MEDIA
    playlist_type = constant.PlaylistType.MASTER
    attrs = [
        Attr('type', 'TYPE', constant.MediaType, required=True),
        Attr('group_id', 'GROUP-ID', str, required=True),
        Attr('name', 'NAME', str, required=True),
        Attr('uri', 'URI', str),
        Attr('language', 'LANGUAGE', str),
        Attr('assoc_language', 'ASSOC-LANGUAGE', str),
        Attr('default', 'DEFAULT', constant.YesNo),
        Attr('autoselect', 'AUTOSELECT', constant.YesNo),
        Attr('forced', 'FORCED', constant.YesNo),
        Attr('instream_id', 'INSTREAM-ID', str),
        Attr('characteristics', 'CHARACTERISTICS', str),
        Attr('channels', 'CHANNELS', str),
    ]

    def __init__(self,
                 type: constant.MediaType,
                 group_id: str,
                 name: str,
                 uri: Optional[str] = None,
                 language: Optional[str] = None,
                 assoc_language: Optional[str] = None,
                 default: Optional[constant.YesNo] = None,
                 autoselect: Optional[constant.YesNo] = None,
                 forced: Optional[constant.YesNo] = None,
                 instream_id: Optional[str] = None,
                 characteristics: Optional[str] = None,
                 channels: Optional[str] = None):
        self.type = type
        self.group_id = group_id
        self.name = name
        self.uri = uri
        self.language = language
        self.assoc_language = assoc_language
        self.default = default
        self.autoselect = autoselect
        self.forced = forced
        self.instream_id = instream_id
        self.characteristics = characteristics
        self.channels = channels

        if self.type == constant.MediaType.CLOSED_CAPTIONS:
            if self.uri is not None:
                raise ParseError('Unknown URI for CLOSED-CAPTIONS')
            if self.instream_id is None:
                raise ParseError('Missing INSTREAM-ID for CLOSED-CAPTIONS')
        else:
            if self.instream_id is not None:
                raise ParseError('Unknown INSTREAM-ID')

    @classmethod
    def loads(cls, line: str) -> 'Media':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class StreamInf(Tag):
    name = constant.EXT_X_STREAM_INF
    playlist_type = constant.PlaylistType.MASTER
    attrs = [
        Attr('bandwidth', 'BANDWIDTH', int, required=True),
        Attr('average_bandwidth', 'AVERAGE-BANDWIDTH', int),
        Attr('codecs', 'CODECS', str),
        Attr('resolution', 'RESOLUTION', constant.Resolution),
        Attr('frame_rate', 'FRAME-RATE', float),
        Attr('hdcp_level', 'HDCP-LEVEL', constant.HdcpLevel),
        Attr('audio', 'AUDIO', str),
        Attr('video', 'VIDEO', str),
        Attr('subtitles', 'SUBTITLES', str),
        Attr('closed_captions', 'CLOSED-CAPTIONS', str),
    ]

    def __init__(self,
                 bandwidth: int,
                 average_bandwidth: Optional[int] = None,
                 codecs: Optional[str] = None,
                 resolution: Optional[constant.Resolution] = None,
                 frame_rate: Optional[float] = None,
                 hdcp_level: Optional[constant.HdcpLevel] = None,
                 audio: Optional[str] = None,
                 video: Optional[str] = None,
                 subtitles: Optional[str] = None,
                 closed_captions: Optional[str] = None):
        self.bandwidth = bandwidth
        self.average_bandwidth = average_bandwidth
        self.codecs = codecs
        self.resolution = resolution
        self.frame_rate = frame_rate
        self.hdcp_level = hdcp_level
        self.audio = audio
        self.video = video
        self.subtitles = subtitles
        self.closed_captions = closed_captions

    @classmethod
    def loads(cls, line: str) -> 'StreamInf':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class IFrameStreamInf(Tag):
    name = constant.EXT_X_I_FRAME_STREAM_INF
    playlist_type = constant.PlaylistType.MASTER
    attrs = [
        Attr('bandwidth', 'BANDWIDTH', int, required=True),
        Attr('uri', 'URI', str, required=True),
        Attr('average_bandwidth', 'AVERAGE-BANDWIDTH', int),
        Attr('codecs', 'CODECS', str),
        Attr('resolution', 'RESOLUTION', constant.Resolution),
        Attr('hdcp_level', 'HDCP-LEVEL', constant.HdcpLevel),
        Attr('video', 'VIDEO', str),
    ]

    def __init__(self,
                 bandwidth: int,
                 uri: str,
                 average_bandwidth: Optional[int] = None,
                 codecs: Optional[str] = None,
                 resolution: Optional[constant.Resolution] = None,
                 hdcp_level: Optional[constant.HdcpLevel] = None,
                 video: Optional[str] = None):
        self.bandwidth = bandwidth
        self.uri = uri
        self.average_bandwidth = average_bandwidth
        self.codecs = codecs
        self.resolution = resolution
        self.hdcp_level = hdcp_level
        self.video = video

    @classmethod
    def loads(cls, line: str) -> 'IFrameStreamInf':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class SessionData(Tag):
    name = constant.EXT_X_SESSION_DATA
    playlist_type = constant.PlaylistType.MASTER
    attrs = [
        Attr('data_id', 'DATA-ID', str, required=True),
        Attr('value', 'VALUE', str),
        Attr('uri', 'URI', str),
        Attr('language', 'LANGUAGE', str),
    ]

    def __init__(self,
                 data_id: str,
                 value: Optional[str] = None,
                 uri: Optional[str] = None,
                 language: Optional[str] = None):
        self.data_id = data_id
        self.value = value
        self.uri = uri
        self.language = language

        if self.value is None and self.uri is None:
            raise ParseError('Missing VALUE or URI')
        if self.value is not None and self.uri is not None:
            raise ParseError(f'Cannot have both VALUE and URI')

    @classmethod
    def loads(cls, line: str) -> 'SessionData':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class SessionKey(Tag):
    name = constant.EXT_X_SESSION_KEY
    playlist_type = constant.PlaylistType.MASTER
    attrs = [
        Attr('method', 'METHOD', constant.SessionEncryptionMethod,
             required=True),
        Attr('uri', 'URI', str, required=True),
        Attr('iv', 'IV', int),
        Attr('key_format', 'KEYFORMAT', str),
        Attr('key_format_versions', 'KEYFORMATVERSIONS', str),
    ]

    def __init__(self,
                 method: constant.SessionEncryptionMethod,
                 uri: str,
                 iv: Optional[int] = None,
                 key_format: Optional[str] = None,
                 key_format_versions: Optional[str] = None):
        self.method = method
        self.uri = uri
        self.iv = iv
        self.key_format = key_format
        self.key_format_versions = key_format_versions

    @classmethod
    def loads(cls, line: str) -> 'SessionKey':
        return cls(**convert_dict(cls._extract(line), cls.attrs))


class IndependentSegments(Tag):
    name = constant.EXT_X_INDEPENDENT_SEGMENTS

    def __init__(self, present: bool = False):
        self.present = present

    @classmethod
    def loads(cls, line: str) -> 'IndependentSegments':
        return cls(True)


class Start(Tag):
    name = constant.EXT_X_START
    attrs = [
        Attr('time_offset', 'TIME-OFFSET', float, required=True),
        Attr('precise', 'PRECISE', constant.YesNo),
    ]

    def __init__(self, time_offset: float,
                 precise: Optional[constant.YesNo] = None):
        self.time_offset = time_offset
        self.precise = precise

    @classmethod
    def loads(cls, line: str) -> 'Start':
        return cls(**convert_dict(cls._extract(line), cls.attrs))
