"""
generate_mal_examples.py — paper-aligned per-language sample sentences for the
UDW26 MAL companion site.

Output layout (everything inside the analyses site):

    <output_dir>/<lang_code>/
        index.html               — MAL_n / LMAL_n / RMAL_n table; each cell links
                                   to the corresponding samples/<dir>_n<N>.html
        samples/
            mal_nN.html          — verbs with N total dependents
            lmal_nN.html         — verbs with N left dependents (any right)
            rmal_nN.html         — verbs with N right dependents (any left)

Design notes
------------
- Bucket definitions match exactly the MAL/LMAL/RMAL definitions used in
  ``mal_html_report``: MAL_n bins on (left+right)=n, LMAL_n bins on totleft=n
  (any right), RMAL_n bins on totright=n (any left).
- Verb identification, dependent set, span sizes and "bastard" handling are
  delegated to ``conll_processing.extract_verb_config_examples`` and
  ``extract_treebank_configs.get_span_size`` so the displayed numbers stay
  consistent with the values aggregated into MAL_n.
- The older helix / "AnyOtherSide" generator (``generate_html_examples.py``,
  output ``html_examples/``) is kept untouched and intentionally not used
  here — that pipeline is for a separate study.
"""

from __future__ import annotations

import argparse
import functools
import html
import multiprocessing
import os
import pickle
import random
from collections import defaultdict

from tqdm import tqdm

import conll_processing
from conll import conllFile2trees
from extract_treebank_configs import get_span_size


# ---------------------------------------------------------------------------
# Constants / styling
# ---------------------------------------------------------------------------

REACTIVE_DEP_TREE_SCRIPT = (
    'https://unpkg.com/reactive-dep-tree/dist/reactive-dep-tree.umd.js'
)

DIRECTIONS = ('mal', 'lmal', 'rmal')
DIRECTION_LONG = {
    'mal': 'MAL (any side)',
    'lmal': 'LMAL (left side)',
    'rmal': 'RMAL (right side)',
}
DIRECTION_DESC = {
    'mal': ('verbs that have exactly <b>{n}</b> dependents in total '
            '(left + right combined)'),
    'lmal': ('verbs that have exactly <b>{n}</b> left dependents '
             '(right side may be anything)'),
    'rmal': ('verbs that have exactly <b>{n}</b> right dependents '
             '(left side may be anything)'),
}

PAGE_CSS = """
body { font-family: Arial, sans-serif; max-width: 1100px; margin: 20px auto;
       padding: 0 20px; color: #222; }
h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
h2 { color: #34495e; margin-top: 28px; border-left: 4px solid #3498db; padding-left: 10px; }
.info { background: #f0f8ff; border: 1px solid #d0e0f0; padding: 12px 16px;
        border-radius: 5px; margin: 14px 0 22px 0; font-size: 14px; }
.info code, .info b { font-family: Consolas, monospace; }
.example { margin-bottom: 28px; padding: 16px; border: 1px solid #ddd;
           border-radius: 5px; background: #fff; }
.example-meta { color: #666; font-size: 12px; margin-bottom: 8px; }
.back { font-size: 13px; }
table.mal-table { border-collapse: collapse; margin: 10px 0 20px 0; }
table.mal-table th, table.mal-table td { border: 1px solid #ddd; padding: 6px 10px;
                                          text-align: center; font-size: 13px; }
table.mal-table th { background: #4CAF50; color: white; }
table.mal-table td.lang-label { background: #f5f5f5; font-weight: bold; }
table.mal-table a { text-decoration: none; color: #1976d2; }
table.mal-table a:hover { text-decoration: underline; }
.no-data { color: #999; font-style: italic; padding: 20px 0; }
"""


# ---------------------------------------------------------------------------
# Tree → reactive-dep-tree HTML
# ---------------------------------------------------------------------------

