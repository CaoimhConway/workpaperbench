"""Report the real-v1 study separately from the published historical experiment."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from .cli import summarize


def fraction(passed, assessed):
    return f'{passed} / {assessed}' if assessed else 'Pending'


def report_real(root):
    root = Path(root)
    dataset = root / 'datasets/real-v1'
    manifest_path = dataset / 'manifest.json'
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text())
    schedule = json.loads((root / manifest['schedule']).read_text())
    reconciliation_path = root / 'reports/real-v1/final-reconciliation.json'
    reconciliation = json.loads(reconciliation_path.read_text()) if reconciliation_path.is_file() else {}
    if reconciliation and reconciliation.get('manifest_id') != manifest['manifest_id']:
        raise ValueError('Real study reconciliation identity mismatch')
    rows, retained = [], 0
    for slot in schedule:
        directory = root / 'reports/runs' / manifest['manifest_id'] / slot['slot_id']
        path = directory / 'record.json'
        record = json.loads(path.read_text()) if path.is_file() else {'status': 'unrecorded', 'verdict': None, **reconciliation.get('slots', {}).get(slot['slot_id'], {})}
        if path.is_file():
            if record.get('freeze_manifest_id') != manifest['manifest_id'] or any(record.get(k) != slot[k] for k in ('slot_id', 'task', 'arm', 'repetition', 'split')):
                raise ValueError('Real study record identity mismatch')
            audit_path = directory / 'artifact-audit.json'
            if not audit_path.is_file():
                raise ValueError('Unauthenticated real study record')
            audit = json.loads(audit_path.read_text())
            if audit.get('archive_digest_verified') is not True or hashlib.sha256(path.read_bytes()).hexdigest() != audit['retained_file_sha256'].get('record.json'):
                raise ValueError('Real study provenance mismatch')
            for name in ('answer.raw.txt', 'answer.json', 'verdict.json'):
                retained_path = directory / name
                if retained_path.is_file() and hashlib.sha256(retained_path.read_bytes()).hexdigest() != audit['retained_file_sha256'].get(name):
                    raise ValueError('Real study retained bytes mismatch')
            if (directory / 'answer.raw.txt').is_file() or (directory / 'answer.json').is_file():
                retained += 1
        rows.append({**slot, **record})
    summaries = summarize(rows)
    output = root / 'reports/real-v1'
    output.mkdir(parents=True, exist_ok=True)
    snapshots = [json.loads(path.read_text()) for path in (output / 'provider').glob('*.json')]
    latest = max(snapshots, key=lambda item: item['as_of'], default=None)
    lifetime = latest['snapshot'].get('usage_usd') if latest else None
    baseline = manifest['budget']['historical_provider_lifetime_usd']
    cost = {'latest_provider_snapshot': latest, 'cumulative_inference_usd': lifetime,
            'historical_baseline_usd': baseline,
            'new_campaign_increment_usd': lifetime - baseline if lifetime is not None else None,
            'note': 'Provider lifetime includes development and failed calls. Reporting can lag. Per-arm allocation and Actions invoice/storage charges are unknown.'}
    result = {'manifest_id': manifest['manifest_id'], 'dataset_id': 'real-v1',
              'scorer_version': manifest['scorer_version'], 'model': manifest['model'],
              'summary': summaries, 'slots': rows, 'retained_answers': retained, 'cost': cost,
              'status': 'measured' if any(r.get('verdict') for r in rows) and all(r.get('status') in ('complete', 'task_failed', 'infra_failed', 'blocked', 'artifact_missing') for r in rows) else 'pending',
              'actual_execution_order': [r['slot_id'] for r in sorted((r for r in rows if r.get('execution_started_at')), key=lambda r: r['execution_started_at'])]}
    lines = ['# Real-v1 results', '', f"Dataset `{manifest['manifest_id']}`, scorer {manifest['scorer_version']}, model `{manifest['model']}`.", '',
             'Historical results are a separate study. No scores carry over to changed tasks.', '',
             '| Split | Arm | Strict / scheduled | Numbers / assessed | Conclusion verdict / assessed | Evidence / assessed | Replay / assessed | Verdict coverage | Retained / scheduled |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for split, arms in summaries.items():
        for arm, s in arms.items():
            counts = s['checks_passed']
            assessed = s['checks_assessed']
            selected = [r for r in rows if r['split'] == split and r['arm'] == arm]
            nret = sum((root / 'reports/runs' / manifest['manifest_id'] / r['slot_id'] / 'answer.json').is_file() or (root / 'reports/runs' / manifest['manifest_id'] / r['slot_id'] / 'answer.raw.txt').is_file() for r in selected)
            cells = [fraction(counts.get(k, 0), assessed.get(k, 0)) for k in ('numerical', 'conclusion_verdict', 'evidence_context', 'replay')]
            lines.append('| ' + ' | '.join([split, arm, fraction(s['verified'], s['scheduled']) if s['assessed'] else 'Pending', *cells, f"{s['assessed']} / {s['scheduled']}", f"{nret} / {s['scheduled']}"]) + ' |')
    lines += ['', 'Strict completion requires all declared checks. A missing citation or reason does not establish an incorrect financial conclusion. Unassessed checks are pending, not zero accuracy.', '',
              'The five evaluation tasks share some source bundles. Apple is a previously exposed regression task. This is not an independent-dataset or contamination-free study.', '',
              '| Slot | Status | Strict | Numbers | Conclusion verdict | Errors |', '|---|---|---|---|---|---|']
    for row in rows:
        v = row.get('verdict') or {}
        c = (v.get('details') or {}).get('conclusion') or {}
        lines.append('| ' + ' | '.join([row['slot_id'], row['status'], str(v.get('complete', 'Pending')), str((v.get('checks') or {}).get('numerical', 'Pending')), str(c.get('verdict', 'Pending')), ', '.join(v.get('errors', [])).replace('|', '\\|')]) + ' |')
    lines += ['', '## Intervention interpretation', '', interpretation(summaries, result['status']), '',
              'A has full common instructions. B adds only the preserved contract-check skill. Three repeated attempts per task are not independent financial datasets. No significance or causal claim is made.', '',
              '## Independent diagnostics', '', '| Split | Arm | Conclusion reason / assessed | Conclusion evidence / assessed | Format / assessed |', '|---|---|---:|---:|---:|']
    for split, arms in summaries.items():
        for arm, s in arms.items():
            cells = [fraction(s['checks_passed'].get(k, 0), s['checks_assessed'].get(k, 0)) for k in ('conclusion_reason_code', 'conclusion_evidence', 'format')]
            lines.append('| ' + ' | '.join([split, arm, *cells]) + ' |')
    lines += ['', 'Actual order and original per-slot records are retained in [scores.json](scores.json). No official answer is repaired or retried for a better score.']
    if latest:
        lines += ['', f"Provider receipt as of {latest['as_of']}: cumulative USD {lifetime:.9f}, including historical USD {baseline:.9f}. New campaign increment USD {cost['new_campaign_increment_usd']:.9f}. The unchanged dedicated lifetime cap is USD 20, below the USD 50 authorization.", '', cost['note']]
    (output / 'scores.json').write_text(json.dumps(result, indent=2) + '\n')
    (output / 'results.md').write_text('\n'.join(lines) + '\n')
    update_combined_readme(root, result)
    return result


def interpretation(summary, state):
    if state != 'measured':
        return 'New measured results are pending. The historical intervention outcome does not evaluate this dataset.'
    a, b = (summary['evaluation'][arm] for arm in ('A', 'B'))
    if a['assessed'] != a['scheduled'] or b['assessed'] != b['scheduled']:
        return 'The new campaign has incomplete verdict coverage. Strict completion counts retain the scheduled denominator and cannot establish an intervention benefit.'
    if b['verified'] > a['verified']:
        return f"B completed {b['verified']}/{b['scheduled']} evaluation workpapers versus A {a['verified']}/{a['scheduled']}. This is a descriptive difference in this small fixed study."
    if b['verified'] == a['verified']:
        return 'The skill produced no observed strict-completion improvement in this fixed evaluation.'
    return 'The skill did not improve strict completion in this fixed evaluation.'


def update_combined_readme(root, real):
    root = Path(root)
    path = root / 'README.md'
    text = path.read_text()
    start, end = '<!-- versioned-results:start -->', '<!-- versioned-results:end -->'
    if start not in text:
        return
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Invalid combined result markers')
    old = json.loads((root / 'reports/scores.json').read_text())
    lines = [start, '', '| Dataset / scorer | Model | Arm | Strict / scheduled | Numbers / assessed | Conclusion verdict / assessed | Evidence / assessed | Replay / assessed | Verdict / scheduled | Retained / scheduled |',
             '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for label, summary, rows, reviews in (('Historical v1 / 1.2.0', old['reviewed_summary'], old['slots'], old['reviews']), ('real-v1 / ' + real['scorer_version'], real['summary'], real['slots'], None)):
        for arm in ('A', 'B'):
            s = summary['evaluation'][arm]
            counts, assessed = s['checks_passed'], s['checks_assessed']
            cells = [fraction(counts.get(k, 0), assessed.get(k, 0)) for k in ('numerical', 'conclusion_verdict', 'evidence_context', 'replay')]
            selected = [r for r in rows if r['split'] == 'evaluation' and r['arm'] == arm]
            nret = sum(r['slot_id'] in reviews for r in selected) if reviews is not None else sum((root / 'reports/runs' / real['manifest_id'] / r['slot_id'] / 'answer.json').is_file() or (root / 'reports/runs' / real['manifest_id'] / r['slot_id'] / 'answer.raw.txt').is_file() for r in selected)
            lines.append('| ' + ' | '.join([label, '`qwen/qwen3.6-35b-a3b`', arm, fraction(s['verified'], s['scheduled']) if s['assessed'] else 'Pending', *cells, f"{s['assessed']} / {s['scheduled']}", f"{nret} / {s['scheduled']}"]) + ' |')
    lines += ['', 'Evaluation only. Development is separate. Historical skill: no improvement. Real-v1: ' + interpretation(real['summary'], real['status']), '',
              '[New study](reports/real-v1/results.md) · [Historical study and original negative results](reports/results.md). Missing evidence is distinct from an incorrect conclusion. Assessments and retained outputs may have different coverage.', '', end]
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(before + '\n'.join(lines) + after)
