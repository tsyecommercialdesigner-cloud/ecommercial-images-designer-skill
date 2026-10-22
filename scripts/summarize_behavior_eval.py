"""Summarize latest explicitly selected case revisions without hiding failed repetitions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]


def summarize(roots, cases):
    rows=[]
    for case in cases:
        selected=None
        for root in roots:
            trials=sorted(root.glob(case['id']+'-r*/trial.json'))
            if trials:selected=(root,trials)
        if selected is None:
            rows.append(dict(case_id=case['id'],status='not_run',trials=[]));continue
        root,paths=selected
        grades={}
        if (root/'grades.jsonl').exists():
            for line in (root/'grades.jsonl').read_text(encoding='utf-8').splitlines():
                grade=json.loads(line);grades[grade['trial_id']]=grade
        trials=[json.loads(p.read_text(encoding='utf-8')) for p in paths]
        complete=len(trials)==3 and {t['repeat'] for t in trials}=={1,2,3} and all(t['status']=='completed' and t['trial_id'] in grades for t in trials)
        judgments=[grades[t['trial_id']] for t in trials if t['trial_id'] in grades]
        rows.append(dict(case_id=case['id'],run=str(root),status='scored' if complete else 'incomplete',trials=[t['trial_id'] for t in trials],judgments=judgments))
    judgments=[j for row in rows for j in row.get('judgments',[])]
    means={key:sum(j[key] for j in judgments)/len(judgments) if judgments else None for key in ('routing','evidence','boundaries')}
    critical=sum(j['critical_failure'] for j in judgments)
    complete=all(row['status']=='scored' for row in rows)
    return dict(cases=rows,scored_trials=len(judgments),complete=complete,critical_failures=critical,means=means,accepted=complete and critical==0 and all(value>=1.8 for value in means.values()))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',action='append',required=True,type=Path);a=p.parse_args()
    cases=json.loads((REPO/'evals/scenarios.json').read_text(encoding='utf-8'))['cases']
    result=summarize(a.run,cases)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['accepted'] else 1


if __name__=='__main__':raise SystemExit(main())
