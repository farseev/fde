#!/usr/bin/env python3
"""One-off: import the hand-made /zh/, /ms/ and /ta/ pages into i18n/<code>.json.

The three language versions were generated together with the English pages in commit cc95725.
Segments are aligned position by position (per kind: text runs, attributes, JSON-LD) with the
English page; a pair is imported only when the placeholder structure matches. Two alignments are used:
  - cc95725 English  <->  cc95725 translation   (the original generator output)
  - current English  <->  current translation   (accepted only where the English segment existed in
    cc95725 too, or where the translation was updated together with the English, e.g. the giving block)
English segments that were rewritten after cc95725 (new titles and descriptions) therefore stay
untranslated and appear in the todo files. Existing TM entries are never overwritten.
Usage: python3 tools/i18n_import_legacy.py [--dry]
"""
import difflib, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import i18n

BASE = "cc95725"


def git_show(rev, rel):
    r = subprocess.run(["git", "show", "%s:%s" % (rev, rel)], cwd=i18n.ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def struct_key(doc, s):
    """Structural signature of a run segment: the opening tag (name + class + data-*) right before it."""
    if s.kind != "run":
        return s.kind + ":" + (s.attr or "")
    m = None
    for m in re.finditer(r"<([a-z0-9]+)([^>]*)>", doc[max(0, s.a - 400):s.a]):
        pass
    if not m:
        return "?"
    cls = re.search(r'class="([^"]*)"', m.group(2))
    dat = re.findall(r'data-(?:f|cat)="([^"]*)"', m.group(2))
    return "%s.%s%s" % (m.group(1), cls.group(1) if cls else "", "|".join(dat))


def align(en_doc, tr_doc, label):
    ne, nt = i18n.normalise(en_doc), i18n.normalise(tr_doc)
    _, se = i18n.segments(ne)
    _, st = i18n.segments(nt)
    pairs, problems = [], []
    for kind in ("run", "attr", "ld"):
        a = [s for s in se if s.kind == kind]
        b = [s for s in st if s.kind == kind]
        if len(a) == len(b):
            matched = list(zip(a, b))
        else:
            problems.append("%s %s count %d vs %d (aligned structurally)" % (label, kind, len(a), len(b)))
            ka = [struct_key(ne, x) + "/" + str(len(x.tags)) for x in a]
            kb = [struct_key(nt, y) + "/" + str(len(y.tags)) for y in b]
            matched = []
            for blk in difflib.SequenceMatcher(None, ka, kb, autojunk=False).get_matching_blocks():
                matched += [(a[blk.a + k], b[blk.b + k]) for k in range(blk.size)]
        for x, y in matched:
            if not x.id:
                continue
            if kind == "attr" and x.attr != y.attr:
                problems.append("%s attr name mismatch" % label); continue
            if not i18n.check_ph(x.text, y.text) or not y.text.strip():
                problems.append("%s ph %s | %s" % (label, x.text[:40], y.text[:40])); continue
            pairs.append((x.id, x.text, y.text, y.suffix or "", True))
    return pairs, problems


def main():
    dry = "--dry" in sys.argv
    src, pages = i18n.cmd_extract(quiet=True)
    for code in i18n.LEGACY:
        d = i18n.L[code]["dir"]
        tm = i18n.load_tm(code)
        added, problems, conflicts, skipped_changed = 0, [], 0, 0
        for rel in i18n.en_pages():
            en_old, tr_old = git_show(BASE, rel), git_show(BASE, "%s/%s" % (d, rel))
            en_new, tr_new = i18n.read(os.path.join(i18n.ROOT, rel)), i18n.read(os.path.join(i18n.ROOT, d, rel))
            old_pairs, p1 = align(en_old, tr_old, "%s %s@base" % (code, rel)) if en_old and tr_old else ([], [])
            new_pairs, p2 = align(en_new, tr_new, "%s %s@head" % (code, rel))
            problems += p1 + p2
            old_en_ids = {p[0] for p in old_pairs}
            old_tr_texts = {p[2] for p in old_pairs}
            cand = {}
            for i, en, tr, sfx, ok in old_pairs:
                cand.setdefault(i, tr)
            for i, en, tr, sfx, ok in new_pairs:
                if i in old_en_ids or tr not in old_tr_texts:
                    cand[i] = tr          # unchanged English, or translation updated with the English
                else:
                    skipped_changed += 1  # English rewritten, translation still the old one
            for i, tr in cand.items():
                if i not in src:
                    continue
                if i in tm:
                    if tm[i] != tr:
                        conflicts += 1
                    continue
                # identical-to-English pairs are imported too: the legacy pages deliberately keep
                # source/citation titles, video titles and alt text in English
                tm[i] = tr
                added += 1
            # title suffix translation
            for i, en, tr, sfx, ok in new_pairs + old_pairs:
                if sfx and i18n.sid(i18n.SUFFIX_KEY) not in tm:
                    tm[i18n.sid(i18n.SUFFIX_KEY)] = sfx.strip()
        if not dry:
            i18n.save_tm(code, tm)
        need = set(x for ids in pages.values() for x in ids)
        print("%s: added %d, conflicts kept first %d, stale (English rewritten) %d, coverage %d/%d" % (
            code, added, conflicts, skipped_changed, len(need & set(tm)), len(need)))
        for p in problems[:12]:
            print("   ", p)
        if len(problems) > 12:
            print("    … %d more" % (len(problems) - 12))


if __name__ == "__main__":
    main()
