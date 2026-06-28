import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv("assignment_05/data/zonale_statistik.csv")

plt.figure(figsize=(10,5))
sns.boxplot(data=df, x="LCZ", y="_mean")
plt.xticks(rotation=45)
plt.title("LCZ Temperatur (Polygon-Mittelwerte)")
plt.show()