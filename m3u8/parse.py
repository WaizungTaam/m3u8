from typing import Optional, Any, Dict, List, Tuple

from . import constant


class ParseError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Parser(object):

    def __init__(self, content: str):
        self.content: str = content

        self.version: Optional[int] = None
        self.segments: List[Tuple[float, str, str]] = []
        self.current_segment: Optional[Tuple[float, str]] = None
        self.target_duration: Optional[int] = None
        self.endlist: bool = False
        self.encryption: Optional[Dict[str, Any]] = None
        self.media_sequence: int = 0
        self.playlist_type: Optional[constant.PlaylistType] = None
        self.medias: List[Dict[str, Any]] = []
        self.sessions: List[Dict[str, Any]] = []
        self.independent: bool = False
        self.start: Optional[Dict[str, Any]] = None

    @staticmethod
    def _has_tag(line: str, tag: str) -> bool:
        return line == tag or line.startswith(tag + ':')

    @staticmethod
    def _extract(line: str, tag: str) -> str:
        return line[len(tag)+1:].strip()

    @staticmethod
    def _convert_value(s: str, t: type) -> Any:
        if t is str and len(s) >= 2 and s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        try:
            ret = t(s)
        except Exception:
            return ParseError(f'Invalid {t.__name__}: "{s}"')
        else:
            return ret

    @staticmethod
    def _convert_list(s: str, lt: List[type]) -> List[Any]:
        values = [p.strip() for p in s.split(',')]
        for i in range(min(len(values), len(lt))):
            values[i] = Parser._convert_value(values[i], lt[i])
        return values

    @staticmethod
    def _convert_dict(s: str, kt: Dict[str, type]) -> Dict[str, Any]:
        values = {}
        for p in s.split(','):
            kv = p.split('=', 1)
            if len(kv) != 2:
                raise ParseError('Invalid key-value')
            k, v = kv
            values[k] = Parser._convert_value(v, kt[k]) if k in kt else v
        return values

    @staticmethod
    def _require(d: Dict[str, Any], k: str, tag: str):
        if k not in d:
            raise ParseError(f'Missing {k} for {tag}')

    def _parse_ext_x_version(self, line: str, tag: str):
        if self.version is not None:
            raise ParseError('Duplicated version')
        self.version = self._convert_value(self._extract(line, tag), int)
        # TODO: validate min version
        #       https://datatracker.ietf.org/doc/html/rfc8216#section-7

    def _parse_extinf(self, line: str, tag: str):
        if self.current_segment is not None:
            raise ParseError('Invalid media segment')
        if self.endlist:
            return
        v = self._convert_list(self._extract(line, tag), [float, str])
        if len(v) < 1:
            raise ParseError(f'Missing duration for {tag}')
        duration = v[0]
        title = v[1] if len(v) > 1 else ''
        self.current_segment = (duration, title)

    def _parse_ext_x_byterange(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_discontinuity(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_key(self, line: str, tag: str):
        v = self._convert_dict(self._extract(line, tag), {
            'METHOD': constant.EncryptionMethod,
            'URI': str,
            'IV': int,
            'KEYFORMAT': str,
            'KEYFORMATVERSIONS': str,
        })
        self._require(v, 'METHOD', tag)
        if v['METHOD'] == constant.EncryptionMethod.NONE:
            if len(v) > 1:
                raise ParseError('Unknown attributes for NONE encryption')
            return
        self._require(v, 'URI', tag)
        self.encryption = v
        # TODO: Possible multiple x-keys?

    def _parse_ext_x_map(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_program_date_time(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_daterange(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_targetduration(self, line: str, tag: str):
        if self.target_duration is not None:
            raise ParseError('Duplicated target duration')
        v = self._extract(line, tag)
        self.target_duration = self._convert_value(v, int)

    def _parse_ext_x_media_sequence(self, line: str, tag: str):
        if len(self.segments) > 0 or self.current_segment is not None:
            raise ParseError('Media sequence in wrong place')
        v = self._extract(line, tag)
        self.media_sequence = self._convert_value(v, int)

    def _parse_ext_x_discontinuity_sequence(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_endlist(self, line: str, tag: str):
        self.endlist = True

    def _parse_ext_x_playlist_type(self, line: str, tag: str):
        v = self._extract(line, tag)
        self.playlist_type = self._convert_value(v, constant.PlaylistType)

    def _parse_ext_x_i_frames_only(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_media(self, line: str, tag: str):
        v = self._convert_dict(self._extract(line, tag), {
            'TYPE': constant.MediaType,
            'URI': str,
            'GROUP-ID': str,
            'LANGUAGE': str,
            'ASSOC-LANGUAGE': str,
            'NAME': str,
            'DEFAULT': constant.YesNo,
            'AUTOSELECT': constant.YesNo,
            'FORCED': constant.YesNo,
            'INSTREAM-ID': str,
            'CHARACTERISTICS': str,
            'CHANNELS': str,
        })
        self._require(v, 'TYPE', tag)
        self._require(v, 'GROUP-ID', tag)
        self._require(v, 'NAME', tag)
        if v['TYPE'] == constant.MediaType.CLOSED_CAPTIONS:
            if 'URI' in v:
                raise ParseError('Unknown URI for CLOSED-CAPTIONS')
            if 'INSTREAM-ID' not in v:
                raise ParseError('Missing INSTREAM-ID for CLOSED-CAPTIONS')
        else:
            if 'INSTREAM-ID' in v:
                raise ParseError('Unknown INSTREAM-ID')
        self.medias.append(v)

    def _parse_ext_x_stream_inf(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_i_frame_stream_inf(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_session_data(self, line: str, tag: str):
        v = self._convert_dict(self._extract(line, tag), {
            'DATA-ID': str,
            'VALUE': str,
            'URI': str,
            'LANGUAGE': str,
        })
        self._require(v, 'DATA-ID', tag)
        if 'VALUE' not in v and 'URI' not in v:
            raise ParseError(f'Missing VALUE or URI for {tag}')
        if 'VALUE' in v and 'URI' in v:
            raise ParseError(f'Cannot have both VALUE and URI for {tag}')
        self.sessions.append(v)

    def _parse_ext_x_session_key(self, line: str, tag: str):
        pass  # TODO

    def _parse_ext_x_independent_segments(self, line: str, tag: str):
        self.independent = True

    def _parse_ext_x_start(self, line: str, tag: str):
        v = self._convert_dict(self._extract(line, tag), {
            'TIME-OFFSET': float,
            'PRECISE': constant.YesNo,
        })
        self._require(v, 'TIME-OFFSET', tag)
        self.start = v

    def parse(self):
        lines = [r.strip() for r in self.content.splitlines()]

        if not lines:
            raise ParseError('Empty input')
        if lines[0] != constant.EXTM3U:
            raise ParseError('Invalid first line')

        parse_funcs = {
            constant.EXT_X_VERSION: self._parse_ext_x_version,

            constant.EXTINF: self._parse_extinf,
            constant.EXT_X_BYTERANGE: self._parse_ext_x_byterange,
            constant.EXT_X_DISCONTINUITY: self._parse_ext_x_discontinuity,
            constant.EXT_X_KEY: self._parse_ext_x_key,
            constant.EXT_X_MAP: self._parse_ext_x_map,
            constant.EXT_X_PROGRAM_DATE_TIME:
                self._parse_ext_x_program_date_time,
            constant.EXT_X_DATERANGE: self._parse_ext_x_daterange,

            constant.EXT_X_TARGETDURATION: self._parse_ext_x_targetduration,
            constant.EXT_X_MEDIA_SEQUENCE: self._parse_ext_x_media_sequence,
            constant.EXT_X_DISCONTINUITY_SEQUENCE:
                self._parse_ext_x_discontinuity_sequence,
            constant.EXT_X_ENDLIST: self._parse_ext_x_endlist,
            constant.EXT_X_PLAYLIST_TYPE: self._parse_ext_x_playlist_type,
            constant.EXT_X_I_FRAMES_ONLY: self._parse_ext_x_i_frames_only,

            constant.EXT_X_MEDIA: self._parse_ext_x_media,
            constant.EXT_X_STREAM_INF: self._parse_ext_x_stream_inf,
            constant.EXT_X_I_FRAME_STREAM_INF:
                self._parse_ext_x_i_frame_stream_inf,
            constant.EXT_X_SESSION_DATA: self._parse_ext_x_session_data,
            constant.EXT_X_SESSION_KEY: self._parse_ext_x_session_key,

            constant.EXT_X_INDEPENDENT_SEGMENTS:
                self._parse_ext_x_independent_segments,
            constant.EXT_X_START: self._parse_ext_x_start,
        }

        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#') and not line.startswith('#EXT'):
                continue

            parsed = False
            for tag, func in parse_funcs.items():
                if self._has_tag(line, tag):
                    func(line, tag)
                    parsed = True
                    break

            if not parsed:
                if self.endlist:
                    continue
                if self.current_segment is None:
                    raise ParseError('Unknown line')
                duration, title = self.current_segment
                self.segments.append((duration, title, line))
                self.current_segment = None

        if self.current_segment is not None:
            raise ParseError('Unknown media segment')
        if self.version is None:
            raise ParseError('Missing version')
        if self.target_duration is None:
            raise ParseError('Missing target duration')
        for duration, _, _ in self.segments:
            if round(duration) > self.target_duration:
                raise ParseError('Media segment too long: '
                                 f'{duration} > {self.target_duration}')
