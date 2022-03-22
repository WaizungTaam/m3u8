from typing import Optional, Type, TypeVar

from .parser import Parser
from . import constant


class PlaylistError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


P = TypeVar('P', bound='Playlist')


class Playlist(object):
    """HLS M3U8 Playlist
    """

    def __init__(self, version: Optional[int]):
        self.version = version

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


class MediaPlaylist(Playlist):
    """HLS M3U8 Media Playlist
    """

    @classmethod
    def _from_parser(cls, parser: Parser) -> 'MediaPlaylist':
        if parser.playlist_type != constant.PlaylistType.MEDIA:
            raise PlaylistError('Playlist type MEDIA required')
        obj = MediaPlaylist()
        # TODO
        return obj


class MasterPlaylist(Playlist):
    """HLS M3U8 Master Playlist
    """

    @classmethod
    def _from_parser(cls, parser: Parser) -> 'MasterPlaylist':
        if parser.playlist_type != constant.PlaylistType.MASTER:
            raise PlaylistError('Playlist type MASTER required')
        obj = MasterPlaylist()
        # TODO
        return obj
