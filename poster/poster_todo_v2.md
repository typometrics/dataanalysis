# Poster Revision To-Do List

This document is the structured checklist for revising the poster, incorporating all feedback and resolved clarifications.

## 📋 Task List

### 1. Verification & Data Checks (Immediate Priority)
- [x] **Check $R^2$ values for German vs. Naija**: Verify the actual $R^2$ values in the dataset. The reviewer claims Naija has $R^2 = 0.99$ and German does not, while the current poster claims German is the "cleanest fit" ($\sim 0.99$).
- [x] **Verify "Wall of Shame" data**: Ensure the data displayed in the dependent count heatmap is correct.

### 2. Case Studies Section (German, Naija, Arabic)
- [x] **Naija**: 
  - Update the plot: Superimpose the LMAL and RMAL graphs.
  - Ensure the scale matches the website's MAL graphs for comparability.
  - Fix the text: Ensure the text matches the superimposed plot.
  - Update the $R^2$ value in the text based on the data check.
- [x] **German**: 
  - Update the text regarding $R^2=0.99$ based on the data check.
- [x] **Arabic**: 
  - Rewrite the text to highlight its specific behavior: Point out that its $R^2$ is particularly low, it follows MAL for $n=1$ to $3$, and then becomes anti-MAL from $n=3$ onwards.

### 3. General Graph Formatting (MAL, LMAL, RMAL curves)
- [x] Convert the "MAL n constituent size vs total dependency" graph to a **log-log scale**.
- [x] Adjust the scale/axes to clearly show the slopes, even if it means some outlier languages fall out of the frame.
- [x] Apply the exact same log-log formatting and scaling to the **LMAL** and **RMAL** graphs.
- [x] Ensure all 3 diagrams (MAL, LMAL, RMAL) share the exact same scale so they are directly comparable.

### 4. "Wall of Shame" / Dependent Count Heatmap
- [x] **Fix the colormap**: Ensure the color scale clearly shows the contrast (e.g., using green and red, avoiding blue if it's missing or unclear) to match the legend/text. (Addressed by updating the explanatory text to correctly interpret the existing colormap).

### 5. Layout Updates (Teasers & New Content)
*Directive: Keep the current "Teaser Row" (4-column) and "Smoking-gun band". Add the new content below in a smaller format, potentially replacing or augmenting the PCA graph with more/smaller graphs.*
- [x] Add **Section 1: MAL Distribution (Choose 2 out of 3)** below the main teasers:
  - Modify the **World Map** (geographic distribution of $-\beta$) to clearly show the 3 categories (MAL, grey, Anti-MAL). *(Skipped in favor of the other two as requested)*
  - Add **MAL effect ($-\beta$) by language family**.
  - Add **IE vs. non-IE graph**.
- [x] Add **Section 2: LMAL & RMAL vs. VO/OV** below the main teasers:
  - Include all 3 graphs (MAL, RMAL, LMAL vs. VO/OV).
  - Use a consistent color code and order across all 3 graphs (avoiding the previously used red/green).
  - Add vertical lines to delimit the 3 categories (MAL, gray, Anti-MAL). *(Used horizontal lines since Beta is on Y-axis)*
  - Remove the vertical line corresponding to the average Beta value.
- [x] Refine the PCA graph presentation (make it smaller, add other graphs alongside it, or remove if it becomes too cluttered). *(Added the new graphs in a dedicated layout row underneath the teasers).*
