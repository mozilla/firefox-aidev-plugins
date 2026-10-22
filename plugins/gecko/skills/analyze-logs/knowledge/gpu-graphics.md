# GPU / Graphics Log Patterns

Reference for analyzing logs involving GPU process failures, Direct3D device loss,
and OpenGL/EGL context failures.

## Key Signals

| Signal                               | Meaning                                                       |
|--------------------------------------|---------------------------------------------------------------|
| `D3D device lost` / `device removed` | Direct3D device was lost (driver reset, sleep/hibernate, TDR) |
| `Failed to make GL context current`  | EGL/GL context failure in GPU process                         |
| `GLContextProvider` errors           | OpenGL context provider failure                               |
| `D3D11` / `DXGI` errors              | Direct3D 11 or DXGI-level failure                             |

## Device Loss Pattern

GPU device loss (from sleep/hibernate, driver timeout recovery, or display change)
causes a cascade:

1. **GPU process** detects device removed/reset
2. **Parent process** receives GPU process notification
3. Any subsystem holding GPU resources (CDM, compositor, video decoder) becomes invalid

If you see GPU device loss signals alongside CDM/MF failures, the GPU event is
likely the root cause. See `mf-media-engine.md` for how hardware context resets
propagate through the CDM pipeline specifically.

## Common Causes

- **Sleep/hibernate** — most common; GPU driver reinitializes on wake
- **Driver timeout detection and recovery (TDR)** — driver reset due to a hung GPU operation
- **Display configuration change** — monitor plug/unplug on some hardware
- **Resource exhaustion** — rare; usually shows `E_OUTOFMEMORY` (`0x8007000E`) alongside device loss
