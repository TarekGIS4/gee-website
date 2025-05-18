import folium
import geemap.foliumap as geemap
import ee


ee.Initialize(project='ee-risgis897')

roi = ee.FeatureCollection('projects/ee-risgis897/assets/beni-gov')

Map = folium.Map(location=[29.1, 30.6], zoom_start=10)
Map.add_child(folium.GeoJson(data=roi.getInfo(), name='Beni Suef Region'))

def get_ndvi(year):
    start = f'{year}-01-01'
    end = f'{year}-12-31'

    if year <= 2011:
        col_id = 'LANDSAT/LT05/C02/T1_L2'
        collection = ee.ImageCollection(col_id)
        def mask_sr(img):
            qa = img.select('QA_PIXEL')
            mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
            return img.updateMask(mask)
        def scale(img):
            return img.multiply(0.0000275).add(-0.2)

        image = collection.filterDate(start, end).filterBounds(roi).map(mask_sr)
        if image.size().getInfo() == 0:
            raise Exception(f"No images available for year {year}")
        image = image.median()
        red = scale(image.select('SR_B3'))
        nir = scale(image.select('SR_B4'))

    elif year >= 2013:
        col_id = 'LANDSAT/LC08/C02/T1_L2'
        collection = ee.ImageCollection(col_id)
        def mask_sr(img):
            qa = img.select('QA_PIXEL')
            mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
            return img.updateMask(mask)
        def scale(img):
            return img.multiply(0.0000275).add(-0.2)

        image = collection.filterDate(start, end).filterBounds(roi).map(mask_sr)
        if image.size().getInfo() == 0:
            raise Exception(f"No images available for year {year}")
        image = image.median()
        red = scale(image.select('SR_B4'))
        nir = scale(image.select('SR_B5'))
    else:
        raise Exception(f"Landsat 7 is excluded in year {year}")

    ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
    ndvi_vis = ndvi.clip(roi).visualize(min=0.2, max=0.8, palette=['white', 'yellow', 'green'])

    return ndvi_vis

for year in range(1984, 2025):
    if year == 2012:
        continue
    try:
        ndvi_layer = get_ndvi(year)
        map_id = ee.Image(ndvi_layer).getMapId()
        folium.TileLayer(
            tiles=map_id['tile_fetcher'].url_format,
            attr='NDVI',
            name=f'NDVI {year}',
            overlay=True,
            control=True
        ).add_to(Map)
    except Exception as e:
        print(f"❌ Year {year} skipped: {e}")

folium.LayerControl().add_to(Map)

Map.save('C:/Users/tm605/Desktop/GEE.APP/ndvi_time_slider_map55.html')