### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Pull data

Modify `START_DT` and `END_DT` in `pull_data.py` to the desired date range.

```bash
setx POLYGON_API_KEY API_KEY # Windows
export POLYGON_API_KEY=API_KEY # UNIX
python pull_data.py
```

### Simulate

```bash
python simulate.py
```
