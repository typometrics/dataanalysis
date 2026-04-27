#!/usr/bin/env python3
"""Generate the MAL-profile PCA scatter for the poster.

Uses the same code path as the website (mal_site._pca_2d) over the
12 MAL/LMAL/RMAL features at n=2..5 from data/lang2MAL_full.pkl, and
labels the points with language names using the local adjustText helper.

Output: plots/mal_pca_map.png
"""
from __future__ import annotations

import os
import pickle
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from adjustText import adjust_text  # noqa: E402  (local helper)


def _pca_2d(feature_dict):
    """Mirror of mal_site._pca_2d, also returning the V^T loading matrix and kept-col mask."""
    codes = sorted(feature_dict.keys())
    X = np.array([feature_dict[c] for c in codes], dtype=float)
    keep = ~np.all(np.isnan(X), axis=0)
    X = X[:, keep]
    col_means = np.nanmean(X, axis=0)
    nan_idx = np.where(np.isnan(X))
    X[nan_idx] = np.take(col_means, nan_idx[1])
    X = X - X.mean(axis=0, keepdims=True)
    stds = X.std(axis=0, keepdims=True)
    stds[stds == 0] = 1.0
    X = X / stds
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    coords = U[:, :2] * S[:2]
    explained = (S[:2] ** 2) / ((S ** 2).sum() or 1.0)
    return codes, coords, explained, Vt[:2], keep


def main():
    data_dir = os.path.join(ROOT, "data")
    plots_dir = os.path.join(ROOT, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    with open(os.path.join(data_dir, "metadata.pkl"), "rb") as f:
        meta = pickle.load(f)
    langNames = meta["langNames"]
    langnameGroup = meta["langnameGroup"]

    with open(os.path.join(data_dir, "lang2MAL_full.pkl"), "rb") as f:
        lang2MAL = pickle.load(f)

    total = {l: d["total"] for l, d in lang2MAL.items() if d.get("total")}
    left = {l: d["left"] for l, d in lang2MAL.items() if d.get("left")}
    right = {l: d["right"] for l, d in lang2MAL.items() if d.get("right")}

    NS = (2, 3, 4, 5)
    src_labels = ("M", "L", "R")
    sources = [total, left, right]
    feat_names = [f"{lab}{n}" for lab in src_labels for n in NS]
    codes = sorted(c for c, d in total.items() if d and 2 in d)
    feat = {}
    for c in codes:
        row = []
        for src in sources:
            d = src.get(c, {}) or {}
            for n in NS:
                row.append(d.get(n, np.nan))
        feat[c] = row

    codes, coords, exp, loadings, keep = _pca_2d(feat)
    kept_names = [n for n, k in zip(feat_names, keep) if k]

    fam_of = {c: langnameGroup.get(langNames.get(c, c), "Other") for c in codes}
    fams = sorted(set(fam_of.values()))
    cmap = plt.get_cmap("tab10")
    fam_color = {f: cmap(i % 10) for i, f in enumerate(fams)}

    fig, ax = plt.subplots(figsize=(10, 10))
    for f in fams:
        mask = [fam_of[c] == f for c in codes]
        if any(mask):
            ax.scatter(
                coords[mask, 0], coords[mask, 1],
                c=[fam_color[f]], s=120, alpha=0.85,
                label=f, edgecolors="white", linewidths=0.7,
            )

    # Language-name labels: every language, repelled.
    texts = []
    for i, c in enumerate(codes):
        name = langNames.get(c, c)
        texts.append(ax.text(
            coords[i, 0], coords[i, 1], name,
            fontsize=8, color="#222", alpha=0.9,
        ))
    adjust_text(
        texts, ax=ax,
        arrowprops=dict(arrowstyle="-", color="#888", lw=0.4, alpha=0.6),
        expand_text=(1.05, 1.2), expand_points=(1.2, 1.4),
        force_text=(0.4, 0.6), force_points=(0.3, 0.4),
        lim=200,
    )

    # --- Biplot loadings: scale V^T[:2] so the longest arrow ~ 70 % of axis range.
    xr = coords[:, 0].max() - coords[:, 0].min()
    yr = coords[:, 1].max() - coords[:, 1].min()
    arr_norm = np.sqrt((loadings ** 2).sum(axis=0)).max()
    scale = 0.45 * min(xr, yr) / (arr_norm or 1.0)
    fam_palette = {"M": "#cc0000", "L": "#1f4e79", "R": "#2e7d32"}
    arrow_texts = []
    for j, name in enumerate(kept_names):
        x, y = loadings[0, j] * scale, loadings[1, j] * scale
        col = fam_palette.get(name[0], "#444")
        ax.annotate(
            "", xy=(x, y), xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color=col, lw=2.0, alpha=0.9),
            zorder=5,
        )
        arrow_texts.append(ax.text(
            x * 1.08, y * 1.08, name,
            color=col, fontsize=13, fontweight="bold",
            ha="center", va="center", zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85),
        ))

    ax.set_xlabel(f"PC1 ({exp[0] * 100:.0f}%)", fontsize=18)
    ax.set_ylabel(f"PC2 ({exp[1] * 100:.0f}%)", fontsize=18)
    ax.set_title(
        f"PCA of MAL profile — 12 features (MAL/LMAL/RMAL × n=2..5), "
        f"{len(codes)} languages",
        fontsize=17,
    )
    ax.legend(loc="best", fontsize=11, frameon=True, ncol=1)
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=13)
    fig.tight_layout()

    out = os.path.join(plots_dir, "mal_pca_map.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    print(f"wrote {out}  (PC1={exp[0] * 100:.1f}%, PC2={exp[1] * 100:.1f}%, "
          f"n_lang={len(codes)})")


if __name__ == "__main__":
    main()
