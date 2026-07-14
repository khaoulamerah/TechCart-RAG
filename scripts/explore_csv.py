
import pandas as pd
from pathlib import Path

def explore(filepath, name):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    
    df = pd.read_csv(filepath, encoding='utf-8-sig', on_bad_lines='skip')
    
    print(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\nColumns:")
    for col in df.columns:
        nulls = df[col].isnull().sum()
        pct = (nulls/len(df))*100
        sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else "N/A"
        print(f"  {col:<40} nulls={nulls:4} ({pct:4.1f}%)  sample={str(sample)[:40]}")
    
    print(f"\nFirst row:")
    print(df.iloc[0].to_dict())

explore("data/raw/All_GPUs.csv", "GPUs")
explore("data/raw/Intel_CPUs.csv", "Intel CPUs")