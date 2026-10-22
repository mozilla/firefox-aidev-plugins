# HRESULT Decode Reference

## Common Media Foundation / PlayReady HRESULTs

The `MF_E_*` values come from `mferror.h`. The `DRM_E_*` values come from
`dom/media/ipc/MFMediaEngineUtils.h`.

| HRESULT      | Name                                                       | Meaning                                                                                                                                                                   |
|--------------|------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `0x8004CD12` | `DRM_E_TEE_INVALID_HWDRM_STATE`                            | Hardware DRM state became invalid, e.g. after OS sleep/resume or a move to another graphics adapter. Gecko closes all CDM sessions (`MFCDMProxy::OnHardwareContextReset`) |
| `0x8004CD00` | `DRM_OEM_E_ASD_ACTIVE_DISPLAY_FAIL`                        | AMD-specific hardware DRM state error (active display security failure)                                                                                                   |
| `0xC00D3E85` | `MF_E_SHUTDOWN`                                            | MF object used after shutdown                                                                                                                                             |
| `0xC00D36BB` | `MF_E_UNEXPECTED`                                          | Engine in invalid state                                                                                                                                                   |
| `0xC00D36D5` | `MF_E_NOT_FOUND`                                           | Resource/key not found                                                                                                                                                    |
| `0xC00D36BA` | `MF_E_UNSUPPORTED_SERVICE`                                 | Requested service not supported                                                                                                                                           |
| `0xC00D7159` | `MF_E_POLICY_UNSUPPORTED`                                  | The output protection policy is not supported                                                                                                                             |
| `0xC00D6D6D` | `MF_E_TRANSFORM_NOT_POSSIBLE_FOR_CURRENT_OUTPUT_MEDIATYPE` | The decoder cannot produce the current output type                                                                                                                        |
| `0xC00D36B1` | `MF_E_BUFFERTOOSMALL`                                      | Buffer too small                                                                                                                                                          |
| `0xC00D36B3` | `MF_E_INVALIDSTREAMNUMBER`                                 | Invalid stream                                                                                                                                                            |
| `0x8007000E` | `E_OUTOFMEMORY`                                            | Out of memory (often GPU memory after device loss)                                                                                                                        |
| `0x8004DA73` | PlayReady DRM error (name not verified)                    | License/key acquisition failure                                                                                                                                           |
| `0x80004004` | `E_ABORT`                                                  | Operation aborted                                                                                                                                                         |
| `0x80004005` | `E_FAIL` / `NS_ERROR_FAILURE`                              | General failure                                                                                                                                                           |

## High-Bit Classification

For unknown codes, the high bits identify the category:

| Pattern      | Category                                                                       |
|--------------|--------------------------------------------------------------------------------|
| `0x8007xxxx` | Win32 error wrapped in HRESULT — look up the low 16 bits as a Win32 error code |
| `0xC00Dxxxx` | Media Foundation error                                                         |
| `0x8004xxxx` | COM / DRM error                                                                |
| `0x8000xxxx` | Standard COM error                                                             |
