from types import SimpleNamespace


class GeoDataFrame(object):
    pass


class GeoSeries(object):
    pass


geopandas = SimpleNamespace()
setattr(geopandas, "GeoDataFrame", GeoDataFrame)
setattr(geopandas, "GeoSeries", GeoSeries)


class Feature(object):
    pass


class FeatureCollection(object):
    pass


geojson = SimpleNamespace()
setattr(geojson, "Feature", Feature)
setattr(geojson, "FeatureCollection", FeatureCollection)

