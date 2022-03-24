from typing import Any, Dict, List, Optional, Tuple

from . import component
from . import constant
from . import tag
from . import util
from .error import ParseError


class ParserMeta(type):

    def __new__(cls, name: str, bases: Tuple, attrs: Dict[str, Any]):
        c = super().__new__(cls, name, bases, attrs)
        c._tag_parsers = {}
        tag_parser_prefix = '_parse_tag_'
        for k, v in attrs.items():
            if k.startswith(tag_parser_prefix) and callable(v):
                c._tag_parsers[k[len(tag_parser_prefix):]] = v
        return c


class Parser(object, metaclass=ParserMeta):

    def __init__(self, content: str):
        self.content = content

        self.playlist_type: Optional[constant.PlaylistType] = None

        self.version: Optional[tag.Version] = None

        self.keys: List[tag.Key] = []

        self.target_duration: Optional[tag.TargetDuration] = None
        self.media_sequence: Optional[tag.MediaSequence] = None
        self.discontinuity_sequence: Optional[tag.DiscontinuitySequence] = None
        self.end_list: Optional[tag.EndList] = None
        self.media_playlist_type: Optional[tag.PlaylistType] = None
        self.i_frames_only: Optional[tag.IFramesOnly] = None

        self.medias: List[tag.Media] = []
        self.stream_infs: List[tag.StreamInf] = []
        self.current_stream_inf: Optional[tag.StreamInf] = None
        self.variant_streams: List[component.VariantStream] = []
        self.i_frame_stream_infs: List[tag.IFrameStreamInf] = []
        self.session_datas: List[tag.SessionData] = []
        self.session_keys: List[tag.SessionKey] = []

        self.independent_segments: Optional[tag.IndependentSegments] = None
        self.start: Optional[tag.Start] = None

    @staticmethod
    def _has_tag(line: str, name: str) -> bool:
        return line == name or line.startswith(name + ':')

    def _check_playlist_type(self,
                             playlist_type: Optional[constant.PlaylistType]):
        if playlist_type is None:
            return
        if self.playlist_type is None:
            self.playlist_type = playlist_type
        else:
            if self.playlist_type != playlist_type:
                print(self.playlist_type, playlist_type)
                raise ParseError('Mixed playlist type')

    def _check_unique(self, name: str):
        if getattr(self, name, None) is not None:
            name = name.replace('_', ' ')
            raise ParseError(f'Duplicated {name}')

    def _parse_tag_version(self, line: str):
        if self.version is not None:
            raise ParseError('Duplicated version')
        self.version = tag.Version.loads(line)

    def _parse_tag_ext_inf(self, line: str):
        ...  # TODO

    def _parse_tag_byte_range(self, line: str):
        ...  # TODO

    def _parse_tag_discontinuity(self, line: str):
        ...  # TODO

    def _parse_tag_key(self, line: str):
        self.keys.append(tag.Key.loads(line))

    def _parse_tag_map(self, line: str):
        ...  # TODO

    def _parse_tag_program_date_time(self, line: str):
        ...  # TODO

    def _parse_tag_date_range(self, line: str):
        ...  # TODO

    def _parse_tag_target_duration(self, line: str):
        self._check_unique('target_duration')
        self.target_duration = tag.TargetDuration.loads(line)

    def _parse_tag_media_sequence(self, line: str):
        self._check_unique('media_sequence')
        self.media_sequence = tag.MediaSequence.loads(line)

    def _parse_tag_discontinuity_sequence(self, line: str):
        self._check_unique('discontinuity_sequence')
        self.discontinuity_sequence = tag.DiscontinuitySequence.loads(line)

    def _parse_tag_end_list(self, line: str):
        self._check_unique('end_list')
        self.end_list = tag.EndList.loads(line)

    def _parse_tag_playlist_type(self, line: str):
        self._check_unique('media_playlist_type')
        self.media_playlist_type = tag.PlaylistType.loads(line)

    def _parse_tag_i_frames_only(self, line: str):
        self._check_unique('i_frames_only')
        self.i_frames_only = tag.IFramesOnly.loads(line)

    def _parse_tag_media(self, line: str):
        media = tag.Media.loads(line)
        self.medias.append(media)

    def _parse_tag_stream_inf(self, line: str):
        stream_inf = tag.StreamInf.loads(line)
        self.stream_infs.append(stream_inf)

    def _parse_tag_i_frame_stream_inf(self, line: str):
        i_frame_stream_inf = tag.IFrameStreamInf.loads(line)
        self.i_frame_stream_infs.append(i_frame_stream_inf)

    def _parse_tag_session_data(self, line: str):
        session_data = tag.SessionData.loads(line)
        for s in self.session_datas:
            if (session_data.data_id == s.data_id and
                    session_data.language == s.language):
                raise ParseError('Duplicated SESSION-DATA')
        self.session_datas.append(session_data)

    def _parse_tag_session_key(self, line: str):
        session_key = tag.SessionKey.loads(line)
        if session_key in self.session_keys:
            raise ParseError('Duplicated SESSION-KEY')
        self.session_keys.append(session_key)

    def _parse_tag_independent_segments(self, line: str):
        self._check_unique('independent_segments')
        self.independent_segments = tag.IndependentSegments.loads(line)

    def _parse_tag_start(self, line: str):
        self._check_unique('start')
        self.start = tag.Start.loads(line)

    def parse(self):
        lines = [r.strip() for r in self.content.splitlines()]
        lines = [r for r in lines if r]

        if not lines:
            raise ParseError('Empty input')
        if lines[0] != constant.EXTM3U:
            raise ParseError('Unknown file type')

        for line in lines[1:]:
            if line.startswith('#') and not line.startswith('#EXT'):
                continue

            line_parsed = False
            for t in tag.all_tags:
                if self._has_tag(line, t.name):
                    k = util.camel_to_snake(t.__name__)
                    if k not in self._tag_parsers:
                        raise ParseError(f'Unknown parse for {t.name}')
                    self._check_playlist_type(t.playlist_type)
                    self._tag_parsers[k](self, line)
                    line_parsed = True
                    break

            if not line_parsed:
                if self.current_stream_inf is not None:
                    self.variant_streams.append(
                        component.VariantStream(self.current_stream_inf, line))
                    self.current_stream_inf = None
                else:
                    ...
                    # raise ParseError('Unknown line')

        if self.playlist_type == constant.PlaylistType.MEDIA:
            ...
        elif self.playlist_type == constant.PlaylistType.MASTER:
            ...
        else:
            raise ParseError('Unknown playlist type')

        if self.current_stream_inf is not None:
            raise ParseError('Missing URI for STREAM-INF')
        # TODO: Build VariantStream and RenditionGroup from medias
