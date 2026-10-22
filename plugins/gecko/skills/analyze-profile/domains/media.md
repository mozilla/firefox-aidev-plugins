# Media domain pack for analyze-profile

Read this file when the symptom or the profile involves media playback: `<video>`,
`<audio>`, MSE, EME, WebAudio or WebRTC, or threads such as
`MediaDecoderStateMachine`, `MediaSupervisor`, `MediaPDecoder` or `AudioSink`.

## Threads

**Never analyze only one thread.** The media pipeline spans multiple thread types.
After running the standard query set, explicitly account for every thread class:

| Thread pattern                | Role                                                |
|-------------------------------|-----------------------------------------------------|
| `GeckoMain`                   | Main thread — WMF init logs, global state dumps     |
| `MediaDecoderStateMachine #N` | MDSM — playback state, buffering decisions          |
| `MediaSupervisor #N`          | GPU-process decoder supervision — DXVA init/failure |
| `MediaPDecoder #N`            | Decoder threads — per-decoder decode loop           |
| `AudioSink #N`                | Audio output — clock, underruns                     |
| `BackgroundThreadPool #N`     | Demux, network reads                                |

If findings appear only in `MediaDecoderStateMachine #1`, explicitly check whether
`MediaSupervisor`, `MediaPDecoder`, and `GeckoMain` threads contain relevant markers
before concluding. Missing a thread = missing the root cause.

## In-tree media docs

`dom/media/docs/` in the Firefox tree documents media classes and the rules of the
media code. Before you read the code of a component that appears in the profile, check
whether it has a page there, for example `MediaFormatReader.md` or `AudioStream.md`.
The `review/` pages describe the threading, IPC and async lifecycle rules. The docs are
published at https://firefox-source-docs.mozilla.org/media/index.html.

## Targeted marker searches

Run these on the media threads and on the `GeckoMain` thread of the content process
that plays the media, all via
`profiler-cli thread markers --session <id> --thread t-N --search "<term>"`. A search
that finds nothing is still a result: list it as not detected.

| Symptom                     | Search term         |
|-----------------------------|---------------------|
| Buffering / stall           | `waiting`           |
| Video freeze / black screen | `blank media`       |
| Audio desync / dropout      | `Dropping audio`    |
| Audio clock fallback        | `system clock`      |
| MDSM state transitions      | `MDSM::StateChange` |
| Hardware decode failure     | `DXVA`              |
| Codec / decoder errors      | `NS_ERROR`          |
| HEVC / codec probe          | `METADATA`          |
| MSE / demux issues          | `MediaSource`       |
| Frame delivery / copy-out   | `CopyDecodedVideo`  |
| DirectComposition overlay   | `DCSurfaceVideo`    |

Run the searches that match the symptom. If the symptom is unknown or general, run
all of them.

## Signatures

Signals that quote log text only appear when the profile was captured with that MOZ_LOG
module enabled. If the profile has no log markers,
say so instead of reporting the signal as not detected.

### DXVA slot exhaustion
- Signal: `DXVA failure: D3D11:` repeating across `MediaSupervisor #N` threads, one per video
- Confirm: also check for `WMFInit DXVA Status` on `GeckoMain` showing `sDXVAEnabled`
- Meaning: `media.wmf.dxva.max-videos` (default 8) exceeded; feed-style site keeping too many decoders alive

### No-SW-fallback codec failure
- Signal: `NS_ERROR_DOM_MEDIA_METADATA_ERR` or `NS_ERROR_DOM_MEDIA_FATAL_ERR` for HEVC/VP9/AV1/VP8
- Meaning: HW decode failed and no software fallback exists; site had to retry with different codec

### Video suspended (blank media)
- Signal: `blank media data decoder` repeating in MDSM thread
- Meaning: video element backgrounded or tab hidden; decoder suspended by `MediaDecoderStateMachine`

### Audio clock drift / loop gap
- Signal: `Dropping audio packets` log markers from `AudioSinkWrapper` on the
  `MediaDecoderStateMachine` thread (needs `AudioSinkWrapper:5` in MOZ_LOG), or
  `Dropping audio [` from `DecodedStream` for a captureStream or MediaStream output
  (needs `MediaDecoder:4`)
- Meaning: audio sink clock diverged from video PTS; often caused by loop boundary gap or MSE discontinuity

### Audio clock fallback
- Signal: `Getting position from the system clock` log markers from `AudioSinkWrapper`
  on the `MediaDecoderStateMachine` thread (needs `AudioSinkWrapper:5` in MOZ_LOG)
- Meaning: the audio stream has not started or stopped, so the clock runs on the system
  clock; A/V sync accuracy degrades

### MSE stall / demux failure
- Signal: `NS_ERROR_DOM_MEDIA_WAITING_FOR_DATA` in MDSM thread
- Meaning: MSE buffer ran dry; network or append-rate issue

### MDSM buffering state
- Signal: an `MDSM::StateChange` marker with the text `BUFFERING`, without a later
  `MDSM::StateChange` to any other state within a few seconds. A change to
  `SEEKING`, `COMPLETED` or `SHUTDOWN` also ends buffering
- Meaning: decoder starved; look for network issue or demux failure upstream