def _tree_to_reactive(tree, verb_id, dep_ids, dep_sizes):
    """Render one verb-rooted example as reactive-dep-tree HTML.

    ``tree`` is the conll_processing tree object (dict with int keys + helpers).
    """
    sorted_ids = sorted(i for i in tree if isinstance(i, int))
    forms = [tree[i].get('t', '_') for i in sorted_ids]
    upos = [tree[i].get('tag', '_') for i in sorted_ids]
    heads = [list(tree[i].get('gov', {}).keys())[0] if tree[i].get('gov') else 0
             for i in sorted_ids]
    deprels = [list(tree[i].get('gov', {}).values())[0] if tree[i].get('gov') else 'root'
               for i in sorted_ids]

    sentence_text = ' '.join(forms)
    lines = [f'# text = {sentence_text}']
    for i, (form, pos, head, rel) in enumerate(
            zip(forms, upos, heads, deprels), 1):
        misc = []
        if i == verb_id:
            misc.append('highlight=red')
        elif i in dep_ids:
            misc.append('highlight=green')
            sz = dep_sizes.get(i)
            if sz is not None:
                misc.append(f'span={sz}')
        misc_str = '|'.join(misc) if misc else '_'
        lines.append(f"{i}\t{form}\t{form}\t{pos}\t{pos}\t_\t{head}\t{rel}\t_\t{misc_str}")

    conll_str = '\n'.join(lines).replace('"', '&quot;')
    return (
        f'<reactive-dep-tree interactive="true" '
        f'shown-features="UPOS,LEMMA,FORM,MISC.span" '
        f'conll="{conll_str}"></reactive-dep-tree>'
    )


# ---------------------------------------------------------------------------
# Per-language example collection
# ---------------------------------------------------------------------------

def _iter_trees_round_robin(conll_files):
    """Yield ``(filename, tree)`` interleaved across all input files.

    Round-robin parsing guarantees that when a language has multiple
    treebanks, the first sentences seen come from different sources rather
    than draining the first file completely. This is important because
    ``max_sentences`` may stop the walk before later files are reached.
    """
    iterators = []
    for fn in conll_files:
        if not os.path.exists(fn):
            continue
        try:
            iterators.append((fn, iter(conllFile2trees(fn))))
        except Exception as exc:
            print(f"  ! parse error opening {fn}: {exc}")
    while iterators:
        next_round = []
        for fn, it in iterators:
            try:
                tree = next(it)
            except StopIteration:
                continue
            except Exception as exc:
                print(f"  ! parse error in {fn}: {exc}")
                continue
            yield fn, tree
            next_round.append((fn, it))
        iterators = next_round


def _collect_examples(conll_files, max_per_bucket=20, max_sentences=None,
                      seed=0):
    """Walk the CoNLL files of one language and bucket verb instances.

    Returns ``{(direction, n): [example_dict, ...]}``. Each example is a dict
    with keys ``html`` (the rendered reactive-dep-tree snippet),
    ``source`` (basename of the conllu file), ``n_left``, ``n_right``,
    ``mean_span``. Sentences are walked round-robin across input files so
    that all treebanks of a language contribute diversely to the sample.
    """
    rng = random.Random(seed)
    # Reservoir per bucket
    buckets: dict = defaultdict(list)
    bucket_counts: dict = defaultdict(int)

    sentences_seen = 0
    try:
        for conll_filename, tree in _iter_trees_round_robin(conll_files):
            if max_sentences is not None and sentences_seen >= max_sentences:
                break
            sentences_seen += 1
            tree.addspan(exclude=['punct'], compute_bastards=True)
            verb_configs = conll_processing.extract_verb_config_examples(
                tree, include_bastards=True)
            # ``extract_verb_config_examples`` emits the same verb several
            # times (once per matching config pattern: exact, anyleft,
            # anyright, anyboth). For example collection we only want one
            # entry per verb token, so dedupe by ``verb_id`` here.
            seen_verbs = set()
            for config, verb_id, dep_ids in verb_configs:
                if verb_id in seen_verbs:
                    continue
                seen_verbs.add(verb_id)
                n_left = sum(1 for d in dep_ids if d < verb_id)
                n_right = sum(1 for d in dep_ids if d > verb_id)
                n_tot = n_left + n_right
                if n_tot == 0:
                    continue
                dep_sizes = {k: get_span_size(tree, k, True) for k in dep_ids}
                rendered = None  # render lazily on first store

                def _render():
                    return _tree_to_reactive(tree, verb_id, dep_ids, dep_sizes)

                src = os.path.basename(conll_filename)
                mean_span = (sum(dep_sizes.values()) / len(dep_sizes)
                             if dep_sizes else 0.0)

                for key in (('mal', n_tot),
                            ('lmal', n_left) if n_left > 0 else None,
                            ('rmal', n_right) if n_right > 0 else None):
                    if key is None:
                        continue
                    bucket_counts[key] += 1
                    existing = buckets[key]
                    if len(existing) < max_per_bucket:
                        if rendered is None:
                            rendered = _render()
                        existing.append({
                            'html': rendered,
                            'source': src,
                            'n_left': n_left,
                            'n_right': n_right,
                            'mean_span': mean_span,
                        })
                    else:
                        # Reservoir sampling so that all sentences have
                        # equal probability of appearing.
                        j = rng.randrange(bucket_counts[key])
                        if j < max_per_bucket:
                            if rendered is None:
                                rendered = _render()
                            existing[j] = {
                                'html': rendered,
                                'source': src,
                                'n_left': n_left,
                                'n_right': n_right,
                                'mean_span': mean_span,
                            }
    except Exception as exc:
        print(f"  ! collection error: {exc}")
    return buckets, dict(bucket_counts)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def _page_head(title, extra_css=''):
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<title>{html.escape(title)}</title>'
        f'<script src="{REACTIVE_DEP_TREE_SCRIPT}" async deferred></script>'
        f'<style>{PAGE_CSS}{extra_css}</style></head><body>'
    )


