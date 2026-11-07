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
    dmo = sub.add_parser("demo-run", help="Run simulation sequence; optional NI gRPC U02 decisions")
    dmo.add_argument("--plan", type=Path, default=None)
    dmo.add_argument("--backend", choices=["mock", "grpc"], default="mock")
    dmo.add_argument("--exe", type=Path, default=None)
    dmo.add_argument("--native-dir", type=Path, default=None)
    gui = sub.add_parser("demo-gui", help="Start simulation-only desktop operator UI")
    gui.add_argument("--exe", type=Path, default=None)
    gui.add_argument("--native-dir", type=Path, default=None)
    finish = sub.add_parser("native-cleanup", help="Plan or perform backup-first LabVIEW VI block-diagram cleanup")
    finish.add_argument("--batch", required=True, choices=["U01", "U02", "U03", "U04", "A01"])
    finish.add_argument("--exe", required=True, type=Path)
    finish.add_argument("--apply", action="store_true", help="Mutate scratch VIs after backup; default: dry-run")
    sub.add_parser("sim-smoke", help="A01 deterministic reference simulator demo (no LabVIEW or hardware)")
    a01prep = sub.add_parser("a01-clock-prepare", help="Stage only native Sim_Clock.vi in scratch output")
    a01prep.add_argument("--native-dir", default="native_clock_v1")
    a01test = sub.add_parser("a01-clock-test", help="Execute exact signed-64-bit clock cases in LabVIEW")
    a01test.add_argument("--exe", required=True, type=Path)
    a01test.add_argument("--backend", choices=["grpc", "pylabview"], default="grpc")
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
    cm.add_argument("--finish-exe", type=Path, default=None,
                    help="After successful new offline composition, back up and clean the VIs in LabVIEW")
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
    if args.action == "demo-run":
        import asyncio
        from .sequence_mvp import PLAN_FILE, run_file, save_results
        out = asyncio.run(run_file(args.plan or PLAN_FILE, args.backend,
                                   exe=args.exe, vi_dir=args.native_dir))
        json_file, csv_file = save_results(out)
        print(json.dumps({"run_id": out["run_id"], "status": out["status"],
                          "backend": out["backend"], "native_decisions": out["native_decisions"],
                          "steps": out["steps"], "json": str(json_file),
                          "csv": str(csv_file)}, indent=2))
        return 0 if out["status"] == "PASS" else 2
    if args.action == "demo-gui":
        from .sequence_gui import launch
        launch(args.exe, args.native_dir)
        return 0
    if args.action == "native-cleanup":
        from .native_cleanup import cleanup_batch
        out = cleanup_batch(args.batch, args.exe, args.apply)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") is True else 2
    if args.action == "a01-clock-prepare":
        from .a01_clock import prepare_sim_clock
        output = prepare_sim_clock(args.native_dir)
        print(json.dumps({"batch": output["batch"], "component": output["component"],
                          "connector": output["items"][0]["connector_map"],
                          "connector_pattern": output["items"][0]["connector_pattern"],
                          "native_vi": output["items"][0]["native_vi"],
                          "native_vis_staged": output["native_vis_staged"],
                          "native_vis_built": 0}, indent=2))
        return 0
    if args.action == "a01-clock-test":
        from .a01_clock import test_native_sim_clock
        output = test_native_sim_clock(args.exe, args.backend)
        print(json.dumps(output, indent=2))
        return 0 if output["native_test_count"] == 8 and output["passes"] == 8 and (
            output["failures"] == 0 and output["not_run"] == 0) else 2
    if args.action == "sim-smoke":
        from .sim_reference import SimSession, SimModel, Command, Fault
        simulator = SimSession("SIM-SMOKE-1", model=SimModel())
        accepted = simulator.submit(Command("C1", simulator.run_id,
                                             pressure_bar=50, flow_lpm=20, lever_mm=100))
        simulator.advance(100)
        normal = simulator.feedback()
        simulator.schedule_fault(Fault.SENSOR_STALE, 100)
        simulator.advance(300)
        stale = simulator.feedback()
        simulator.schedule_fault(Fault.SENSOR_DROPOUT, 400)
        dropout = simulator.feedback()
        output = {"phase": "A01_PYTHON_REFERENCE_ONLY", "simulation_only": True,
                  "native_vis_built": 0, "accepted": accepted, "normal": normal,
                  "stale": stale, "dropout": dropout, "events": simulator.events}
        ok = (accepted["type"] == "ACCEPTED" and normal["quality"] == "GOOD"
              and stale["quality"] == "STALE" and dropout["quality"] == "INVALID"
              and simulator.simulation_only)
        output["status"] = "PASS" if ok else "FAIL"
        record("A01", "sim_reference", output)
        print(json.dumps(output, indent=2))
        return 0 if ok else 2
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
        if out["complete"] and args.finish_exe is not None:
            from .native_cleanup import cleanup_batch
            finished = cleanup_batch(args.batch, args.finish_exe, apply=True)
            out["post_generation_cleanup"] = {
                "ok": finished.get("ok") is True,
                "backup_dir": finished.get("backup_dir"),
                "evidence": str(Path("outputs") / args.batch.upper() /
                                "evidence/native_cleanup.json"),
            }
        print(json.dumps(out, indent=2))
        return 0 if (out["complete"] and
                     out.get("post_generation_cleanup", {"ok": True})["ok"]) else 2
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
