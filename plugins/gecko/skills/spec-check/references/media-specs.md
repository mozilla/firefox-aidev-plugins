# Media spec catalog for spec-check

Read this file when the question is about media: media elements, text tracks and
subtitles, autoplay, audio sessions, MSE, EME, WebCodecs, media capture, Web Audio,
WebRTC, or a codec, container or protocol.

## HTML Standard: media elements

- HTMLMediaElement, HTMLVideoElement, HTMLAudioElement: load, play, pause, seeking,
  loop. Chapter: https://html.spec.whatwg.org/multipage/media.html
- Append the section anchor, for example `media.html#seeking`, `#dom-media-seekable`
  or `#event-media-timeupdate`.
- Text tracks (`<track>`, `TextTrack`, cues): `media.html#timed-text-tracks`.

## WebVTT
- **WebVTT**: https://w3c.github.io/webvtt/
  - The WebVTT file format, cue parsing, cue settings and cue rendering

## W3C Media Working Group specs
- **Media Source Extensions (MSE)**: https://w3c.github.io/media-source/
  - MediaSource, SourceBuffer APIs for adaptive streaming

- **Encrypted Media Extensions (EME)**: https://w3c.github.io/encrypted-media/
  - MediaKeys, MediaKeySession for protected content playback

- **Media Capabilities**: https://w3c.github.io/media-capabilities/
  - MediaCapabilities API for querying device capabilities

- **Media Session**: https://w3c.github.io/mediasession/
  - MediaSession API for media playback control and metadata

- **Picture-in-Picture**: https://w3c.github.io/picture-in-picture/
  - Picture-in-Picture API for floating video windows

- **WebCodecs**: https://w3c.github.io/webcodecs/
  - Low-level codec interfaces (VideoDecoder, VideoEncoder, AudioDecoder, AudioEncoder)

- **Media Playback Quality**: https://w3c.github.io/media-playback-quality/
  - VideoPlaybackQuality metrics

- **Autoplay Policy Detection**: https://w3c.github.io/autoplay/
  - Autoplay policy detection API

- **Audio Session**: https://w3c.github.io/audio-session/
  - Audio session management

## Media capture specs
- **Media Capture from DOM Elements**: https://w3c.github.io/mediacapture-fromelement/
  - captureStream() for canvas and media elements

- **Media Capture and Streams**: https://w3c.github.io/mediacapture-main/
  - getUserMedia, MediaStream, MediaStreamTrack

- **Screen Capture**: https://w3c.github.io/mediacapture-screen-share/
  - getDisplayMedia for screen/window capture

## Web Audio
- **Web Audio API**: https://webaudio.github.io/web-audio-api/
  - AudioContext, AudioNode, audio processing

## WebRTC
- **WebRTC**: https://w3c.github.io/webrtc-pc/
  - RTCPeerConnection, RTCDataChannel
  - Real-time communication

## Codec, container and protocol specs

Use these when the question involves codec fields, NAL units, SEI payloads, container box formats, or protocol message structure — even for patches with no web-visible behaviour change.

### H.265 / HEVC (ITU-T H.265)
- **Entry point**: https://www.itu.int/rec/T-REC-H.265/en
  - SEI payload types: **Annex D, Table D.1** (`payloadType` integer → semantic name)
  - NAL unit types: **Table 7-1** (nal_unit_type values)
  - PREFIX_SEI_NUT: nal_unit_type = 39 (0x27)
  - user_data_unregistered: payloadType = **5** (Table D.1)
  - Emulation-prevention byte (0x03) rules: **Section 7.4.1**
  - hvcC box SEI rules: see ISO 14496-15

### H.264 / AVC (ITU-T H.264)
- **Entry point**: https://www.itu.int/rec/T-REC-H.264/en
  - SEI payload types: **Annex D, Table D-1**
  - user_data_unregistered: payloadType = **5** (same as H.265)
  - NAL unit types: **Table 7-1**
  - Emulation-prevention byte rules: **Section 7.4.1**

### ISOBMFF / MP4 (ISO/IEC 14496-12) and Codec Mappings (ISO/IEC 14496-15)
- ISO specs are paywalled; use publicly available drafts via WebSearch:
  ```
  WebSearch: "ISO 14496-15 hvcC box SEI site:github.com OR site:mpeg.chiariglione.org"
  ```
  - hvcC box: stores HEVC decoder config including pre-stream NALUs (SPS, PPS, VPS, SEI)
  - Which NAL types are valid in hvcC: **ISO 14496-15, Section 8.3.3.1**

### VP8 (RFC 6386)
- https://datatracker.ietf.org/doc/html/rfc6386
  - Bitstream format and frame header fields

### VP9
- WebM Project spec: https://www.webmproject.org/vp9/
- Codec spec (publicly available): search via WebSearch for "VP9 bitstream specification"

### Opus (RFC 6716)
- https://datatracker.ietf.org/doc/html/rfc6716
  - Codec framing and packet structure

### FLAC (RFC 9639)
- https://datatracker.ietf.org/doc/html/rfc9639

### HLS (RFC 8216)
- https://datatracker.ietf.org/doc/html/rfc8216
  - M3U8 playlist format, segment packaging

### WebM / Matroska
- https://www.matroska.org/technical/elements.html
  - Container element definitions

### RTP (RFC 3550) and RTP payload formats
- https://datatracker.ietf.org/doc/html/rfc3550
  - RTP H.264 payload: RFC 6184
  - RTP H.265 payload: RFC 7798
  - RTP Opus payload: RFC 7587

## WPT directories

- `testing/web-platform/tests/html/semantics/embedded-content/media-elements/`
- `testing/web-platform/tests/media-source/`
- `testing/web-platform/tests/encrypted-media/`
- `testing/web-platform/tests/media-capabilities/`
- `testing/web-platform/tests/mediasession/`
- `testing/web-platform/tests/picture-in-picture/`
- `testing/web-platform/tests/webcodecs/`
- `testing/web-platform/tests/mediacapture-streams/`
- `testing/web-platform/tests/mediacapture-fromelement/`
- `testing/web-platform/tests/screen-capture/`
- `testing/web-platform/tests/webaudio/`
- `testing/web-platform/tests/webrtc/`
- `testing/web-platform/tests/audio-session/`
- `testing/web-platform/tests/autoplay-policy-detection/`
- `testing/web-platform/tests/webvtt/` (`parsing/`, `rendering/` and `api/`)
