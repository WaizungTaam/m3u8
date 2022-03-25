import os
from typing import List, Optional, Type, TypeVar, Union

import requests

from .parser import Parser
from . import component
from . import constant
from . import tag


class PlaylistError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


P = TypeVar('P', bound='Playlist')


class Playlist(object):
    """HLS M3U8 Playlist
    """

    @classmethod
    def _from_parser(cls: Type[P], parser: Parser) -> P:
        if parser.playlist_type == constant.PlaylistType.MEDIA:
            return MediaPlaylist._from_parser(parser)
        elif parser.playlist_type == constant.PlaylistType.MASTER:
            return MasterPlaylist._from_parser(parser)
        else:
            raise PlaylistError('Unknown playlist type')

    @classmethod
    def from_str(cls: Type[P], s: str) -> P:
        parser = Parser(s)
        parser.parse()
        return cls._from_parser(parser)

    @classmethod
    def from_bytes(cls: Type[P], b: bytes) -> P:
        try:
            s = b.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            raise PlaylistError('Invalid encoding, UTF-8 required')
        return cls._from_str(s)

    @classmethod
    def from_file(cls: Type[P], file: Union[str, bytes, os.PathLike]) -> P:
        with open(file, 'r', encoding='utf-8') as f:
            s = f.read()
        return cls.from_str(s)

    @classmethod
    def from_url(cls, url: str, **kwargs) -> P:
        res = requests.get(url, **kwargs)
        res.raise_for_status()
        return cls.from_bytes(res.content)


class MediaPlaylist(Playlist):
    """HLS M3U8 Media Playlist
    """
    def __init__(
            self,
            version: Optional[tag.Version] = None,
            media_segments: Optional[List[component.MediaSegment]] = None,
            target_duration: Optional[tag.TargetDuration] = None,
            media_sequence: Optional[tag.MediaSequence] = None,
            discontinuity_sequence: Optional[tag.DiscontinuitySequence] = None,
            end_list: Optional[tag.EndList] = None,
            media_playlist_type: Optional[tag.PlaylistType] = None,
            i_frames_only: Optional[tag.IFramesOnly] = None,
            independent_segments: Optional[tag.IndependentSegments] = None,
            start: Optional[tag.Start] = None):
        self.version = version
        self.media_segments = media_segments or []
        self.target_duration = target_duration
        self.media_sequence = media_sequence
        self.discontinuity_sequence = discontinuity_sequence
        self.end_list = end_list
        self.media_playlist_type = media_playlist_type
        self.i_frames_only = i_frames_only
        self.independent_segments = independent_segments
        self.start = start

    @classmethod
    def _from_parser(cls, parser: Parser) -> 'MediaPlaylist':
        if parser.playlist_type != constant.PlaylistType.MEDIA:
            raise PlaylistError('Playlist type MEDIA required')
        return MediaPlaylist(
            version=parser.version,
            media_segments=parser.media_segments,
            target_duration=parser.target_duration,
            media_sequence=parser.media_sequence,
            discontinuity_sequence=parser.discontinuity_sequence,
            end_list=parser.end_list,
            media_playlist_type=parser.media_playlist_type,
            i_frames_only=parser.i_frames_only,
            independent_segments=parser.independent_segments,
            start=parser.start,
        )


class MasterPlaylist(Playlist):
    """HLS M3U8 Master Playlist
    """

    def __init__(
            self,
            version: Optional[tag.Version] = None,
            variant_streams: Optional[List[component.VariantStream]] = None,
            i_frame_stream_infs: Optional[List[tag.IFrameStreamInf]] = None,
            session_datas: Optional[List[tag.SessionData]] = None,
            session_keys: Optional[List[tag.SessionKey]] = None,
            independent_segments: Optional[tag.IndependentSegments] = None,
            start: Optional[tag.Start] = None):
        self.version = version
        self.variant_streams = variant_streams or []
        self.i_frame_stream_infs = i_frame_stream_infs or []
        self.session_datas = session_datas or []
        self.session_keys = session_keys or []
        self.independent_segments = independent_segments
        self.start = start

    @classmethod
    def _from_parser(cls, parser: Parser) -> 'MasterPlaylist':
        if parser.playlist_type != constant.PlaylistType.MASTER:
            raise PlaylistError('Playlist type MASTER required')
        return MasterPlaylist(
            version=parser.version,
            variant_streams=parser.variant_streams,
            i_frame_stream_infs=parser.i_frame_stream_infs,
            session_datas=parser.session_datas,
            session_keys=parser.session_keys,
            independent_segments=parser.independent_segments,
            start=parser.start,
        )
