# erreichbarkeit raaster calc

1 *
(
(
("LCZ_precise_utm@1" = 2) +
("LCZ_precise_utm@1" = 3) +
("LCZ_precise_utm@1" = 5) +
("LCZ_precise_utm@1" = 6) +
("LCZ_precise_utm@1" = 8) +
("LCZ_precise_utm@1" = 9)
)
*
("Wiesbaden_LST_2025_Summer_QA@1" <= 37.2)
*
("distance_final@1" < 500)
)

+

2 *
(
(
("LCZ_precise_utm@1" = 2) +
("LCZ_precise_utm@1" = 3) +
("LCZ_precise_utm@1" = 5) +
("LCZ_precise_utm@1" = 6) +
("LCZ_precise_utm@1" = 8) +
("LCZ_precise_utm@1" = 9)
)
*
("Wiesbaden_LST_2025_Summer_QA@1" <= 37.2)
*
("distance_final@1" >= 500)
)

+

3 *
(
(
("LCZ_precise_utm@1" = 2) +
("LCZ_precise_utm@1" = 3) +
("LCZ_precise_utm@1" = 5) +
("LCZ_precise_utm@1" = 6) +
("LCZ_precise_utm@1" = 8) +
("LCZ_precise_utm@1" = 9)
)
*
("Wiesbaden_LST_2025_Summer_QA@1" > 37.2)
*
("distance_final@1" < 500)
)

+

4 *
(
(
("LCZ_precise_utm@1" = 2) +
("LCZ_precise_utm@1" = 3) +
("LCZ_precise_utm@1" = 5) +
("LCZ_precise_utm@1" = 6) +
("LCZ_precise_utm@1" = 8) +
("LCZ_precise_utm@1" = 9)
)
*
("Wiesbaden_LST_2025_Summer_QA@1" > 37.2)
*
("distance_final@1" >= 500)
)
# raster stats temp

Q25: 27.540018590000017
Median: 33.305363825000015
Q75: 37.22241474500002

# gee temp code

// Wiesbaden-Grenze laden
var area = ee.FeatureCollection(
  'projects/ee-leonfaller/assets/Wiesbaden_shape'
);

// Karte zentrieren
Map.centerObject(area, 11);
Map.addLayer(area, {}, 'Wiesbaden');


// Funktion zur Entfernung von Wolken und Schatten
function maskLandsat(image) {

  var qa = image.select('QA_PIXEL');

  // Bits:
  // 3 = Cloud
  // 4 = Cloud Shadow
  // 5 = Snow
  // 7 = Water
  var mask = qa.bitwiseAnd(1 << 3).eq(0)
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));

  return image.updateMask(mask);
}


// Landsat 9 Level-2 Surface Temperature
var landsat = ee.ImageCollection(
  'LANDSAT/LC09/C02/T1_L2'
)
  .filterBounds(area)
  .filterDate('2025-06-01', '2025-08-31')
  .filter(ee.Filter.lt('CLOUD_COVER', 20))
  .map(maskLandsat);


// Anzahl verwendeter Bilder anzeigen
print(
  'Anzahl Landsat Szenen:',
  landsat.size()
);


// Oberflächentemperatur in °C berechnen
var lst = landsat.map(function(image) {

  var temperature = image.select('ST_B10')
    .multiply(0.00341802)
    .add(149.0)
    .subtract(273.15)
    .rename('LST');

  return temperature.copyProperties(
    image,
    ['system:time_start']
  );

});


// Sommermittelwert
var meanLST = lst.mean();


// Temperaturstatistik Wiesbaden
var stats = meanLST.reduceRegion({
  reducer: ee.Reducer.minMax()
    .combine({
      reducer2: ee.Reducer.mean(),
      sharedInputs:true
    }),
  geometry: area,
  scale: 100,
  maxPixels: 1e13
});

print('LST Statistik °C:', stats);


// Darstellung
Map.addLayer(
  meanLST.clip(area),
  {
    min:20,
    max:45,
    palette:[
      'blue',
      'cyan',
      'green',
      'yellow',
      'orange',
      'red'
    ]
  },
  'Mean LST Sommer 2025'
);


// Export
Export.image.toDrive({
  image: meanLST.clip(area),
  description:'Wiesbaden_LST_2025_Summer_QA',
  folder:'GEE',
  fileNamePrefix:'Wiesbaden_LST_2025_Summer_QA',
  region:area.geometry(),
  scale:100,
  crs:'EPSG:25832',
  maxPixels:1e13
});