def _samples_page_html(lang_name, lang_code, direction, n,
                       mal_value, sample_count, examples):
    title = f'{lang_name} — {direction.upper()}_{n}'
    parts = [_page_head(title)]
    parts.append('<p class="back"><a href="../index.html">← back to '
                 f'{html.escape(lang_name)} examples</a> · '
                 '<a href="../../index.html">← back to MAL site</a></p>')
    parts.append(f'<h1>{html.escape(lang_name)} '
                 f'<small style="color:#999;font-weight:normal">'
                 f'({html.escape(lang_code)})</small> — '
                 f'{direction.upper()}<sub>{n}</sub></h1>')

    desc = DIRECTION_DESC[direction].format(n=n)
    val_str = f'{mal_value:.3f}' if mal_value is not None else '—'
    cnt_str = f'{sample_count:,}' if sample_count else '?'
    formula = {
        'mal':  ('mean of subtree sizes (in tokens) over all dependents of '
                 'all verbs in this bucket'),
        'lmal': ('mean of subtree sizes (in tokens) over the <i>left</i> '
                 'dependents of all verbs in this bucket'),
        'rmal': ('mean of subtree sizes (in tokens) over the <i>right</i> '
                 'dependents of all verbs in this bucket'),
    }[direction]
    parts.append(
        '<div class="info">'
        f'<p><b>Bucket:</b> {desc}.</p>'
        f'<p><b>{direction.upper()}<sub>{n}</sub> = {val_str}</b> &nbsp; '
        f'<span style="color:#666">({cnt_str} verb tokens in this bucket)</span></p>'
        f'<p style="font-size:13px;color:#555">Definition: {formula}. '
        'Below: a reservoir sample of up to {n_show} sentences from this '
        'bucket; the verb is highlighted in red, its qualifying dependents in '
        'green, and each dependent shows its subtree size '
        '(field <code>MISC.span</code>).</p>'.format(n_show=len(examples))
        + '</div>'
    )

    if not examples:
        parts.append('<p class="no-data">No example sentences available '
                     'for this bucket.</p>')
    else:
        for i, ex in enumerate(examples, 1):
            parts.append('<div class="example">')
            parts.append(
                f'<div class="example-meta">Example {i} '
                f'· source: {html.escape(ex["source"])} '
                f'· this verb has L={ex["n_left"]}, R={ex["n_right"]} '
                f'(mean span = {ex["mean_span"]:.2f})</div>'
            )
            parts.append(ex['html'])
            parts.append('</div>')

    parts.append('</body></html>')
    return '\n'.join(parts)


