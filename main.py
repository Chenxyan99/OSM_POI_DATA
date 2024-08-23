# from OSMdata import OSMDataProcessor
from QGIS_controller import qgisController

if __name__ == '__main__':
    # 获取区域边界、POI数据
    # processor = OSMDataProcessor(place='Hangzhou, China')
    # processor.get_OSM_data()
    # processor.save_to_csv()
    # processor.save_to_shp()

    # 处理POI数据
    qgis = qgisController()
    qgis.test()
    # qgis.exit()