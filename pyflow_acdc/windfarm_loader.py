import json
import os
from pathlib import Path
from shapely.geometry import LineString, MultiPolygon, Polygon, shape

from .grid_creator import Create_grid_from_pickle


def _name_variants(case_name):
    return [
        case_name,
        case_name.lower(),
        case_name.upper(),
        case_name.capitalize(),
    ]


def _candidate_dirs():
    current_file = Path(__file__).resolve()
    pkg_root = current_file.parent
    candidates = []

    # Optional override for private/local datasets.
    custom_data_dir = os.getenv("PYFLOW_WINDFARM_DATA_DIR")
    if custom_data_dir:
        candidates.append(Path(custom_data_dir))

    # Default packaged wind-farm data location.
    candidates.extend(
        [
            pkg_root / "example_grids" / "wind_farm_data",
        ]
    )
    return candidates


def _find_grid_pickle(case_name, source_tag="gebco"):
    for base in _candidate_dirs():
        for name in _name_variants(case_name):
            candidates = [
                base / f"{name}_{source_tag}.pkl.gz",
                base / f"{name}.pkl.gz",
            ]
            for candidate in candidates:
                if candidate.exists():
                    return candidate
    raise FileNotFoundError(f"Could not find grid pickle for case '{case_name}'.")


def _find_geojson(case_name):
    for base in _candidate_dirs():
        for name in _name_variants(case_name):
            candidate = base / f"{name}.geojson"
            if candidate.exists():
                return candidate
    return None


def _parse_geojson_context(geojson_path):
    if geojson_path is None:
        return [], [], [], []

    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    dev_area_polygons = []
    exclusion_polygons = []
    soft_exclusion_polygons = []
    export_lines = []

    def _as_polygon_list(geom_obj):
        if isinstance(geom_obj, Polygon):
            return [geom_obj]
        if isinstance(geom_obj, MultiPolygon):
            return list(geom_obj.geoms)
        return []

    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        my_type = props.get("myType")
        geom_type = geom.get("type")
        coords = geom.get("coordinates")

        if not coords:
            continue

        try:
            geom_obj = shape(geom)
        except Exception:
            continue

        if my_type == "pixel":
            pixel_parts = _as_polygon_list(geom_obj)
            dev_area_polygons.extend(pixel_parts)
            # Match create_array_graph_from_geojson behavior: interior rings act as exclusions.
            for poly in pixel_parts:
                for interior in poly.interiors:
                    exclusion_polygons.append(Polygon(interior))
        elif my_type == "exclusion_zone":
            exclusion_polygons.extend(_as_polygon_list(geom_obj))
        elif my_type == "exclusion_zone_soft":
            soft_exclusion_polygons.extend(_as_polygon_list(geom_obj))
        elif my_type == "export_cable":
            if geom_type == "LineString":
                export_lines.append(geom_obj if isinstance(geom_obj, LineString) else LineString(coords))
            elif geom_type == "MultiLineString":
                export_lines.extend(list(geom_obj.geoms))

    return dev_area_polygons, export_lines, exclusion_polygons, soft_exclusion_polygons


def load_case_grid_and_geo(case_name, source_tag="gebco"):
    grid_pickle = _find_grid_pickle(case_name, source_tag=source_tag)
    grid, res = Create_grid_from_pickle(str(grid_pickle), use_dill=True)

    geojson_path = _find_geojson(case_name)
    dev_area_polygons, export_lines, exclusion_zones, soft_exclusion_zones = _parse_geojson_context(geojson_path)

    # Attach geometry context for plotting helpers.
    grid.dev_polygon = dev_area_polygons
    grid.export_cables = export_lines
    grid.exclusion_zones = exclusion_zones
    grid.soft_exclusion_zones = soft_exclusion_zones
    

    return grid, res
