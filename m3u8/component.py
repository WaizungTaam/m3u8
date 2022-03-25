from typing import List, Optional

from . import constant
from . import tag


class MediaSegment(object):

    def __init__(self,
                 info: tag.ExtInf,
                 uri: str,
                 byte_range: Optional[tag.ByteRange] = None,
                 discontinuity: Optional[tag.Discontinuity] = None,
                 key: Optional[tag.Key] = None,
                 map: Optional[tag.Map] = None,
                 program_date_time: Optional[tag.ProgramDateTime] = None,
                 date_range: Optional[tag.DateRange] = None):
        self.info = info
        self.uri = uri
        self.byte_range = byte_range
        self.discontinuity = discontinuity
        self.key = key
        self.map = map
        self.program_date_time = program_date_time
        self.date_range = date_range


class RenditionGroup(object):

    def __init__(self,
                 group_id: str,
                 type: constant.MediaType,
                 renditions: Optional[List[tag.Media]] = None):
        self.group_id = group_id
        self.type = type
        self.renditions: List[tag.Media] = renditions or []


class VariantStream(object):

    def __init__(self,
                 info: tag.StreamInf,
                 uri: str,
                 audio: Optional[RenditionGroup] = None,
                 video: Optional[RenditionGroup] = None,
                 subtitles: Optional[RenditionGroup] = None,
                 closed_captions: Optional[RenditionGroup] = None):

        self.info = info
        self.uri = uri
        self.audio = audio
        self.video = video
        self.subtitles = subtitles
        self.closed_captions = closed_captions
