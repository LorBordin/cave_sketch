The satellite view gets not rendered. The app displays only white background. The other features work.

DIAGNOSIS 2026-06-23: ZERO_HEIGHT — probeResult: "{\"bodyW\":352,\"bodyH\":0,\"mapW\":352,\"mapH\":0,\"mapCompH\":0}"

RESOLVED 2026-06-23: branch C1 — Folium map container collapsed to 0px height inside WebView due to lack of MATCH_PARENT layout parameters and height constraints. Preview renders on device.
