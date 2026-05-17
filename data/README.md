# Data

This project uses the real public KDD Cup 99 dataset through:

```python
sklearn.datasets.fetch_kddcup99
```

No fake training dataset is committed to this repository.

When you run:

```bash
python train.py --sample-size 100000
```

scikit-learn downloads/caches the dataset, trains the model, and saves:

- `models/fraud_model.pkl`
- `models/metrics.json`
- `data/reference_transactions.csv`

`reference_transactions.csv` is a small sample from the real dataset for dashboard streaming.
