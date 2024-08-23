<template>
    <div id="cesiumContainer"></div>
    <div id="leaflet"></div>
</template>
<script setup lang="ts">
import * as Cesium from 'cesium'
import * as shapefile from 'shapefile'
import HeatMapLayer from '@cesium-extends/heat';
import CesiumNavigation from 'cesium-navigation-es6';
import Supercluster from 'supercluster';
import axios from 'axios';
import { onMounted, } from 'vue'

Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJiNGNiNTMwMy1iMTM0LTRmNjMtODQ3Zi1mMDEwMTc2N2FmYTkiLCJpZCI6MTM0NTEzLCJpYXQiOjE2ODE5MTAzOTJ9.tiKWDatrDzITuelBgU6GOGvDC9i8Uw-UVWE_2kQmTD4'
let viewer: any = undefined
const pointEntities: any[] = [];

// 初始化 Cesium
const initCeisum = () => {
    viewer = new Cesium.Viewer('cesiumContainer', {
        sceneMode: Cesium.SceneMode.SCENE3D, // 场景模式
        timeline: false, // 时间轴控件
        animation: false, // 动画控件
        geocoder: false, // 搜索控件
        homeButton: true, // 主页控件
        sceneModePicker: true, // 投影方式控件
        baseLayerPicker: false, // 图层选择控件
        navigationHelpButton: false, // 帮助控件
        fullscreenButton: false, //全屏控件
    })
    // 去除左下角的logo
    viewer._cesiumWidget._creditContainer.style.display = "none";
    // 添加 OpenStreetMap 图层
    viewer.imageryLayers.removeAll();
    viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({
        url: 'https://a.tile.openstreetmap.org/'
    }));
    // // 创建一个新的网格图像提供者
    // const gridImageryProvider = new Cesium.GridImageryProvider({
    //     cells: 0, // 设置网格的单元格数量
    //     color: Cesium.Color.WHITE, // 设置网格的颜色
    // });
    // // 将网格图像提供者添加到图层中
    // viewer.imageryLayers.addImageryProvider(gridImageryProvider);
    // 显示帧数
    viewer.scene.debugShowFramesPerSecond = true;
    // 聚焦到中国杭州
    viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(120.1536, 30.2875, 400000), // 杭州的经度、纬度和高度
        orientation: {
            heading: Cesium.Math.toRadians(0), // 方向
            pitch: Cesium.Math.toRadians(-90), // 倾斜角度
            roll: 0 // 翻滚角度
        },
        duration: 0
    });
    // 比例尺
    new CesiumNavigation(viewer, {
        enableCompass: false,//指南针
        enableZoomControls: true, //是否启用缩放控件
        enableDistanceLegend: true//比例尺
    });
}

// 实现原生聚类
const POI_cluster_simple = async () => {
    // 创建监听器
    let removeListener: any = undefined;
    // 创建一个自定义数据源来保存聚类后的点
    const clusterDataSource = new Cesium.CustomDataSource('POI_Cluster');
    // 添加数据
    for (let i = 0; i < pointEntities.length; i++) {
        clusterDataSource.entities.add(pointEntities[i]);
    }

    const clusterDataSourcePromise = viewer.dataSources.add(clusterDataSource);

    clusterDataSourcePromise.then((dataSource: any) => {
        // 创建聚合
        dataSource.clustering.enabled = true;
        dataSource.clustering.pixelRange = 170;
        dataSource.clustering.minimumClusterSize = 2;
        // 设置聚合样式
        removeListener = dataSource.clustering.clusterEvent.addEventListener((clusteredEntities: any, cluster: any) => {
            // console.log(`Clustered ${clusteredEntities.length} entities`); // 调试输出

            cluster.label.show = false;
            cluster.billboard.show = true;

            // 创建一个包含文本的canvas
            const canvas = document.createElement('canvas');
            canvas.width = 60;
            canvas.height = 60;
            const context = canvas.getContext('2d');
            if (context) {
                // 创建一个圆形渐变
                const gradient = context.createRadialGradient(canvas.width / 2, canvas.height / 2, 0, canvas.width / 2, canvas.height / 2, canvas.width / 2);
                gradient.addColorStop(0, 'red');
                gradient.addColorStop(0.6, 'red');
                gradient.addColorStop(1, 'transparent');

                // 使用渐变填充背景
                context.fillStyle = gradient;
                context.fillRect(0, 0, canvas.width, canvas.height);

                // 绘制文本
                context.font = '16px sans-serif'; // 增大字体大小
                context.textAlign = 'center';
                context.textBaseline = 'middle';
                context.fillStyle = 'white';
                context.fillText(clusteredEntities.length.toString(), canvas.width / 2, canvas.height / 2);
            }
            // 将canvas转换为图像URL
            const imageUrl = canvas.toDataURL();
            cluster.billboard.image = imageUrl;
        });

        // 强制更新聚类效果
        const pixelRange = dataSource.clustering.pixelRange;
        dataSource.clustering.pixelRange = 0;
        dataSource.clustering.pixelRange = pixelRange;
    });
}

