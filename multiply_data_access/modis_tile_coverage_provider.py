from osgeo import osr, __version__ as gdalversion
from shapely.geometry import LineString, Point, Polygon
from typing import Optional

POLYGON_H11_V01 = 'POLYGON((-180 70.26877076152088, -175.4282639386602 69.99999999361783, -180 69.99999999361783, ' \
                  '-180 70.26877076152088))'
POLYGON_H24_V01 = 'POLYGON((180 69.99999999361783, 175.428263943709 69.99999999361783, 180 70.26877076121633, ' \
                  '180 69.99999999361783))'
POLYGON_H11_V16 = 'POLYGON((-180 -69.99999999448121, -175.4282639459231 -69.99999999448121, -180 -70.2687707619221, ' \
                  '-180 -69.99999999448121))'
POLYGON_H24_V16 = 'POLYGON((175.4282639509718 -69.99999999448121, 180 -69.99999999448121, 180 -70.26877076161755, ' \
                  '175.4282639509718 -69.99999999448121))'
POLYGON_H14_V17 = 'POLYGON((-180 -79.99999999363114, -172.7631143657403 -79.99999999363114, -180 -80.47144392544007, ' \
                  '-180 -79.99999999363114))'
POLYGON_H21_V17 = 'POLYGON((172.7631143756843 -79.99999999363114, 180 -79.99999999363114, 180 -80.43280255632753, ' \
                  '172.7631143756843 -79.99999999363114))'
_PROVIDED_COVERAGES = {(1, 11): POLYGON_H11_V01, (1, 24): POLYGON_H24_V01, (16, 11): POLYGON_H11_V16,
                       (16, 24): POLYGON_H24_V16, (17, 14): POLYGON_H14_V17, (17, 21): POLYGON_H21_V17}

_X_STEP = -463.31271653 * 2400
_Y_STEP = 463.31271653 * 2400
_M_Y0 = -20015109.354
_M_X0 = 10007554.677
_H_MIN = [14, 11, 9, 6, 4, 2, 1, 0, 0, 0, 0, 1, 2, 4, 6, 9, 11, 14]
_H_MAX = [21, 24, 26, 29, 31, 33, 34, 35, 35, 35, 35, 34, 33, 31, 29, 26, 24, 21]
_MERIDIAN = LineString([[0.0, 90.0], [0.0, -90.0]])

wgs84_srs = osr.SpatialReference()  # Define a SpatialReference object
wgs84_srs.ImportFromEPSG(4326)  # And set it to WGS84 using the EPSG code
modis_sinu_srs = osr.SpatialReference()  # define the SpatialReference object
modis_sinu_srs.ImportFromProj4(
    "+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")
_modis_to_wgs84 = osr.CoordinateTransformation(modis_sinu_srs, wgs84_srs)


def get_tile_coverage(h: int, v: int) -> Optional[Polygon]:
    if h < _H_MIN[v] or h > _H_MAX[v]:
        return None
    sinu_min_lat = h * _Y_STEP + _M_Y0
    sinu_max_lat = (h + 1) * _Y_STEP + _M_Y0
    sinu_min_lon = v * _X_STEP + _M_X0
    sinu_max_lon = (v + 1) * _X_STEP + _M_X0
    points = []
    if int(gdalversion[0]) >= 3:
        lon0, lat0, z0 = _modis_to_wgs84.TransformPoint(sinu_min_lat, sinu_min_lon)
        lon2, lat2, z2 = _modis_to_wgs84.TransformPoint(sinu_max_lat, sinu_min_lon)
        lon3, lat3, z3 = _modis_to_wgs84.TransformPoint(sinu_max_lat, sinu_max_lon)
        lon1, lat1, z1 = _modis_to_wgs84.TransformPoint(sinu_min_lat, sinu_max_lon)
    else:
        lat0, lon0, z0 = _modis_to_wgs84.TransformPoint(sinu_min_lat, sinu_min_lon)
        lat2, lon2, z2 = _modis_to_wgs84.TransformPoint(sinu_max_lat, sinu_min_lon)
        lat3, lon3, z3 = _modis_to_wgs84.TransformPoint(sinu_max_lat, sinu_max_lon)
        lat1, lon1, z1 = _modis_to_wgs84.TransformPoint(sinu_min_lat, sinu_max_lon)
    points.append(Point(lat0, lon0))
    points.append(Point(lat2, lon2))
    points.append(Point(lat3, lon3))
    points.append(Point(lat1, lon1))
    points.append(Point(lat0, lon0))
    
    polygon = Polygon([[p.x, p.y] for p in points])
    polygon = _validate_polygon(polygon)
    if h < 17:
        polygon = _cut_western(polygon)
    elif h > 18:
        polygon = _cut_eastern(polygon)
    return polygon

