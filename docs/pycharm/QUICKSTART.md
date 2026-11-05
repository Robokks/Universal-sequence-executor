# PyCharm step-by-step

Open extracted folder -> choose Python 3.11+ virtualenv -> PyCharm Terminal:

```powershell
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m lvbatch list
python -m lvbatch prepare --batch U01 --pane 4815
python -m lvbatch check --batch U01
```

Review `outputs/U01/vi_docs/` to see the intent and all connector and test contracts before generating anything. Then choose one optional route:

- Offline native VI COMPOSITION (not validation): see `docs/PYLABVIEW_OFFLINE.md`.
- Native VI generation and behavior tests on the LabVIEW PC: see `README.md`.
- NI Docker MassCompile: see `docs/DOCKER_VALIDATION.md`.

Use only ONE of pane variants 4815 / 4833. Do not automatically continue to U02 on a failed U01, and do not overwrite a VI. No hardware controller VIs are part of this first batch.