from typing import List, Optional

from . import constant
from . import tag


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
