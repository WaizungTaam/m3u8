# M3U8

**M3U8** is a parser for HTTP Live Streaming (HLS) playlist `.m3u8` files.

The protocol is described in [rfc8216](https://datatracker.ietf.org/doc/html/rfc8216).


## Installing

Install with `pip`:
```console
$ pip install -e git+https://github.com/WaizungTaam/m3u8
```

## Example

```python
from m3u8 import MediaPlaylist


playlist = MediaPlaylist.from_file('index.m3u8')

for segment in playlist.media_segments:
    print(segment.uri)
```


## License

This project is licensed under the terms of the MIT license.


## References
- https://datatracker.ietf.org/doc/html/rfc8216
- https://en.wikipedia.org/wiki/HTTP_Live_Streaming