// SuperCluster网格距离算法
const POI_cluster_grid = async () => {
    // 创建一个 Supercluster 实例
    let index = new Supercluster({
        radius: 160, // 聚类半径，以像素为单位
        maxZoom: 16, // 最大缩放级别
        minZoom: 0,  // 最小缩放级别
        extent: 256, // 每个瓦片的边长
        nodeSize: 64 // 四叉树节点的大小
    });

    // 准备要加载到Supercluster的点数据
    let points: any[] = [];
    // 创建一个BillboardCollection和一个PointPrimitiveCollection
    let billboards: any = undefined;
    let pointsEntities: any = undefined;
    // 添加点到 points
    for (let i = 0; i < pointEntities.length; i++) {
        const point = pointEntities[i];
        const pointInGlobal = point.position.getValue(Cesium.JulianDate.now());
        const position = Cesium.Cartographic.fromCartesian(pointInGlobal);
        // 将弧度转换为经纬度
        const longitude = Cesium.Math.toDegrees(position.longitude);
        const latitude = Cesium.Math.toDegrees(position.latitude);

        // 添加点到数组
        points.push({
            type: 'Feature',
            properties: {},
            geometry: {
                type: 'Point',
                coordinates: [longitude, latitude]
            }
        });
    }

    // 加载点数据
    index.load(points);
    const updateClusters = () => {
        // 获取当前的摄像机高度
        const height = viewer.camera.positionCartographic.height;
        // 计算缩放级别
        const maxZoom = 16; // 这是你在Supercluster中设置的最大缩放级别
        const zoom = Math.max(0, Math.min(maxZoom, Math.floor(Math.log2(352000000 / height))));
        // // 获取当前视图的聚类
        let clusters = index.getClusters([118, 28, 121, 32], zoom);
        // 清除之前的Primitive
        if (billboards) {
            viewer.scene.primitives.remove(billboards);
        }
        if (pointsEntities) {
            viewer.scene.primitives.remove(pointsEntities);
        }
        billboards = new Cesium.BillboardCollection();
        pointsEntities = new Cesium.PointPrimitiveCollection();
        // 添加新的实体
        clusters.forEach(cluster => {
            if (cluster.properties.cluster) {
                // 这是一个聚类
                // 创建一个包含文本的canvas
                const canvas = document.createElement('canvas');
                canvas.width = 60;
                canvas.height = 60;
                const context = canvas.getContext('2d');
                if (context) {
                    // 根据数量选择颜色
                    let color;
                    if (cluster.properties.point_count < 50) {
                        color = 'rgba(181, 226, 140, 0.8)';
                    } else if (cluster.properties.point_count < 100) {
                        color = 'rgba(241, 211, 87, 0.8)';
                    } else {
                        color = 'rgba(253, 156, 115, 0.8)';
                    }
                    // 创建一个圆形渐变
                    const gradient = context.createRadialGradient(canvas.width / 2, canvas.height / 2, 0, canvas.width / 2, canvas.height / 2, canvas.width / 2);
                    gradient.addColorStop(0, color);
                    gradient.addColorStop(0.6, color);
                    gradient.addColorStop(1, 'transparent');

                    // 使用渐变填充背景
                    context.fillStyle = gradient;
                    context.fillRect(0, 0, canvas.width, canvas.height);

                    // 绘制文本
                    context.font = '16px sans-serif'; // 增大字体大小
                    context.textAlign = 'center';
                    context.textBaseline = 'middle';
                    context.fillStyle = 'black';
                    context.fillText(cluster.properties.point_count.toString(), canvas.width / 2, canvas.height / 2);
                }
                // 将canvas转换为图像URL
                const imageUrl = canvas.toDataURL();

                const position = Cesium.Cartesian3.fromDegrees(cluster.geometry.coordinates[0], cluster.geometry.coordinates[1]);
                // 添加到BillboardCollection
                billboards.add({
                    position: position,
                    image: imageUrl,
                });
            } else {
                // 这是一个单独的点
                const position = Cesium.Cartesian3.fromDegrees(cluster.geometry.coordinates[0], cluster.geometry.coordinates[1]);
                // 添加到PointPrimitiveCollection
                pointsEntities.add({
                    position: position,
                    pixelSize: 10,
                    color: Cesium.Color.BLUE
                });
            }
        });
        // 添加新的Primitive
        viewer.scene.primitives.add(billboards);
        viewer.scene.primitives.add(pointsEntities);
    }
    updateClusters();
    // 当视图改变时，重新计算聚类
    viewer.camera.changed.addEventListener(function () {
        updateClusters();
    });
}

