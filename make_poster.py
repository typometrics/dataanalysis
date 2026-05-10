import re

with open('poster/poster.tex', 'r') as f:
    text = f.read()

# 1. bodyverticalshift=-2mm to 2mm in tabloid and tabgrey
text = text.replace('bodyverticalshift=-2mm, roundedcorners=0', 'bodyverticalshift=2mm, roundedcorners=0')

# 2. Update MASTHEAD to include QR code
masthead_old = r"""% =====================================================================
% MASTHEAD - plain block, no grey background
% =====================================================================
\block{}{
  \begin{center}
  {\fontsize{75}{85}\selectfont\tabhead{%
    The universal that wasn't:\\[5mm]
    a large-scale treebank study of Menzerath-Altmann
  }}\\[10mm]
  {\fontsize{30}{36}\selectfont\textbf{%
    Pegah Faghiri\textsuperscript{1,2} \quad
    Kim Gerdes\textsuperscript{2} \quad
    Sylvain Kahane\textsuperscript{1,3}}}\\[4mm]
  {\fontsize{22}{28}\selectfont
    \textsuperscript{1}Modyco, CNRS \& Paris Nanterre University \quad
    \textsuperscript{2}LISN, CNRS \& Paris-Saclay University \quad
    \textsuperscript{3}Institut Universitaire de France}\\[5mm]
  \rule{\linewidth}{2pt}
  \end{center}
}"""

masthead_new = r"""% =====================================================================
% MASTHEAD - plain block, no grey background
% =====================================================================
\block{}{
  \begin{minipage}[c]{0.80\linewidth}
    \begin{center}
    {\fontsize{75}{85}\selectfont\tabhead{%
      The universal that wasn't:\\[5mm]
      a large-scale treebank study of Menzerath-Altmann
    }}\\[10mm]
    {\fontsize{30}{36}\selectfont\textbf{%
      Pegah Faghiri\textsuperscript{1,2} \quad
      Kim Gerdes\textsuperscript{2} \quad
      Sylvain Kahane\textsuperscript{1,3}}}\\[4mm]
    {\fontsize{22}{28}\selectfont
      \textsuperscript{1}Modyco, CNRS \& Paris Nanterre University \quad
      \textsuperscript{2}LISN, CNRS \& Paris-Saclay University \quad
      \textsuperscript{3}Institut Universitaire de France}
    \end{center}
  \end{minipage}\hfill
  \begin{minipage}[c]{0.18\linewidth}
    \begin{center}
      \qrcode[height=5.5cm, level=H]{https://typometrics.elizia.net/menzerath}\\[3mm]
      {\fontsize{24}{28}\selectfont \textbf{typometrics.elizia.net}}\\[2mm]
      {\large Scan to see how your language is doing!\\ Interactive maps \& curves online.}
    \end{center}
  \end{minipage}\\[5mm]
  \rule{\linewidth}{2pt}
}"""
text = text.replace(masthead_old, masthead_new)

# 3. Teaser Row 3-column layout
teaser_pattern = r"% =====================================================================\n% TEASER ROW.*?\useblockstyle{tabloid}\n\\end{columns}"
teaser_new = r"""% =====================================================================
% TEASER ROW - four big questions on grey: three originals + PCA.
% =====================================================================
\begin{columns}
\column{0.48}
\useblockstyle{tabgrey}
\block{%
  \tabkicker{Linguists hate this trick}\\[2mm]
  \tablineTightH{75pt}{Got more dependents? Just make them smaller!}}{
  \raggedright
  \vspace{0pt}
  \includegraphics[width=\linewidth]{../plots/mal_combined_curves_1x3}\\[3mm]
  \begin{minipage}[t]{0.48\linewidth}\raggedright
    \vspace{0pt}
    {\fontsize{30}{34}\selectfont\tabhead{Wait, it's not a universal?}}\\[3mm]
    {\normalsize In \textbf{most languages, yes.} The average size of a verb's dependents drops as $n$ grows --- exactly what Menzerath-Altmann predicts. \textbf{Each thin line = one of 186 languages}; the bold line is the cross-linguistic mean.}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.48\linewidth}\raggedright
    \vspace{0pt}
    {\fontsize{30}{34}\selectfont\tabhead{Left vs right asymmetry}}\\[3mm]
    {\normalsize Left dependents stay \textbf{flat} as $n$ grows; right dependents \textbf{collapse} from 5.2 down to 2.3. \textbf{Same law, two different worlds.} The verb is not ambidextrous --- it leans right.}
  \end{minipage}
}

\column{0.26}
\block{%
  \tabkicker{Wake up, Indo-European!}\\[2mm]
  \tablineTightH{75pt}{Some families fail the test!}}{
  \raggedright
  \vspace{0pt}
  \includegraphics[width=\linewidth]{../plots/mal_compliance_categories}\\[3mm]
  {\fontsize{30}{34}\selectfont\tabhead{Where do the laws break?}}\\[3mm]
  {\normalsize \textbf{Only 38\% of languages} are fully MAL-conformant.
   \textbf{6.5\% are openly anti-MAL} --- and every family hides at least one rebel. Indo-European is no model student.}
}

\column{0.26}
\block{%
  \tabkicker{The dots they don't want you to connect}\\[2mm]
  \tablineTightH{75pt}{tiny points, BIG secrets!}}{
  \raggedright
  \vspace{0pt}
  {\centering \includegraphics[width=0.6\linewidth]{../plots/mal_pca_map}\par}
  \vspace{3mm}
  {\fontsize{30}{34}\selectfont\tabhead{Typological PCA clustering}}\\[3mm]
  {\normalsize Every language projected onto a 2D map of its MAL
   profile (PCA on 12 features: MAL/LMAL/RMAL at \(n=2..5\)).
   \textbf{PC1 = 65\%, PC2 = 13\%.} Indo-European clusters tightly;
   Japanese, Esperanto and Old Proven\c{c}al drift out as outliers.}
}
\useblockstyle{tabloid}
\end{columns}"""
text = re.sub(teaser_pattern, teaser_new, text, flags=re.DOTALL)

