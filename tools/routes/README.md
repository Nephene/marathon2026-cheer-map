# Route data pipeline (docs/data/routes.json)

Scratch scripts used to build `docs/data/routes.json`. Run them in this order from a working dir:

1. `route.py <course.pdf>` extracts the red marathon line (stroke 0.93/0.11/0.14, width ~5) and writes `red_segs.json`.
2. `fit2.py` matches the metro and train icons in the PDF to OSM station nodes (`stations.json` from Overpass, `railway=station`) and fits a quadratic PDF→lat/lon transform (`geofit.json`, ~50 m mean residual).
3. `transform_route.py` joins the route (start→km10, km10→~25, ~25→finish), transforms it with `geofit.json` and saves `route_raw2.json`. Its OSRM map-matching part fails, because the public server allows only a few points with a 40 m radius. It isn't needed: the raw trace already follows the streets. `geo.py` is the earlier affine-only version.
4. `kmfix.py <course.pdf>` snaps the red km labels and the cheer spots onto the course (`kmfix.json`).
5. `build_data.py` writes `docs/data/routes.json`, with walking legs from routing.openstreetmap.de (foot) at 4.8 km/h and metro legs as station-to-station lines.
