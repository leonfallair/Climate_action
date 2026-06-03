import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data")
METADATA_FILE = "metadata.csv"
OUTPUT_FILE = "output/temperaturen_24062025.csv"

TARGET_TIMES = {
    "temp_16": "2025-06-24T16:00:00Z",
    "temp_23": "2025-06-24T23:00:00Z"
}


def interpolate_missing(df):
    df = df.copy()

    df["temperature"] = df["temperature"].replace(-999, np.nan)

    df = df.sort_values("timestamps")
    df["timestamps"] = pd.to_datetime(df["timestamps"], utc=True)

    df = df.set_index("timestamps")

    df["temperature"] = df["temperature"].interpolate(method="time")

    return df


def parse_filename(filename):
    parts = Path(filename).stem.split("-")

    messnetz = f"{parts[0][:2]}/{parts[0][2:]}"
    station_id = parts[1]
    station_id_ergaenzung = f"{parts[2][0]}/{parts[2][1]}"

    return messnetz, station_id, station_id_ergaenzung


metadata = pd.read_csv(METADATA_FILE, dtype=str)

results = []

for file in DATA_DIR.glob("*.csv"):

    try:
        df = pd.read_csv(file)

        # ❗ SKIP: Datei komplett leer
        if df.empty:
            continue

        # ❗ SKIP: keine Temperature-Spalte oder nur NaN
        if "temperature" not in df.columns:
            continue

        if df["temperature"].replace(-999, np.nan).dropna().empty:
            continue

        messnetz, station_id, station_id_ergaenzung = parse_filename(file.name)

        if station_id_ergaenzung != "2/1":
            continue

        df = interpolate_missing(df)

        # ❗ SKIP nach Interpolation: immer noch alles leer
        if df["temperature"].dropna().empty:
            continue

        row = {
            "messnetz": messnetz,
            "station_id": station_id,
            "station_id_ergaenzung": station_id_ergaenzung
        }

        for col_name, ts in TARGET_TIMES.items():

            ts = pd.Timestamp(ts)

            if ts in df.index:
                row[col_name] = float(df.loc[ts, "temperature"])
            else:
                before = df[df.index < ts]["temperature"].tail(1)
                after = df[df.index > ts]["temperature"].head(1)

                values = []

                if len(before):
                    values.append(before.iloc[0])
                if len(after):
                    values.append(after.iloc[0])

                row[col_name] = float(np.mean(values)) if values else np.nan

        results.append(row)

    except Exception as e:
        print(f"Fehler bei {file.name}: {e}")


result_df = pd.DataFrame(results)

final_df = result_df.merge(
    metadata,
    on=["messnetz", "station_id", "station_id_ergaenzung"],
    how="left"
)

final_df = final_df[
    ["messnetz", "station_id", "station_id_ergaenzung", "lat", "lon", "temp_16", "temp_23"]
]

final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print(f"Datei gespeichert: {OUTPUT_FILE}")
print(f"Anzahl Stationen: {len(final_df)}")