def _index_page_html(lang_name, lang_code, mal_data, counts_data, max_n=8):
    """Per-language landing page with the MAL_n / LMAL_n / RMAL_n table."""
    title = f'{lang_name} ({lang_code}) — MAL examples'
    parts = [_page_head(title)]
    parts.append('<p class="back"><a href="../../index.html">← back to MAL site</a></p>')
    parts.append(f'<h1>{html.escape(lang_name)} '
                 f'<small style="color:#999;font-weight:normal">'
                 f'({html.escape(lang_code)})</small></h1>')
    parts.append(
        '<div class="info">'
        '<p>This page lets you inspect the <b>real treebank sentences</b> behind '
        'each MAL value reported on the MAL companion site. Each cell below '
        'shows the value <code>X<sub>n</sub></code> (with the underlying '
        'sample count) and links to a page of example sentences from the '
        'corresponding bucket. The verb is highlighted in red and its '
        'qualifying dependents in green; each dependent is annotated with its '
        'subtree size — these are the numbers averaged into '
        '<code>X<sub>n</sub></code>.</p>'
        '<ul style="margin:6px 0 0 16px;padding:0;font-size:13px">'
        '<li><b>MAL<sub>n</sub></b> — verbs with <i>n</i> dependents in total.</li>'
        '<li><b>LMAL<sub>n</sub></b> — verbs with <i>n</i> left dependents (right side any).</li>'
        '<li><b>RMAL<sub>n</sub></b> — verbs with <i>n</i> right dependents (left side any).</li>'
        '</ul></div>'
    )

    # Find effective max n present
    eff_max = 0
    for d in DIRECTIONS:
        if mal_data.get(d):
            eff_max = max(eff_max, max(mal_data[d].keys()))
    eff_max = min(max_n, eff_max) if eff_max else max_n

    parts.append('<table class="mal-table"><thead><tr>')
    parts.append('<th>direction</th>')
    for n in range(1, eff_max + 1):
        parts.append(f'<th>n = {n}</th>')
    parts.append('</tr></thead><tbody>')
    for d in DIRECTIONS:
        parts.append(f'<tr><td class="lang-label">{d.upper()}<sub>n</sub></td>')
        for n in range(1, eff_max + 1):
            v = mal_data.get(d, {}).get(n)
            c = counts_data.get(d, {}).get(n, 0)
            sample_path = f'samples/{d}_n{n}.html'
            sample_full = os.path.join(os.path.dirname(__file__) or '.',
                                       sample_path)  # not used; checked at write time
            if v is not None:
                cell = f'{v:.3f}<br><small>({c:,})</small>'
                parts.append(f'<td><a href="{sample_path}">{cell}</a></td>')
            else:
                parts.append('<td style="color:#bbb">—</td>')
        parts.append('</tr>')
    parts.append('</tbody></table>')

    parts.append('<p style="font-size:12px;color:#666">'
                 'Note: cells link to a reservoir sample of sentences for that '
                 'bucket; sample size is bounded by '
                 '<code>--max-per-bucket</code> at generation time.</p>')
    parts.append('</body></html>')
    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Per-language driver
# ---------------------------------------------------------------------------

