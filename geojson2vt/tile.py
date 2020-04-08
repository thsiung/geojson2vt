import math


def createTile(features, z, tx, ty, options):
    tolerance = 0 if z == options.maxZoom else options.tolerance / \
        ((1 << z) * options.extent)
    tile = {
        "features": [],
        "numPoints": 0,
        "numSimplified": 0,
        "numFeatures": len(features),
        "source": None,
        "x": tx,
        "y": ty,
        "z": z,
        "transformed": False,
        "minX": 2,
        "minY": 1,
        "maxX": -1,
        "maxY": 0
    }
    for feature in features:
        addFeature(tile, feature, tolerance, options)
    return tile


def addFeature(tile, feature, tolerance, options):
    geom = feature.get('geometry')
    type_ = feature.get('type')
    simplified = []

    tile.minX = math.min(tile.minX, feature.minX)
    tile.minY = math.min(tile.minY, feature.minY)
    tile.maxX = math.max(tile.maxX, feature.maxX)
    tile.maxY = math.max(tile.maxY, feature.maxY)

    if type_ == 'Point' or type == 'MultiPoint':
        for i in range(0, len(geom), 3):
            simplified.append(geom[i], geom[i + 1])
            tile.numPoints += 1
            tile.numSimplified += 1

    elif type_ == 'LineString':
        addLine(simplified, geom, tile, tolerance, False, False)

    elif type_ == 'MultiLineString' or type_ == 'Polygon':
        for i in range(len(geom)):
            addLine(simplified, geom[i], tile,
                    tolerance, type_ == 'Polygon', i == 0)

    elif type_ == 'MultiPolygon':
        for k in range(len(geom)):
            polygon = geom[k]
            for i in range(len(polygon)):
                addLine(simplified, polygon[i], tile, tolerance, True, i == 0)

    if len(simplified) > 0:
        tags = feature.tags

        if type_ == 'LineString' and options.lineMetrics:
            tags = {}
            for key in feature.tags:
                tags[key] = feature.tags[key]
            tags['mapbox_clip_start'] = geom.start / geom.size
            tags['mapbox_clip_end'] = geom.end / geom.size

        tileFeature = {
            "geometry": simplified,
            "type": 3 if type_ == 'Polygon' or type_ == 'MultiPolygon' else (2 if type_ == 'LineString' or type_ == 'MultiLineString' else 1),
            "tags": tags
        }
        if feature.id is not None:
            tileFeature.id = feature.id
        tile.features.append(tileFeature)


def addLine(result, geom, tile, tolerance, isPolygon, isOuter):
    sqTolerance = tolerance * tolerance

    if tolerance > 0 and (geom.size < (isPolygon if isPolygon is not None else tolerance)):
        tile.numPoints += len(geom) / 3
        return

    ring = []
    for i in range(0, len(geom), 3):
        if tolerance == 0 or geom[i + 2] > sqTolerance:
            tile.numSimplified += 1
            ring.append(geom[i], geom[i + 1])
        tile.numPoints += 1

    if isPolygon:
        rewind(ring, isOuter)

    result.append(ring)


def rewind(ring, clockwise):
    area = 0
    l = len(ring)
    j = l - 2
    for i in range(0, l, 2):
        area += (ring[i] - ring[j]) * (ring[i + 1] + ring[j + 1])
        j = i
    if area > 0 == clockwise:
        for i in range(0, l, 2):
            x = ring[i]
            y = ring[i + 1]
            ring[i] = ring[len - 2 - i]
            ring[i + 1] = ring[len - 1 - i]
            ring[len - 2 - i] = x
            ring[len - 1 - i] = y
