import rasterio
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns


# ------------------------------------------------
# Pfade
# ------------------------------------------------

DATA = "data"
OUT = "results"

os.makedirs(OUT, exist_ok=True)


lcz_file = os.path.join(DATA, "LCZ_precise_utm.tif")
lst_file = os.path.join(DATA, "temp_aligned.tif")
access_file = os.path.join(DATA, "Erreichbarkeit_greenery.tif")
vuln_file = os.path.join(DATA, "Vulnerabilität.tif")


# ------------------------------------------------
# Raster laden
# ------------------------------------------------

def read_raster(path):

    with rasterio.open(path) as src:

        arr = src.read(1)

        transform = src.transform

        pixel_area = abs(
            transform.a * transform.e
        )

    return arr, pixel_area


lcz, pixel_area = read_raster(lcz_file)
lst, _ = read_raster(lst_file)
access, _ = read_raster(access_file)
vuln, _ = read_raster(vuln_file)


print("LCZ:", lcz.shape)
print("LST:", lst.shape)
print("ACCESS:", access.shape)
print("VULN:", vuln.shape)



# ------------------------------------------------
# NoData entfernen
# ------------------------------------------------

def clean(arr):

    arr = arr.astype(float)

    arr[arr <= -999] = np.nan

    return arr


lcz = clean(lcz)
lst = clean(lst)
access = clean(access)
vuln = clean(vuln)



pixel_ha = pixel_area / 10000



# ------------------------------------------------
# Wohn-LCZ
# ------------------------------------------------

wohn_lcz = [2,3,5,6,8,9]



# =================================================
# 1. LCZ Flächenstatistik
# =================================================


results=[]


for cls in wohn_lcz:

    mask = lcz == cls

    pixels = np.sum(mask)

    if pixels == 0:
        continue

    area = pixels * pixel_ha

    results.append(
        [
            cls,
            pixels,
            area
        ]
    )



df = pd.DataFrame(
    results,
    columns=[
        "LCZ",
        "Pixel",
        "Flaeche_ha"
    ]
)


df["Anteil_%"] = (
    df["Flaeche_ha"] /
    df["Flaeche_ha"].sum()
    *100
)



df.to_csv(
    os.path.join(
        OUT,
        "lcz_area_statistics.csv"
    ),
    index=False
)



# =================================================
# 2. Temperatur nach LCZ
# =================================================


temperature_results=[]

boxplot=[]


for cls in wohn_lcz:


    mask = (
        (lcz == cls)
        &
        np.isfinite(lst)
    )


    values = lst[mask]


    if len(values)==0:

        print(
            f"LCZ {cls}: keine gültige LST"
        )

        continue


    temperature_results.append(
        [
            cls,
            len(values),
            np.mean(values),
            np.median(values),
            np.std(values),
            np.min(values),
            np.max(values)
        ]
    )


    for v in values:

        boxplot.append(
            [
                cls,
                v
            ]
        )



df_temp = pd.DataFrame(
    temperature_results,
    columns=[
        "LCZ",
        "Pixel",
        "Mean_LST",
        "Median_LST",
        "Std_LST",
        "Min_LST",
        "Max_LST"
    ]
)



df_temp.to_csv(
    os.path.join(
        OUT,
        "lcz_temperature_statistics.csv"
    ),
    index=False
)



# Boxplot

df_box = pd.DataFrame(
    boxplot,
    columns=[
        "LCZ",
        "LST"
    ]
)


# =================================================
# LST Boxplot nach LCZ mit LCZ-Farben
# =================================================

lcz_names = {
    2: "LCZ 2 - Compact mid-rise",
    5: "LCZ 5 - Open mid-rise",
    6: "LCZ 6 - Open low-rise",
    8: "LCZ 8 - Large low-rise",
    9: "LCZ 9 - Sparse built"
}


# LCZ-Farben (orientiert an LCZ Standardfarben)
lcz_colors = {
    "LCZ 2 - Compact mid-rise": "#8B0000",   # dunkelrot
    "LCZ 5 - Open mid-rise": "#FF0000",      # orange
    "LCZ 6 - Open low-rise": "#FF8C00",      # hellorange/beige
    "LCZ 8 - Large low-rise": "#808080",     # grau
    "LCZ 9 - Sparse built": "#D2B48C"        # beige
}


df_box["LCZ_Name"] = (
    df_box["LCZ"]
    .map(lcz_names)
)



plt.figure(figsize=(13,6))


sns.boxplot(
    data=df_box,
    x="LCZ_Name",
    y="LST",
    hue="LCZ_Name",
    palette=lcz_colors,
    legend=False
)


plt.title(
    "Verteilung der Landoberflächentemperatur nach LCZ-Klasse",
    fontsize=16,
    pad=15
)


plt.xlabel(
    "Local Climate Zone (LCZ)",
    fontsize=12
)


plt.ylabel(
    "Landoberflächentemperatur [°C]",
    fontsize=12
)