# 4. Remove SMOKING GUN row, add Distributions row. Wait, I should just replace everything from SMOKING-GUN down!
# Let's replace the bottom half:
bottom_pattern = r"% =====================================================================\n% SMOKING-GUN BAND.*"
bottom_new = r"""% =====================================================================
% DISTRIBUTIONS AND DIRECTIONALITY 
% =====================================================================
\begin{columns}
\column{0.25}
\block{%
  \tabkicker{Family Matters}\\[2mm]
  \tablineTightH{60pt}{Is MAL just a European bias?}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/poster_mal_effect_by_family}\\[3mm]
  {\normalsize Distribution of the MAL effect ($\beta$) across language families. Indo-European clearly dominates the MAL-compliant zone.}
}

\column{0.25}
\block{%
  \tabkicker{The Euro-Centric Law}\\[2mm]
  \tablineTightH{60pt}{IE vs. The Rest}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/poster_ie_vs_non_ie}\\[3mm]
  {\normalsize Indo-European languages exhibit a significantly stronger and more consistent MAL effect compared to all other families combined.}
}

\column{0.25}
\block{%
  \tabkicker{Before and After}\\[2mm]
  \tablineTightH{60pt}{Why left and right differ}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/poster_directional_vs_vo}\\[3mm]
  {\normalsize RMAL vs VO/OV order. The right-side collapse is strongest when verbs precede objects. The syntax restricts dependent sizes asymmetrically.}
}

\column{0.25}
\block{%
  \tabkicker{Universal truth or statistical artifact?}\\[2mm]
  \tablineTightH{60pt}{The Beta spectrum}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/mal_universality_test_beta}\\[3mm]
  {\normalsize Most $\beta$ values are indeed negative (MAL-compliant), but a massive chunk straddles zero. Is it a law, or just a heavy statistical lean?}
}
\end{columns}

% =====================================================================
% CASE STUDIES - three plots + wall of shame
% =====================================================================
\block{%
  \tabkicker{As usual}\\[-2mm]
  {\fontsize{60}{66}\selectfont\tabhead{German nails it. Naija wobbles. Arabic surprises. You?}}}{
  \raggedright
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    \vspace{0pt}
    \includegraphics[width=\linewidth]{../plots/German_loglog}\\[3mm]
    {\fontsize{30}{34}\selectfont\tabhead{German -- textbook MAL}}\\[3mm]
    {\normalsize \textbf{slope = -0.17, R\textsuperscript{2} \textasciitilde\ 0.99}
     on the log-log fit. A near-perfect power law: every extra
     dependent shrinks the average constituent. \textbf{The cleanest
     fit in the sample} --- not the strongest slope, but the most
     orderly one. Is anyone surprised?}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    \vspace{0pt}
    \includegraphics[width=\linewidth]{../plots/Naija_loglog}\\[3mm]
    {\fontsize{30}{34}\selectfont\tabhead{Naija -- mixed, asymmetric}}\\[3mm]
    {\normalsize Left and right dependents diverge wildly. A young
     pidgincreole refusing to fit one curve --- in fact the
     \textbf{strongest Anti-LMAL in the whole sample}
     ($\beta=+0.73$ preverbally).}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    \vspace{0pt}
    \includegraphics[width=\linewidth]{../plots/Arabic_loglog}\\[3mm]
    {\fontsize{30}{34}\selectfont\tabhead{Arabic -- complex behavior}}\\[3mm]
    {\normalsize Arabic has a particularly low R\textsuperscript{2}. It follows MAL from $n=1$ to $3$, but becomes Anti-MAL from $n=3$ onwards.}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    \vspace{0pt}
    \begin{minipage}[t]{0.48\linewidth}\raggedright
      \vspace{0pt}
      \includegraphics[width=\linewidth]{../plots/mal_step_compliance_heatmap}
    \end{minipage}\hfill
    \begin{minipage}[t]{0.48\linewidth}\raggedright
      \vspace{0pt}
      {\fontsize{30}{34}\selectfont\tabhead{The wall of shame}}\\[3mm]
      {\normalsize Every row is a language, every column is the number of dependents $n$. 
       \textbf{Color intensity} shows average constituent size (red is larger, blue is smaller). 
       The arrows ($\downarrow$, $\uparrow$) tell you exactly where the law holds or quietly fails.}
    \end{minipage}
  \end{minipage}

  \vspace{4mm}
}

\end{document}
"""
text = re.sub(bottom_pattern, bottom_new, text, flags=re.DOTALL)

with open('poster/poster.tex', 'w') as f:
    f.write(text)

print("Restored poster.tex successfully!")