def _validate_polygon(polygon: Polygon()):
    coords = polygon.exterior.coords
    min_lat = 90.
    max_lat = -90.
    for coord in coords:
        if coord[1] < min_lat:
            min_lat = coord[1]
        if coord[1] > max_lat:
            max_lat = coord[1]
    upper_coords = []
    lower_coords = []
    for i in range(len(coords) - 1):
        coord = coords[i]
        if coord[1] == max_lat:
            upper_coords.append(coord)
        elif coord[1] == min_lat:
            lower_coords.append(coord)
    point_list = []
    if upper_coords[0][0] > upper_coords[1][0]:
        dist = upper_coords[0][0] - upper_coords[1][0]
        if dist < 180:
            point_list.append(upper_coords[1])
            point_list.append(upper_coords[0])
        else:
            point_list.append(upper_coords[0])
            point_list.append(upper_coords[1])
    else:
        dist = upper_coords[1][0] - upper_coords[0][0]
        if dist < 180:
            point_list.append(upper_coords[0])
            point_list.append(upper_coords[1])
        else:
            point_list.append(upper_coords[1])
            point_list.append(upper_coords[0])
    if lower_coords[0][0] > lower_coords[1][0]:
        dist = lower_coords[0][0] - lower_coords[1][0]
        if dist < 180:
            point_list.append(lower_coords[0])
            point_list.append(lower_coords[1])
        else:
            point_list.append(lower_coords[1])
            point_list.append(lower_coords[0])
    else:
        dist = lower_coords[1][0] - lower_coords[0][0]
        if dist < 180:
            point_list.append(lower_coords[1])
            point_list.append(lower_coords[0])
        else:
            point_list.append(lower_coords[0])
            point_list.append(lower_coords[1])
    point_list.append(point_list[0])
    return Polygon(point_list)


def _cut_western(coverage: Polygon) -> Polygon:
    coverage_coords = coverage.exterior.coords
    polygon_points = []
    if coverage_coords[0][0] < 0:
        polygon_points.append(coverage_coords[0])
    for i in range(len(coverage_coords) - 1):
        if coverage_coords[i][0] > 0 and coverage_coords[i + 1][0] > 0:
            continue
        elif coverage_coords[i][0] < 0 and coverage_coords[i + 1][0] < 0:
            polygon_points.append(coverage_coords[i + 1])
        else:
            lon_0 = coverage_coords[i][0] + 180.0
            if lon_0 > 180.0:
                lon_0 -= 360.0
            coord1 = (lon_0, coverage_coords[i][1])
            lon_1 = coverage_coords[i + 1][0] + 180.0
            if lon_1 > 180.0:
                lon_1 -= 360.0
            coord2 = (lon_1, coverage_coords[i + 1][1])
            fake_line = LineString([coord1, coord2])
            intersection = (-180.0, fake_line.intersection(_MERIDIAN).coords[0][1])
            polygon_points.append(intersection)
            if coverage_coords[i + 1][0] < 0:
                polygon_points.append(coverage_coords[i + 1])
    if polygon_points[0] != polygon_points[-1]:
        polygon_points.append(polygon_points[0])
    return Polygon(polygon_points)


def _cut_eastern(coverage: Polygon) -> Polygon:
    coverage_coords = coverage.exterior.coords
    polygon_points = []
    if coverage_coords[0][0] > 0:
        polygon_points.append(coverage_coords[0])
    for i in range(len(coverage_coords) - 1):
        if coverage_coords[i][0] < 0 and coverage_coords[i + 1][0] < 0:
            continue
        elif coverage_coords[i][0] > 0 and coverage_coords[i + 1][0] > 0:
            polygon_points.append(coverage_coords[i + 1])
        else:
            lon_0 = coverage_coords[i][0] + 180.0
            if lon_0 > 180.0:
                lon_0 -= 360.0
            coord1 = (lon_0, coverage_coords[i][1])
            lon_1 = coverage_coords[i + 1][0] + 180.0
            if lon_1 > 180.0:
                lon_1 -= 360.0
            coord2 = (lon_1, coverage_coords[i + 1][1])
            fake_line = LineString([coord1, coord2])
            intersection = (180.0, fake_line.intersection(_MERIDIAN).coords[0][1])
            polygon_points.append(intersection)
            if coverage_coords[i + 1][0] > 0:
                polygon_points.append(coverage_coords[i + 1])
    if polygon_points[0] != polygon_points[-1]:
        polygon_points.append(polygon_points[0])
    return Polygon(polygon_points)
