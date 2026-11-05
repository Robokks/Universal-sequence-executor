# NI Docker — real LabVIEW validation gate

Reviewed official sources (Nov 2026):
- https://github.com/ni/labview-for-containers
- https://github.com/ni/labview-for-containers/blob/main/.github/workflows/masscompile-linux-container.yml
- https://github.com/ni/labview-for-containers/blob/main/docs/linux-prebuilt.md
- https://knowledge.ni.com/KnowledgeArticleDetails?id=kA0VU000000ANjJ0AW

## Supported reality

NI provides Linux and Windows LabVIEW container images. The images contain LabVIEW Professional, LabVIEWCLI and VI Analyzer, and can run MassCompile, VI Analyzer, RunVI, build specs and similar CI jobs. For 2026 LabVIEW use `-Headless`. Containers are **CI/CD and automated-validation environments only**, not interactive graphical LabVIEW development environments. NI's license terms allow container usage for authorized automated processes when you have acquired a LabVIEW development license, with limits on distribution and development use. Read the license yourself before deploying, especially in company or public CI.

NI provides `nationalinstruments/labview:latest-linux` for Linux containers on Docker Desktop for Windows or Linux; Windows image `:latest-windows` requires suitable Windows-container support. The exact image version and installed LabVIEWCLI path need checking on the chosen tag. **Pin a tested tag or digest for repeatable CI** once your first successful run is documented.

## Example official-style command (PowerShell)

From an output folder containing VI files:

```powershell
docker pull nationalinstruments/labview:latest-linux
# Run from project root; use forward slashes for Docker volume target:
docker run --rm --network none -v "${PWD}\outputs\U01\native:/workspace" nationalinstruments/labview:latest-linux LabVIEWCLI -LogToConsole TRUE -OperationName MassCompile -DirectoryToCompile /workspace -LabVIEWPath /usr/local/natinst/LabVIEW-2026-64/labview -Headless
```

The PyCharm CLI wraps this command: `python -m lvbatch docker-compile --batch U01`. It stores exit code plus stdout/stderr under `outputs/U01/evidence/docker_masscompile.json`. Docker is **not run as part of ordinary Python tests**. Keep VI output in the isolated scratch folder because MassCompile can produce files as a side effect.

## Batch acceptance in Docker

1. Six expected VI binaries exist in the scratch native directory.
2. Docker image matches the LabVIEW version and architecture required by those VIs.
3. MassCompile returns exit code 0 and the log has no unexpected broken VI/dependency warnings.
4. VI Analyzer tests are a separate planned gate, not implemented by this project's current CLI.
5. Behavioral unit tests still need LabVIEW test runner / `lvai_run_vi_and_read_values` or a supported headless RunVI harness.
6. Windows-only functionality, device drivers, class dependencies and RT targets must be separately verified in the corresponding environment.

The 2025q3 Linux image uses `EnableCICDFeaturesForLabVIEW=TRUE`; for 2026 use `-Headless` as official NI documentation requires. Do not silently label a 2025 image able to compile LabVIEW 2026 VIs. The container cannot perform live safety certification or validate physical VFD/PRV/servo output.