// 获取 POI 数据
const getPOIdata = async () => {
    // shp 文件的 URL
    const url = '/all_poi.shp';
    // 读取 shp 文件
    const response = await axios.get(url, { responseType: 'arraybuffer' });
    const shpBuffer = response.data;
    shapefile.open(shpBuffer)
        .then(source => source.read().then(function log(result): any {
            if (result.done) return;
            // 这里可以将 result.value 转换为 GeoJSON 形式
            const geojson = {
                type: "FeatureCollection",
                features: [result.value]
            };

            // 加载 GeoJSON 到 Cesium 中
            Cesium.GeoJsonDataSource.load(geojson).then(dataSource => {
                // 遍历实体集合
                dataSource.entities.values.forEach(entity => {
                    // 获取实体的位置
                    const position = entity.position?.getValue(Cesium.JulianDate.now());
                    const point = new Cesium.Entity({
                        position: position,
                        point: {
                            color: Cesium.Color.BLUE,
                            pixelSize: 5,
                            show: true
                        }
                    });
                    pointEntities.push(point);
                    // viewer.entities.add(point);
                });
            });
            return source.read().then(log);
        })).catch(error => console.error(error.stack));
}

// 获取边界
const getBoundary = async () => {
    // shp 文件的 URL
    const url = '/boundary.shp';

    // 读取 shp 文件
    const response = await axios.get(url, { responseType: 'arraybuffer' });
    const shpBuffer = response.data;
    shapefile.open(shpBuffer)
        .then(source => source.read().then(function log(result): any {
            if (result.done) return;
            // 这里可以将 result.value 转换为 GeoJSON 形式
            const geojson = {
                type: "FeatureCollection",
                features: [result.value]
            };

            // 加载 GeoJSON 到 Cesium 中
            Cesium.GeoJsonDataSource.load(geojson).then(dataSource => {
                // 遍历实体集合
                dataSource.entities.values.forEach(entity => {
                    if (entity.polygon && entity.polygon.hierarchy) {
                        // 获取多边形的边界
                        const hierarchy = entity.polygon.hierarchy.getValue(Cesium.JulianDate.now());
                        if (hierarchy) {
                            // 创建一个线
                            entity.polyline = new Cesium.PolylineGraphics({
                                positions: hierarchy.positions,
                                width: 3,
                                material: Cesium.Color.BLUE
                            });

                            // 删除多边形
                            entity.polygon = undefined;
                        }
                    }
                });
                viewer.dataSources.add(dataSource);
            });

            return source.read().then(log);
        })).catch(error => console.error(error.stack));
}

// 绘制heatMap
const drawHeatMap = async () => {
    const data = [];
    // 添加POI数据到热力图
    for (let i = 0; i < pointEntities.length; i++) {
        const point = pointEntities[i];
        const pointInGlobal = point.position.getValue(Cesium.JulianDate.now());
        const position = Cesium.Cartographic.fromCartesian(pointInGlobal);
        // 将弧度转换为经纬度
        const longitude = Cesium.Math.toDegrees(position.longitude);
        const latitude = Cesium.Math.toDegrees(position.latitude);
        data.push({
            pos: [longitude, latitude],
            value: 1
        });
    }
    // 创建热力图层
    new HeatMapLayer({
        viewer,
        data,
        heatStyle: {
            radius: 20,
            maxOpacity: 0.5,
            blur: 0.8
        }
    })
}

onMounted(async () => {
    initCeisum()
    await getPOIdata()
    await getBoundary()
    // await POI_cluster_simple()
    await POI_cluster_grid()
    await drawHeatMap()
})
</script>
<style scoped lang="scss">
#cesiumContainer {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    z-index: 10;
}

:deep(.distance-legend) {
    background-color: rgba(255, 255, 255, 0.8);
    border: 2px solid #777;

    .distance-legend-label {
        color: #333;
    }

    .distance-legend-scale-bar {
        border-left: 1px solid #333;
        border-right: 1px solid #333;
        border-bottom: 1px solid #333
    }
}

:deep(.navigation-controls) {
    background-color: rgba(255, 255, 255, 0.8);
    border: 1px solid #333;

    .navigation-control-icon-zoom-in,
    .navigation-control-icon-reset,
    .navigation-control-icon-zoom-out {
        color: #333;
        fill: #333;
    }
}
</style>