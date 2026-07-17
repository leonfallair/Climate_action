import numpy as np
from osgeo import gdal

#relative Pfad
path = "final_submission\data\Wiesbaden_LST_2025_Summer_QA.tif"

ds = gdal.Open(path)
band = ds.GetRasterBand(1)

arr = band.ReadAsArray()

# NaN entfernen
arr = arr[np.isfinite(arr)]

print("Anzahl gültiger Pixel:", len(arr))

print("Q25:", np.percentile(arr,25))
print("Median:", np.percentile(arr,50))
print("Q75:", np.percentile(arr,75))