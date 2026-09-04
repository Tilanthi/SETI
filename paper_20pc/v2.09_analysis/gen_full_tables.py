rows = open('/workspace/SETI/paper_20pc/appendix_rows_v209.tex').read().strip('\n').split('\n')
print(f'{len(rows)} rows total')

CHUNK = 34  # rows per table part, tuned to roughly match old page density
chunks = [rows[i:i+CHUNK] for i in range(0, len(rows), CHUNK)]
print(f'{len(chunks)} table parts')

out = []
header = r"""Target & Band & Sp.\ type & Dist.\ (pc) & Freq.\ range (GHz) & N$_{\rm spw}$ & EIRP$_{\rm min}$ (W) & Flux (mJy) & RMS (mJy) & Notes \\
\hline"""

labels = ['tab:full'] + [f'tab:full{i}' for i in range(2, len(chunks)+1)]

caption1 = r"""\caption{Per-target/band results, ordered by distance. Band numbers are
given without the customary ``B'' prefix to avoid confusion with B-type
spectral classifications elsewhere in the table. Frequency range is in
GHz; N$_{\rm spw}$ is the total number of spectral windows configured
simultaneously in the observation (or, where that count is not directly
available in the input metadata, the number of windows actually
searched, a lower bound). EIRP$_{\rm min}$ (W) is the minimum
EIRP that would register as a $5\sigma$ detection in that spectral
window (\S\ref{sec:method}), primary-beam corrected. Flux is the measured
peak continuum flux density for a detection, or the resulting $5\sigma$
upper limit (denoted ``$<$''), also primary-beam corrected; RMS is the
underlying (post-correction) continuum image rms noise; both in mJy. For
a target with more than one searched spectral window, its single
continuum measurement (common to all windows in that band) is given once,
in the first row. Both automatically-flagged technosignature candidates
are noted directly in the Notes column; see \S\ref{sec:results} for their
disposition. Spectral types marked $^\dagger$ are approximate, derived
from the Gaia DR3 effective temperature via the Pecaut \& Mamajek (2013)
main-sequence temperature scale rather than a literature classification
(most such targets are newly added this version); those marked $^\ddagger$
have no Gaia effective temperature available and are given only a coarse
class. This table spans %d parts (Tables~\ref{%s}--\ref{%s})
for typesetting reasons only; it is a single table.}""" % (len(chunks), labels[0], labels[-1])

for i, chunk in enumerate(chunks):
    lbl = labels[i]
    out.append(r"\begin{table*}")
    out.append(r"\centering")
    out.append(r"\scriptsize")
    if i == 0:
        out.append(caption1)
    else:
        out.append(r"\caption{Table~\ref{tab:full} continued.}")
    out.append(rf"\label{{{lbl}}}")
    out.append(r"\begin{tabularx}{\textwidth}{@{}l c c c c c c c c X@{}}")
    out.append(r"\hline")
    out.append(header)
    out.extend(chunk)
    out.append(r"\hline")
    out.append(r"\end{tabularx}")
    out.append(r"\end{table*}")
    out.append("")

text = '\n'.join(out)
open('/workspace/SETI/paper_20pc/full_tables_v209.tex','w').write(text)
print('wrote', len(text), 'chars')
print('labels:', labels)
