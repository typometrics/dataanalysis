import re

with open('poster/poster.tex', 'r') as f:
    text = f.read()

# 1. bodyverticalshift=-2mm to 2mm in tabloid and tabgrey
text = text.replace('bodyverticalshift=-2mm, roundedcorners=0', 'bodyverticalshift=2mm, roundedcorners=0')

# 2. Side-by-side Wall of Shame layout and \vspace{0pt} fixes
# Find the case studies block and replace it entirely
case_studies_old = r"""% =====================================================================
% CASE STUDIES - three plots + wall of shame
% =====================================================================
\block{%
  \tabkicker{As usual}\\[-2mm]
  {\fontsize{60}{66}\selectfont\tabhead{German nails it. Naija wobbles. Arabic surprises. You?}}}{
  \raggedright
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    \includegraphics[width=\linewidth]{../plots/German_loglog}\\[3mm]
    {\fontsize{30}{34}\selectfont\tabhead{German -- textbook MAL}}\\[3mm]
    {\normalsize \textbf{slope = -0.17, R\textsuperscript{2} \textasciitilde\ 0.99}
     on the log-log fit. A near-perfect power law: every extra
     dependent shrinks the average constituent. \textbf{The cleanest
     fit in the sample} --- not the strongest slope, but the most
     orderly one. Is anyone surprised?}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    \includegraphics[width=\linewidth]{../plots/Naija_loglog}\\[3mm]
    {\fontsize{30}{34}\selectfont\tabhead{Naija -- mixed, asymmetric}}\\[3mm]
    {\normalsize Left and right dependents diverge wildly. A young
     pidgincreole refusing to fit one curve --- in fact the
     \textbf{strongest Anti-LMAL in the whole sample}
     ($\beta=+0.73$ preverbally).}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    \includegraphics[width=\linewidth]{../plots/Arabic_loglog}\\[3mm]
    {\fontsize{30}{34}\selectfont\tabhead{Arabic -- complex behavior}}\\[3mm]
    {\normalsize Arabic has a particularly low R\textsuperscript{2}. It follows MAL from $n=1$ to $3$, but becomes Anti-MAL from $n=3$ onwards.}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.235\linewidth}\raggedright
    {\fontsize{30}{34}\selectfont\tabhead{The wall of shame}}\\[3mm]
    {\normalsize Every row is a language, every column is the number of dependents $n$. 
     \textbf{Color intensity} shows average constituent size (red is larger, blue is smaller). 
     The arrows ($\downarrow$, $\uparrow$) tell you exactly where the law holds or quietly fails.}
    \vspace{3mm}
    \begin{center}
    \includegraphics[width=\linewidth,height=11cm,keepaspectratio]{../plots/mal_step_compliance_heatmap}
    \end{center}
  \end{minipage}

  \vspace{4mm}
}"""

case_studies_new = r"""% =====================================================================
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
}"""

if case_studies_old in text:
    text = text.replace(case_studies_old, case_studies_new)
else:
    print("Warning: Case studies block not found!")

# 3. 3-column layout for Teaser Row
teaser_old = r"""% =====================================================================
% TEASER ROW - four big questions on grey: three originals + PCA.
% =====================================================================
\begin{columns}
\column{0.25}
\useblockstyle{tabgrey}
\block{%
  \tabkicker{Linguists hate this trick}\\[2mm]
  \tablineTightH{75pt}{Got more dependents? Just make them smaller!}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/mal_n_total_curves_loglog}\\[3mm]
  {\normalsize In \textbf{most languages, yes.} The average size of
   a verb's dependents drops as the dependent count \textbf{n} grows
   --- exactly what Menzerath-Altmann predicts. \textbf{Each thin line
   = one of 186 languages}; the bold line is the cross-linguistic mean.}
}

\column{0.25}
\block{%
  \tabkicker{The truth they are hiding from you}\\[2mm]
  \tablineTightH{75pt}{Left and right are not equal!}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/mal_directional_curves_loglog}\\[3mm]
  {\normalsize Left dependents (top) stay \textbf{flat} as $n$ grows;
   right dependents (bottom) \textbf{collapse} from 5.2 down to 2.3.
   \textbf{Same law, two different worlds.} The verb is not
   ambidextrous --- it leans right.}
}

\column{0.25}
\block{%
  \tabkicker{Wake up, Indo-European!}\\[2mm]
  \tablineTightH{75pt}{Some families fail the test!}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/mal_compliance_categories}\\[3mm]
  {\normalsize \textbf{Only 38\% of languages} are fully MAL-conformant.
   \textbf{6.5\% are openly anti-MAL} --- and every family hides at
   least one rebel. Indo-European is no model student.}
}

\column{0.25}
\block{%
  \tabkicker{The dots they don't want you to connect}\\[2mm]
  \tablineTightH{75pt}{tiny points, BIG secrets!}}{
  \raggedright
  \includegraphics[width=\linewidth]{../plots/mal_pca_map}\\[3mm]
  {\normalsize Every language projected onto a 2D map of its MAL
   profile (PCA on 12 features: MAL/LMAL/RMAL at \(n=2..5\)).
   \textbf{PC1 = 65\%, PC2 = 13\%.} Indo-European clusters tightly;
   Japanese, Esperanto and Old Proven\c{c}al drift out as outliers.}
}
\useblockstyle{tabloid}
\end{columns}"""

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

if teaser_old in text:
    text = text.replace(teaser_old, teaser_new)
else:
    print("Warning: Teaser block not found!")

# 4. Masthead and Remove Row 5
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

if masthead_old in text:
    text = text.replace(masthead_old, masthead_new)
else:
    print("Warning: Masthead not found!")

call_to_action = r"""% =====================================================================
% CALL TO ACTION - QR row, full width below.
% =====================================================================
\block{%
  \tabkicker{It's 100\% free\textsuperscript{\textcolor{tabred}{*}}}\\[-2mm]
  {\fontsize{40}{44}\selectfont\tabhead{Come and find out how your UD language is doing!}}}{
  \raggedright
  \begin{minipage}[c]{0.15\linewidth}\centering
    \qrcode[height=5.5cm, level=H]{https://typometrics.elizia.net/menzerath}
  \end{minipage}\hfill
  \begin{minipage}[c]{0.83\linewidth}\raggedright
    \tablineTightH{55pt}{Scan, or come over to the laptop $\rightarrow$ \;\; \textmd{typometrics.elizia.net/menzerath}}\\[2mm]
    {\large \textbf{180 treebanks}, interactive PCA + family map +
      per-language curves + compliance ridgeline --- all online.
      \textcolor{tabmute}{\textcolor{tabred}{*}~\itshape Free as in
      beer, free as in speech, free as in dependency. Side effects
      may include sudden curiosity about Sanskrit verb valency and
      the unsettling realisation that left and right are not the
      same.}}
  \end{minipage}
}"""

if call_to_action in text:
    text = text.replace(call_to_action, "")
else:
    print("Warning: Call to action not found!")

with open('poster/poster.tex', 'w') as f:
    f.write(text)

print("Done")
