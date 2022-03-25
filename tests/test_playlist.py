import unittest

from m3u8.playlist import MediaPlaylist

from . import playlist as test_playlist


class TestMediaPlaylist(unittest.TestCase):

    def test_from_str(self):
        p = MediaPlaylist.from_str(test_playlist.SIMPLE)
        self.assertEqual(len(p.media_segments), 3)
