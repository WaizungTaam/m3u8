import unittest

from dateutil.parser import isoparse as iso8601_parse

from m3u8 import tag
from m3u8 import constant


class TestVersion(unittest.TestCase):

    def test_loads(self):
        v = tag.Version.loads('#EXT-X-VERSION:2')
        self.assertEqual(v.version, 2)


class TestExtInf(unittest.TestCase):

    def test_loads(self):
        e = tag.ExtInf.loads('#EXTINF:123.4,Test')
        self.assertEqual(e.duration, 123.4)
        self.assertEqual(e.title, 'Test')

        e = tag.ExtInf.loads('#EXTINF:123')
        self.assertEqual(e.duration, 123)
        self.assertIsNone(e.title)


class TestByteRange(unittest.TestCase):

    def test_loads(self):
        b = tag.ByteRange.loads('#EXT-X-BYTERANGE:1234@20')
        self.assertEqual(b.length, 1234)
        self.assertEqual(b.start, 20)

        b = tag.ByteRange.loads('#EXT-X-BYTERANGE:321')
        self.assertEqual(b.length, 321)
        self.assertIsNone(b.start)


class TestDiscontinuity(unittest.TestCase):

    def test_loads(self):
        d = tag.Discontinuity.loads('#EXT-X-DISCONTINUITY')
        self.assertTrue(d.present)


class TestKey(unittest.TestCase):

    def test_loads(self):
        uri = 'https://example.com/key.php'

        k = tag.Key.loads(f'#EXT-X-KEY:METHOD=AES-128,URI="{uri}"')
        self.assertEqual(k.method, constant.EncryptionMethod.AES_128)
        self.assertEqual(k.uri, uri)
        self.assertIsNone(k.iv)
        self.assertIsNone(k.key_format)
        self.assertIsNone(k.key_format_versions)


class TestMap(unittest.TestCase):

    def test_loads(self):
        uri = 'https://example.com/map.php'

        m = tag.Map.loads(f'#EXT-X-MAP:URI="{uri}"')
        self.assertEqual(m.uri, uri)
        self.assertIsNone(m.byte_range)


class TestProgramDateTime(unittest.TestCase):

    def test_loads(self):
        dt = '2010-02-19T14:54:23.031+08:00'
        p = tag.ProgramDateTime.loads(f'#EXT-X-PROGRAM-DATE-TIME:{dt}')
        self.assertEqual(p.date_time, iso8601_parse(dt))


class TestDateRange(unittest.TestCase):

    def test_loads(self):
        d = tag.DateRange.loads(
            '#EXT-X-DATERANGE:ID="splice-6FFFFFF0",START-DATE="2014-03-05T11:'
            '15:00Z",PLANNED-DURATION=59.993')
        self.assertEqual(d.id, 'splice-6FFFFFF0')
        self.assertEqual(d.start_date, iso8601_parse('2014-03-05T11:15:00Z'))
        self.assertEqual(d.planned_duration, 59.993)


class TestTargetDuration(unittest.TestCase):

    def test_loads(self):
        t = tag.TargetDuration.loads('#EXT-X-TARGETDURATION:123')
        self.assertEqual(t.duration, 123)


class TestMediaSequence(unittest.TestCase):

    def test_loads(self):
        m = tag.MediaSequence.loads('#EXT-X-MEDIA-SEQUENCE:1234')
        self.assertEqual(m.number, 1234)


class TestDiscontinuitySequence(unittest.TestCase):

    def test_loads(self):
        d = tag.DiscontinuitySequence.loads(
            '#EXT-X-DISCONTINUITY-SEQUENCE:1234')
        self.assertEqual(d.number, 1234)


class TestEndList(unittest.TestCase):

    def test_loads(self):
        e = tag.EndList.loads('#EXT-X-ENDLIST')
        self.assertTrue(e.present)


class TestPlaylistType(unittest.TestCase):

    def test_loads(self):
        p = tag.PlaylistType.loads('#EXT-X-PLAYLIST-TYPE:EVENT')
        self.assertEqual(p.type, constant.MediaPlaylistType.EVENT)


class TestIFramesOnly(unittest.TestCase):

    def test_loads(self):
        i = tag.IFramesOnly.loads('#EXT-X-I-FRAMES-ONLY')
        self.assertTrue(i.present)


class TestMedia(unittest.TestCase):

    def test_loads(self):
        m = tag.Media.loads(
            '#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="low",NAME="Main",'
            'DEFAULT=YES,URI="low/main/audio-video.m3u8"')
        self.assertEqual(m.type, constant.MediaType.VIDEO)
        self.assertEqual(m.group_id, 'low')
        self.assertEqual(m.name, 'Main')
        self.assertEqual(m.default, constant.YesNo.YES)
        self.assertEqual(m.uri, 'low/main/audio-video.m3u8')


class TestStreamInf(unittest.TestCase):

    def test_loads(self):
        s = tag.StreamInf.loads(
            '#EXT-X-STREAM-INF:BANDWIDTH=1280000,CODECS="ac-3,mp4a.40.2",'
            'VIDEO="low"')
        self.assertEqual(s.bandwidth, 1280000)
        self.assertEqual(s.codecs, 'ac-3,mp4a.40.2')
        self.assertEqual(s.video, 'low')


class TestIFrameStreamInf(unittest.TestCase):

    def test_loads(self):
        i = tag.IFrameStreamInf.loads(
            '#EXT-X-I-FRAME-STREAM-INF:BANDWIDTH=150000,URI="mid/iframe.m3u8"')
        self.assertEqual(i.bandwidth, 150000)
        self.assertEqual(i.uri, 'mid/iframe.m3u8')


class TestSessionData(unittest.TestCase):

    def test_loads(self):
        s = tag.SessionData.loads(
            '#EXT-X-SESSION-DATA:DATA-ID="com.example.title",LANGUAGE="en",'
            'VALUE="This is an example"')
        self.assertEqual(s.data_id, 'com.example.title')
        self.assertEqual(s.language, 'en')
        self.assertEqual(s.value, 'This is an example')


class TestSessionKey(unittest.TestCase):

    def test_loads(self):
        uri = 'https://example.com/key.php'

        s = tag.SessionKey.loads(
            f'#EXT-X-SESSION-KEY:METHOD=AES-128,URI="{uri}"')
        self.assertEqual(s.method, constant.SessionEncryptionMethod.AES_128)
        self.assertEqual(s.uri, uri)


class TestIndependentSegments(unittest.TestCase):

    def test_loads(self):
        i = tag.IndependentSegments.loads('#EXT-X-INDEPENDENT-SEGMENTS')
        self.assertTrue(i.present)


class TestStart(unittest.TestCase):

    def test_loads(self):
        s = tag.Start.loads('#EXT-X-START:TIME-OFFSET=1000,PRECISE=YES')
        self.assertEqual(s.time_offset, 1000)
        self.assertEqual(s.precise, constant.YesNo.YES)
