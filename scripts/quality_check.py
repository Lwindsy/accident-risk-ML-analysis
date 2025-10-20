# 中文：数据质量快速检查脚本
# English: Quick data-quality checker for Phase 1

import pandas as pd
import os

path = "data/raw/driving_sample.csv"
if not os.path.exists(path):
    raise FileNotFoundError(f"{path} not found. Run 'make download' first.")

df = pd.read_csv(path)
print("✅ File loaded:", df.shape)
print("\nMissing values per column:")
print(df.isnull().sum())

print("\nNumeric summary:")
print(df.describe())
