# Firefox CAPTCHA Detection Plugin

Skills for analyzing Firefox's CAPTCHA detection telemetry — the
`captcha_detection.*` metrics and the `captcha-detection` custom ping, recorded by
`toolkit/components/captchadetection/`.

## Skills

### `captcha-detection-metrics`

How to interpret and query the ping: per-vendor counter semantics (ArkoseLabs,
Cloudflare Turnstile, Datadome, Google reCAPTCHA v2, hCaptcha, AWS WAF), which
ratios are valid for each vendor and which are misleading, the known metric gaps
tracked under meta bug 2054266, cohorting by privacy settings or browsing volume,
and the filters that keep non-organic data out of an analysis.

Use it when sizing or writing an analysis over the ping, or when reviewing a query
or dashboard built on it. See
[`skills/captcha-detection-metrics/SKILL.md`](skills/captcha-detection-metrics/SKILL.md)
for details.