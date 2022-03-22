import unittest

from m3u8.parse import Parser

from . import playlist


class TestParse(unittest.TestCase):

    def test_parse_simple(self):
        parser = Parser(playlist.SIMPLE)
        parser.parse()

    def test_parse_live(self):
        parser = Parser(playlist.LIVE)
        parser.parse()

    def test_parse_encrypted(self):
        parser = Parser(playlist.ENCRYPTED)
        parser.parse()

    def test_parse_master(self):
        parser = Parser(playlist.MASTER)
        parser.parse()


if __name__ == '__main__':
    unittest.main()
