#pwd
# cd ... P1_DiceSimulatorStats
# python3 -m venv .venv
# source .venv/bin/activate
# python DiceSimulator.py
# if need libraries: eg. python -m pip install pandas -> within the venv

import random
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def roll_dice():
    return random.randint(1, 6), random.randint(1, 6)

# ---- Data
result = [roll_dice() for _ in range(10000)] # Nr of simulations
table = pd.DataFrame(result, columns=['Dice 1', 'Dice 2'])

# 1) Sum of both dice
table['Sum'] = table['Dice 1'] + table['Dice 2']

# 2) Frequency of each face (both dice combined)
face_series = pd.concat([table['Dice 1'], table['Dice 2']], ignore_index=True)
face_freq = face_series.value_counts().sort_index().to_frame('Frequency')
face_freq['Relative %'] = (face_freq['Frequency'] / (len(table) * 2) * 100).round(2)

# Map face frequencies/percentages into each row
face_freq_map = face_freq['Frequency'].to_dict()
rel_freq_map  = face_freq['Relative %'].to_dict()
table['Freq_D1'] = table['Dice 1'].map(face_freq_map)
table['Freq_D2'] = table['Dice 2'].map(face_freq_map)
table['Rel%_D1'] = table['Dice 1'].map(rel_freq_map)
table['Rel%_D2'] = table['Dice 2'].map(rel_freq_map)

# 3) Global stats over the *Sum* column (mean/std/min/max)
global_stats = pd.Series({
    'Global mean': table['Sum'].mean(),
    'Global std' : table['Sum'].std(),
    'Global min' : table['Sum'].min(),
    'Global max' : table['Sum'].max(),
})
table = table.assign(
    GlobalMean = global_stats['Global mean'],
    GlobalStd  = global_stats['Global std'],
    GlobalMin  = global_stats['Global min'],
    GlobalMax  = global_stats['Global max'],
)

# 4) Frequency of the sums  <<< you were missing this block
sum_freq = table['Sum'].value_counts().sort_index().to_frame('Sum Frequency')
sum_freq['Sum Relative %'] = (sum_freq['Sum Frequency'] / len(table) * 100).round(2)

# Map sum frequencies/percentages into each row
sum_freq_map = sum_freq['Sum Frequency'].to_dict()
sum_rel_map  = sum_freq['Sum Relative %'].to_dict()
table['Freq_Sum'] = table['Sum'].map(sum_freq_map)
table['Rel%_Sum'] = table['Sum'].map(sum_rel_map)

# ---- Output
print("\n== First rows ==")
print(table.head())
print("\n== Face frequency ==")
print(face_freq)
print("\n== Sum frequency ==")
print(sum_freq)

# ---- Visualization
sns.histplot(table['Sum'], bins=range(2,14), stat='probability', discrete=True)
plt.title("Empirical PMF of Dice Sums")
plt.xlabel("Sum")
plt.ylabel("Probability")
plt.show()

# Normal PDFs with different std deviations

def normal_pdf(x, mu, sigma):
    return 1.0/(sigma*np.sqrt(2*np.pi)) * np.exp(-0.5*((x-mu)/sigma)**2)

mu = 7.0                      # center near the dice-sum mean
sigmas = [1.5, 2.0, 2.415, 3.0]  # pick a few std devs (√(35/6)≈2.415 for 2 dice)

x = np.linspace(mu - 5*max(sigmas), mu + 5*max(sigmas), 800)

plt.figure()
for s in sigmas:
    plt.plot(x, normal_pdf(x, mu, s), label=f"μ={mu}, σ={s}")
plt.title("Normal PDFs for different σ")
plt.xlabel("x")
plt.ylabel("density")
plt.legend()
plt.show()