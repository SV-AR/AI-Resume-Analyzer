# Model evaluation

`evaluate_models.py` computes real metrics from `sample_dataset.json`. Nothing is hard-coded.

```bash
cd backend
python evaluation/evaluate_models.py                       # real all-MiniLM-L6-v2
python evaluation/evaluate_models.py --encoder hashing     # offline smoke test only
python evaluation/evaluate_models.py --json results.json   # also save full results
```

| Part | Metric |
|------|--------|
| Skill extraction | micro precision, recall, F1 over (text, gold skill set) pairs |
| Skill matching | exact-match accuracy, plus precision/recall/F1 for matched, missing and additional buckets |
| Semantic matching | top-1 accuracy per job, pairwise ordering accuracy, mean similarity for strong-fit vs unrelated resumes |

## Read the numbers honestly
- The dataset is small (12 + 5 + 2 jobs × 4 resumes) and was written by the project author, who also wrote the
  skill dictionary. High skill-extraction scores therefore say the code does what its author intended,
  not that it generalises to real resumes.
- Add real (anonymised, consented) examples and report the new numbers.
- `--encoder hashing` is a bag-of-words stand-in used so the script can run offline. Do not quote it as a
  transformer result.
