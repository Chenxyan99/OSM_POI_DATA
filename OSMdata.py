import osmnx as ox
import matplotlib.pyplot as plt

class OSMDataProcessor:
    def __init__(self, place):
        self.place = place
        self.city = ox.geocode_to_gdf(place)
        self.poi_data = None

    def get_OSM_data(self):
        # 获取兴趣点数据
        self.poi_data = ox.features_from_polygon(self.city['geometry'].all(), tags={"amenity": True})

        # 提取不同类型的几何数据
        ds = self.poi_data.loc['node']['geometry']
        # ds2 = self.poi_data.loc['way']['geometry']
        # ds3 = self.poi_data.loc['relation']['geometry']

        # 绘制数据
        ax = plt.subplot()
        ds.plot(edgecolor='b', alpha=0.5, ax=ax)
        # ds2.plot(edgecolor='k', alpha=0.5, ax=ax)
        # ds3.plot(edgecolor='r', alpha=0.5, ax=ax)

        # 绘制边界
        self.city.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2, alpha=0.7)

        plt.show()

    def save_to_csv(self):
        self.poi_data.to_csv('./OSM_DATA/all_poi.csv')

    def save_to_shp(self):
        # poi
        # self.poi_data.loc['node']['geometry'].to_file(r'.\OSM_DATA\all_poi.shp')
        # 边界
        self.city.to_file(r'.\OSM_DATA\boundary.shp')

