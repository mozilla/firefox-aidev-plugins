# MF Media Engine / EME / CDM / PlayReady Log Patterns

Reference for analyzing logs involving the Windows Media Foundation Media Engine,
Encrypted Media Extensions (EME), CDM utility processes, and PlayReady DRM.

## Key Signals

| Signal                                                               | Meaning                                                                                                                                                        |
|----------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `MF_MEDIA_ENGINE_EVENT_ERROR`                                        | Media Foundation engine reported an error event                                                                                                                |
| `hardware reset error, hr=`                                          | GPU/hardware device loss with HRESULT code                                                                                                                     |
| `OnHardwareContextReset`                                             | GPU context reset received by CDM proxy                                                                                                                        |
| `Received hardware reset`                                            | Content process notified of hardware reset                                                                                                                     |
| `MFCDMProxy`                                                         | CDM proxy lifecycle messages                                                                                                                                   |
| `MFMediaEngineWrapper` / `MFMediaEngineParent`                       | MF engine wrapper/parent lifecycle                                                                                                                             |
| `CDM setup` / `CDM failed` / `CDM error`                             | CDM initialization failures                                                                                                                                    |
| `E_ABORT` / `0x80004004`                                             | Abort propagation through MF pipeline                                                                                                                          |
| `MF_E_SHUTDOWN` / `0xC00D3E85`                                       | MF object used after shutdown                                                                                                                                  |
| `Destroyed actor without shutdown` on an MFMediaEngine-related actor | The MF Media Engine utility process crashed — find `hr=` or error lines immediately before it. Note: this signal has a different meaning for other IPC actors. |

## Known Failure Pattern: Hardware Context Reset

GPU sleep/hibernate causes the GPU driver to reinitialize. CDM and MF objects that
hold GPU resources become invalid. The failure chain typically looks like:

```
[GPU process]       OnHardwareContextReset received
[CDM utility]       hardware reset error, hr=0x8004CD12
[CDM utility]       Destroyed actor without shutdown  ← utility process crash
[Child process]     Received hardware reset
[Child process]     MF_MEDIA_ENGINE_EVENT_ERROR
[Parent process]    remote process has crashed
```

Look for this sequence crossing process boundaries. The `hr=` code at the CDM
utility level is the root cause; everything after is propagation.

## Cross-Process Propagation

For CDM/EME failures, track the event chain:
1. **CDM utility process** — first to see the hardware/DRM error
2. **Content child process** — receives notification, may fire media error events
3. **Parent process** — sees subprocess crash if CDM utility dies

After a CDM utility process crash (new PID), check whether CDM reinitializes
successfully or stays broken for the remainder of the test.

## PlayReady / DRM-Specific

- `DRM_E_TEE_INVALID_HWDRM_STATE` (`0x8004CD12`) — the hardware DRM state became
  invalid, for example after OS sleep/resume or a move to another graphics adapter.
  It is not a missing license. Gecko then closes all CDM sessions
  (`MFCDMProxy::OnHardwareContextReset`)
- `MF_E_UNSUPPORTED_SERVICE` (`0xC00D36BA`) — requested service not supported; often
  seen when the CDM utility process is in a bad state
- License acquisition failures typically appear before playback starts; hardware
  reset failures appear mid-playback