def _process_language(args):
    (lang_code, lang_name, conll_files, mal_data, counts_data,
     output_dir, max_per_bucket, max_sentences, max_n) = args

    lang_dir = os.path.join(output_dir, lang_code)
    samples_dir = os.path.join(lang_dir, 'samples')
    os.makedirs(samples_dir, exist_ok=True)

    buckets, total_counts = _collect_examples(
        conll_files, max_per_bucket=max_per_bucket,
        max_sentences=max_sentences, seed=hash(lang_code) & 0xFFFF)

    # Index page
    with open(os.path.join(lang_dir, 'index.html'), 'w', encoding='utf-8') as fh:
        fh.write(_index_page_html(lang_name, lang_code, mal_data,
                                  counts_data, max_n=max_n))

    # Sample pages — one per (direction, n) for which we have either a MAL value
    # or actual collected examples.
    written = 0
    for direction in DIRECTIONS:
        ns = set(mal_data.get(direction, {}).keys())
        ns.update(n for (d, n) in buckets if d == direction)
        for n in sorted(ns):
            if n < 1 or n > max_n:
                continue
            examples = buckets.get((direction, n), [])
            mal_value = mal_data.get(direction, {}).get(n)
            sample_count = counts_data.get(direction, {}).get(n, 0)
            page = _samples_page_html(lang_name, lang_code, direction, n,
                                      mal_value, sample_count, examples)
            with open(os.path.join(samples_dir, f'{direction}_n{n}.html'),
                      'w', encoding='utf-8') as fh:
                fh.write(page)
            written += 1

    return lang_code, written, sum(len(v) for v in buckets.values())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_examples(data_dir='data',
                      output_dir='html_analyses/examples',
                      languages=None,
                      max_per_bucket=20,
                      max_sentences=None,
                      max_n=8,
                      n_workers=None):
    """Generate per-language MAL example pages.

    Parameters
    ----------
    data_dir : str
        Directory containing ``metadata.pkl``, ``lang2MAL_full.pkl`` and
        ``all_langs_position2num.pkl``.
    output_dir : str
        Directory under which ``<lang_code>/index.html`` and
        ``<lang_code>/samples/*.html`` are written.
    languages : iterable of str or None
        If given, restrict to those language codes; otherwise process all
        languages present in ``lang2MAL_full.pkl``.
    max_per_bucket : int
        Reservoir size per (direction, n) sample page.
    max_sentences : int or None
        Stop after parsing this many sentences per language (None = all).
    max_n : int
        Highest ``n`` for which to render index/samples cells.
    n_workers : int or None
        Number of parallel worker processes (default: half the CPUs).
    """
    with open(os.path.join(data_dir, 'metadata.pkl'), 'rb') as f:
        metadata = pickle.load(f)
    langNames = metadata['langNames']
    langConllFiles = metadata['langConllFiles']

    with open(os.path.join(data_dir, 'lang2MAL_full.pkl'), 'rb') as f:
        lang2MAL = pickle.load(f)

    with open(os.path.join(data_dir, 'all_langs_position2num.pkl'), 'rb') as f:
        all_p2n = pickle.load(f)

    # Per-language counts: total / left / right
    from mal_html_report import get_sample_counts_per_n, get_directional_counts
    counts_total = get_sample_counts_per_n(all_p2n)
    counts_left, counts_right = get_directional_counts(all_p2n)

    if languages is None:
        languages = sorted(lang2MAL.keys())
    else:
        languages = [l for l in languages if l in lang2MAL]

    os.makedirs(output_dir, exist_ok=True)

    work = []
    for lang in languages:
        files = langConllFiles.get(lang, [])
        if not files:
            continue
        mal_data = {
            'mal': lang2MAL[lang].get('total', {}),
            'lmal': lang2MAL[lang].get('left', {}),
            'rmal': lang2MAL[lang].get('right', {}),
        }
        counts_data = {
            'mal': counts_total.get(lang, {}),
            'lmal': counts_left.get(lang, {}),
            'rmal': counts_right.get(lang, {}),
        }
        work.append((lang, langNames.get(lang, lang), files, mal_data,
                     counts_data, output_dir, max_per_bucket, max_sentences,
                     max_n))

    if n_workers is None:
        n_workers = max(1, (multiprocessing.cpu_count() or 2) // 2)

    print(f"Generating MAL examples for {len(work)} language(s) "
          f"using {n_workers} worker(s) → {output_dir}")

    results = []
    if n_workers <= 1:
        for w in tqdm(work, desc='languages'):
            results.append(_process_language(w))
    else:
        with multiprocessing.Pool(n_workers) as pool:
            for r in tqdm(pool.imap_unordered(_process_language, work),
                          total=len(work), desc='languages'):
                results.append(r)

    n_pages = sum(r[1] for r in results)
    n_examples = sum(r[2] for r in results)
    print(f"✓ Wrote {n_pages} sample page(s) across {len(results)} language(s) "
          f"({n_examples} example sentence(s) collected).")

    # Top-level examples homepage — list all languages that have an index.html
    # on disk (covers both freshly generated and previously generated runs).
    write_examples_homepage(output_dir, langNames)
    return [r[0] for r in results]


def write_examples_homepage(output_dir, langNames):
    """Write ``<output_dir>/index.html`` listing every language with an
    ``<lang_code>/index.html`` page on disk. Returns the path written, or
    ``None`` if no languages were found."""
    if not os.path.isdir(output_dir):
        return None
    entries = []
    for code in sorted(langNames):
        idx = os.path.join(output_dir, code, 'index.html')
        if os.path.exists(idx):
            entries.append((code, langNames[code]))
    if not entries:
        return None

    # Group alphabetically by first letter of language name for navigability.
    by_letter: dict = defaultdict(list)
    for code, name in entries:
        letter = (name[:1] or '?').upper()
        by_letter[letter].append((code, name))

    parts = [_page_head('MAL examples — all languages',
                        extra_css='.lang-grid { display: grid; '
                                  'grid-template-columns: repeat(auto-fill,minmax(220px,1fr)); '
                                  'gap: 6px 16px; margin: 8px 0 24px 0; } '
                                  '.lang-grid a { text-decoration: none; color: #1976d2; '
                                  'font-size: 14px; padding: 2px 0; } '
                                  '.lang-grid a:hover { text-decoration: underline; } '
                                  '.lang-grid .code { color: #999; font-size: 12px; }')]
    parts.append('<p class="back"><a href="../index.html">← back to MAL site</a></p>')
    parts.append('<h1>MAL example sentences</h1>')
    parts.append(
        '<div class="info">'
        f'<p>Per-language pages of <b>real treebank sentences</b> illustrating '
        f'the verb configurations from which MAL<sub>n</sub>, LMAL<sub>n</sub> '
        f'and RMAL<sub>n</sub> are computed. The verb is highlighted in red, '
        f'its qualifying dependents in green; each dependent is annotated with '
        f'its subtree size (<code>MISC.span</code>) — these are the values '
        f'averaged into the MAL.</p>'
        f'<p>{len(entries)} language(s) available. Click a language to see '
        f'its MAL<sub>n</sub> / LMAL<sub>n</sub> / RMAL<sub>n</sub> table and '
        f'sample-sentence pages per bucket.</p>'
        '</div>'
    )

    for letter in sorted(by_letter):
        parts.append(f'<h2 style="margin-top:18px">{letter}</h2>')
        parts.append('<div class="lang-grid">')
        for code, name in sorted(by_letter[letter], key=lambda x: x[1].lower()):
            parts.append(
                f'<a href="{code}/index.html">'
                f'{html.escape(name)} '
                f'<span class="code">({html.escape(code)})</span></a>'
            )
        parts.append('</div>')

    parts.append('</body></html>')
    out_path = os.path.join(output_dir, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(parts))
    print(f"✓ Wrote examples homepage → {out_path} ({len(entries)} languages)")
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    p.add_argument('--data-dir', default='data')
    p.add_argument('--output-dir', default='html_analyses/examples',
                   help='Destination directory (default: html_analyses/examples)')
    p.add_argument('--languages', default=None,
                   help='Comma-separated list of language codes to process '
                        '(default: all in lang2MAL_full.pkl)')
    p.add_argument('--max-per-bucket', type=int, default=20,
                   help='Reservoir size per (direction, n) sample page')
    p.add_argument('--max-sentences', type=int, default=None,
                   help='Stop after parsing this many sentences per language')
    p.add_argument('--max-n', type=int, default=8,
                   help='Highest n displayed in the per-language table')
    p.add_argument('--workers', type=int, default=None,
                   help='Number of parallel worker processes')
    args = p.parse_args(argv)

    langs = None
    if args.languages:
        langs = [l.strip() for l in args.languages.split(',') if l.strip()]

    generate_examples(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        languages=langs,
        max_per_bucket=args.max_per_bucket,
        max_sentences=args.max_sentences,
        max_n=args.max_n,
        n_workers=args.workers,
    )


if __name__ == '__main__':
    main()
