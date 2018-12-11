## Quick start

First create a virtualenv and enter it:

```
python3 -m venv venv
source venv/bin/activate   # Or venv\Scripts\activate on Windows
```

Then install dependencies:

```
pip install -r requirements.txt
```

Then run the CLI:

```
python bud.py
```

## Tests

```
pytest && mypy . && echo "yay everything works"
```
