import os
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt

def compute_outer_effect(pos2num, pos2logsizes, lang, side='right'):
    if side == 'right':
        diag_keys = ['right_2_totright_2', 'right_3_totright_3', 'right_4_totright_4']
        rest_keys = ['right_1_totright_2', 'right_1_totright_3', 'right_2_totright_3']
    else:
        diag_keys = ['left_2_totleft_2', 'left_3_totleft_3', 'left_4_totleft_4']
        rest_keys = ['left_1_totleft_2', 'left_1_totleft_3', 'left_2_totleft_3']
        
    diag_vals = [np.exp(pos2logsizes[lang][k] / pos2num[lang][k]) for k in diag_keys if k in pos2logsizes.get(lang, {}) and k in pos2num.get(lang, {}) and pos2num[lang][k] > 0]
    rest_vals = [np.exp(pos2logsizes[lang][k] / pos2num[lang][k]) for k in rest_keys if k in pos2logsizes.get(lang, {}) and k in pos2num.get(lang, {}) and pos2num[lang][k] > 0]
    
    if diag_vals and rest_vals:
        diag_gm = np.exp(np.mean(np.log(diag_vals)))
        rest_gm = np.exp(np.mean(np.log(rest_vals)))
        return diag_gm / rest_gm
    return np.nan

with open('data/all_langs_position2num.pkl', 'rb') as f:
    pos2num = pickle.load(f)
with open('data/all_langs_position2logsizes.pkl', 'rb') as f:
    pos2logsizes = pickle.load(f)

df_vo = pd.read_csv('data/vo_vs_hi_scores.csv')

right_effects = []
left_effects = []
for code in df_vo['language_code']:
    right_effects.append(compute_outer_effect(pos2num, pos2logsizes, code, 'right'))
    left_effects.append(compute_outer_effect(pos2num, pos2logsizes, code, 'left'))

df_vo['Right_Outer_Effect'] = right_effects
df_vo['Left_Outer_Effect'] = left_effects

print(df_vo[['language_code', 'vo_score', 'Right_Outer_Effect', 'Left_Outer_Effect']].head())