plt.xticks(
    rotation=20,
    ha="right"
)


plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4
)


plt.tight_layout()


plt.savefig(
    os.path.join(
        OUT,
        "LST_boxplot_LCZ.png"
    ),
    dpi=300,
    bbox_inches="tight"
)


plt.close()




# =================================================
# 3. Erreichbarkeit Grünflächen
# =================================================


mask_wohn = np.isin(
    lcz,
    wohn_lcz
)


dist_values = access[
    mask_wohn &
    np.isfinite(access)
]



access_stats = pd.DataFrame({

    "Metric":[
        "Mean",
        "Median",
        "Std",
        "Minimum",
        "Maximum"
    ],

    "Meter":[
        np.mean(dist_values),
        np.median(dist_values),
        np.std(dist_values),
        np.min(dist_values),
        np.max(dist_values)
    ]

})



access_stats.to_csv(
    os.path.join(
        OUT,
        "accessibility_statistics.csv"
    ),
    index=False
)



# =================================================
# 4. Vulnerabilität Fläche
# =================================================


v_results=[]


for cls in [1,2,3,4]:


    mask = vuln == cls

    pixels=np.sum(mask)


    if pixels==0:
        continue


    area=pixels*pixel_ha


    v_results.append(
        [
            cls,
            pixels,
            area
        ]
    )



df_v=pd.DataFrame(
    v_results,
    columns=[
        "Vulnerability",
        "Pixel",
        "Area_ha"
    ]
)



df_v["Anteil_%"] = (
    df_v["Area_ha"] /
    df_v["Area_ha"].sum()
    *100
)



df_v.to_csv(
    os.path.join(
        OUT,
        "vulnerability_statistics.csv"
    ),
    index=False
)



# =================================================
# 5. Vulnerabilität nach LCZ
# =================================================


vuln_lcz_results=[]


for v_class in [1,2,3,4]:

    for cls in wohn_lcz:


        mask = (
            (vuln == v_class)
            &
            (lcz == cls)
        )


        pixels=np.sum(mask)


        if pixels==0:
            continue


        area=pixels*pixel_ha


        vuln_lcz_results.append(
            [
                v_class,
                cls,
                pixels,
                area
            ]
        )



df_v_lcz=pd.DataFrame(
    vuln_lcz_results,
    columns=[
        "Vulnerability",
        "LCZ",
        "Pixel",
        "Area_ha"
    ]
)



# Anteil innerhalb jeder Vulnerabilitätsklasse

df_v_lcz["Anteil_innerhalb_Vuln_%"] = (
    df_v_lcz.groupby(
        "Vulnerability"
    )["Area_ha"]
    .transform(lambda x:
               x/x.sum()*100)
)



df_v_lcz.to_csv(
    os.path.join(
        OUT,
        "vulnerability_lcz_statistics.csv"
    ),
    index=False
)



# =================================================
# Vulnerabilität nach LCZ mit LCZ-Farben
# =================================================

pivot = (
    df_v_lcz
    .pivot(
        index="Vulnerability",
        columns="LCZ",
        values="Area_ha"
    )
    .fillna(0)
)

pivot = pivot[[2,5,6,8,9]]

# LCZ Farben
colors = [
    "#8B0000",   # LCZ 2
    "#FF0000",   # LCZ 5
    "#FF8C00",   # LCZ 6
    "#808080",   # LCZ 8
    "#D2B48C"    # LCZ 9
]

# Beschriftungen der Vulnerabilitätsklassen
vuln_labels = [
    "Niedrig\nLST ≤ 37,2 °C\nGrünfläche < 500 m",
    "Mittel\nLST ≤ 37,2 °C\nGrünfläche ≥ 500 m",
    "Mittel\nLST > 37,2 °C\nGrünfläche < 500 m",
    "Hoch\nLST > 37,2 °C\nGrünfläche ≥ 500 m"
]

ax = pivot.plot(
    kind="bar",
    stacked=True,
    figsize=(12,7),
    color=colors
)

plt.title(
    "Zusammensetzung der Vulnerabilitätsklassen nach LCZ",
    fontsize=16,
    pad=15
)

plt.xlabel(
    "Vulnerabilitätsklasse",
    fontsize=12
)

plt.ylabel(
    "Fläche [ha]",
    fontsize=12
)

# Neue X-Achsenbeschriftungen
ax.set_xticklabels(
    vuln_labels,
    rotation=0,
    ha="center",
    fontsize=10
)

plt.legend(
    [
        "LCZ 2 - Compact mid-rise",
        "LCZ 5 - Open mid-rise",
        "LCZ 6 - Open low-rise",
        "LCZ 8 - Large low-rise",
        "LCZ 9 - Sparse built"
    ],
    title="LCZ-Klasse",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUT,
        "vulnerability_lcz_distribution.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


print("\nAnalyse abgeschlossen.")
print("Ergebnisse gespeichert unter:")
print(OUT)