"""CLI usable from PyCharm Terminal or Run Configurations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .core import get_batch, load_batches, load_stage, check_aixml, prepare_batch, record


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lvbatch", description="Safe batch-wise AIXML / VI build")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list", help="Show batch plan")
    prep = sub.add_parser("prepare", help="Stage VI AIXML with embedded documentation")
    prep.add_argument("--batch", default="U01"); prep.add_argument("--pane", choices=["4815", "4833"], default="4815")
    prep.add_argument("--layout", choices=["compact", "fixed"], default="compact",
                      help="Compact: measured left-input/right-output panes. Fixed: retain baseline indices.")
    prep.add_argument("--native-dir", default="native",
                      help="Use native_refined to preserve the already tested native/*.vi files.")
    chk = sub.add_parser("check", help="Run offline XML lint against staged batch")
    chk.add_argument("--batch", default="U01")
    cm = sub.add_parser("compose", help="EXPERIMENTAL offline AIXML to VI; no native validation")
    cm.add_argument("--batch", default="U01"); cm.add_argument("--mcp-checkout", required=True, type=Path)
    cm.add_argument("--year", default=2026, type=int)
    mcp = sub.add_parser("mcp-generate", help="Use a running Windows LabVIEW MCP service")
    mcp.add_argument("--batch", default="U01"); mcp.add_argument("--exe", required=True, type=Path)
    mcp.add_argument("--backend", default="grpc", choices=["grpc", "pylabview"])
    mcp.add_argument("--pane", default="4815", choices=["4815", "4833"])
    test = sub.add_parser("mcp-test", help="Execute generated native VIs in LabVIEW")
    test.add_argument("--batch", default="U01"); test.add_argument("--exe", required=True, type=Path)
    test.add_argument("--backend", default="grpc", choices=["grpc", "pylabview"])
    icons = sub.add_parser("mcp-icons", help="Backup and apply documented 32x32 icons after composition")
    icons.add_argument("--batch", default="U01"); icons.add_argument("--exe", required=True, type=Path)
    icons.add_argument("--backend", choices=["grpc", "pylabview"], default="grpc")
    pane_audit = sub.add_parser("mcp-pane-audit", help="Read actual native pane geometry and record it")
    pane_audit.add_argument("--batch", default="U01"); pane_audit.add_argument("--exe", required=True, type=Path)
    pane_audit.add_argument("--backend", choices=["grpc", "pylabview"], default="grpc")
    dock = sub.add_parser("docker-compile", help="NI headless MassCompile, real Docker run")
    dock.add_argument("--batch", default="U01")
    args = parser.parse_args(argv)
    if args.action == "list":
        data = load_batches()
        for item in data["batches"]:
            print(f"{item['batch']:<5} {item['kind']:<24} {len(item['vi_names']):>3}  {item['label']}")
        return 0
    if args.action == "prepare":
        output = prepare_batch(args.batch, args.pane, layout=args.layout, native_dir=args.native_dir)
        print(json.dumps({"batch": output["batch"], "pane": output["pane"],
                          "layout": output["layout"], "native_dir": output["native_dir"],
                          "patterns": {e["name"]: e["connector_pattern"] for e in output["items"]},
                          "prepared": len(output["items"])}, indent=2)); return 0
    if args.action == "check":
        manifest = load_stage(args.batch)
        details = [check_aixml(Path(x["xml"]), x["name"]) for x in manifest["items"]]
        out = {"batch": args.batch, "status": "PASS" if all(d["ok"] for d in details) else "FAIL",
               "files": details}
        record(args.batch, "offline_lint", out)
        print(json.dumps({"status": out["status"], "checked": len(details),
                          "issues": [x for d in details for x in d["issues"]]}, indent=2));
        return 0 if out["status"] == "PASS" else 2
    if args.action == "compose":
        from .offline import compose
        out = compose(args.batch, args.mcp_checkout, args.year)
        print(json.dumps(out, indent=2)); return 0 if out["complete"] else 2
    if args.action in ("mcp-generate", "mcp-test"):
        from .mcp_client import generate, native_test
        out = (generate(args.batch, args.exe, args.backend, args.pane)
               if args.action == "mcp-generate" else native_test(args.batch, args.exe, args.backend))
        print(json.dumps(out, indent=2));
        return 0 if (out.get("ok", False) if args.action == "mcp-generate" else
                     out.get("failures", 0) == 0 and out.get("not_run", 1) == 0) else 2
    if args.action in ("mcp-icons", "mcp-pane-audit"):
        from .mcp_client import set_batch_icons, audit_batch_panes
        out = (set_batch_icons(args.batch, args.exe, args.backend)
               if args.action == "mcp-icons" else audit_batch_panes(args.batch, args.exe, args.backend))
        print(json.dumps(out, indent=2))
        return 0 if (out["ok"] if args.action == "mcp-icons" else
                     all(not row.get("tool_error") and not row.get("error")
                         for row in out["items"])) else 2
    if args.action == "docker-compile":
        from .docker_ci import masscompile
        out = masscompile(args.batch)
        print(json.dumps(out, indent=2)); return 0 if out["status"] == "PASS" else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
