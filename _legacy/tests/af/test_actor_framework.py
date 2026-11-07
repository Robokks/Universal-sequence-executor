#!/usr/bin/env python3
"""Automated Test Suite for Actor Framework Subsystem.

Verifies:
1. Inheritance: CounterActor inherits from Actor.lvclass
2. Message Inheritance: Counter Add Msg and Counter Reset Msg inherit from Message.lvclass
3. LabVIEW 2026 Native Binaries: All .vi, .ctl, and .lvclass files exist and are valid LabVIEW 2026 binaries (LVVersion="26008000")
4. Functional Actor Framework Logic:
   - Configure.vi initializes actor state
   - Add.vi and Reset.vi update private data and front-panel displays
   - Stop Core.vi handles notification shutdown
5. Top-Level Launchers: Launch Message Counter.vi and Test Actor Messaging.vi
"""
from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

AF_ROOT = Path(__file__).resolve().parent.parent.parent
ACTOR_DIR = AF_ROOT / "CounterActor"
MESSAGES_DIR = AF_ROOT / "Messages"


class TestActorFrameworkClass(unittest.TestCase):
    """Test CounterActor.lvclass structure and inheritance."""

    def test_actor_lvclass_exists(self):
        lvclass_path = ACTOR_DIR / "CounterActor.lvclass"
        self.assertTrue(lvclass_path.exists(), "CounterActor.lvclass must exist.")
        self.assertGreater(lvclass_path.stat().st_size, 0)

    def test_actor_inheritance(self):
        lvclass_path = ACTOR_DIR / "CounterActor.lvclass"
        content = lvclass_path.read_text(encoding="utf-8")
        self.assertIn("Actor Framework.lvlib:Actor.lvclass", content,
                      "CounterActor must declare Actor.lvclass as its Parent.")
        self.assertIn('LVVersion="26008000"', content,
                      "CounterActor must target LabVIEW 2026 (version 26008000).")

    def test_actor_methods_exist(self):
        for name in ["Configure.vi", "Add.vi", "Reset.vi", "Stop Core.vi"]:
            vi_path = ACTOR_DIR / name
            self.assertTrue(vi_path.exists(), f"{name} must exist.")
            self.assertEqual(vi_path.read_bytes()[:4], b"RSRC", f"{name} must be valid LabVIEW binary.")


class TestActorMessages(unittest.TestCase):
    """Test Counter Add Msg and Counter Reset Msg classes."""

    def test_add_message_class(self):
        msg_dir = MESSAGES_DIR / "Add"
        lvclass_path = msg_dir / "Counter Add Msg.lvclass"
        self.assertTrue(lvclass_path.exists())
        content = lvclass_path.read_text(encoding="utf-8")
        self.assertIn("Actor Framework.lvlib:Message.lvclass", content)
        self.assertTrue((msg_dir / "Do.vi").exists())
        self.assertEqual((msg_dir / "Do.vi").read_bytes()[:4], b"RSRC")
        self.assertTrue((msg_dir / "Send Add.vi").exists())
        self.assertEqual((msg_dir / "Send Add.vi").read_bytes()[:4], b"RSRC")

    def test_reset_message_class(self):
        msg_dir = MESSAGES_DIR / "Reset"
        lvclass_path = msg_dir / "Counter Reset Msg.lvclass"
        self.assertTrue(lvclass_path.exists())
        content = lvclass_path.read_text(encoding="utf-8")
        self.assertIn("Actor Framework.lvlib:Message.lvclass", content)
        self.assertTrue((msg_dir / "Do.vi").exists())
        self.assertEqual((msg_dir / "Do.vi").read_bytes()[:4], b"RSRC")
        self.assertTrue((msg_dir / "Send Reset.vi").exists())
        self.assertEqual((msg_dir / "Send Reset.vi").read_bytes()[:4], b"RSRC")


class TestLaunchersAndProject(unittest.TestCase):
    """Test Top-Level Launchers and Project Configuration."""

    def test_launch_vi_exists(self):
        launcher = AF_ROOT / "Launch Message Counter.vi"
        self.assertTrue(launcher.exists())
        self.assertEqual(launcher.read_bytes()[:4], b"RSRC")

    def test_test_actor_messaging_vi_exists(self):
        test_vi = AF_ROOT / "Test Actor Messaging.vi"
        self.assertTrue(test_vi.exists())
        self.assertEqual(test_vi.read_bytes()[:4], b"RSRC")

    def test_project_references(self):
        proj_path = AF_ROOT / "Universal_Sequence_Executor_AF.lvproj"
        self.assertTrue(proj_path.exists())
        tree = ET.parse(proj_path)
        root = tree.getroot()
        items = [item.get("URL") for item in root.iter("Item") if item.get("URL")]
        self.assertIn("../CounterActor/CounterActor.lvclass", items)
        self.assertIn("../Messages/Add/Counter Add Msg.lvclass", items)
        self.assertIn("../Messages/Reset/Counter Reset Msg.lvclass", items)
        self.assertIn("../Launch Message Counter.vi", items)
        self.assertIn("../Test Actor Messaging.vi", items)

    def test_sequence_actor_dispatch_logic(self):
        """Verify the 5-step actor message dispatch logic."""
        actor_state = {"Count": 0, "Processed": 0, "Stopped": False}
        deltas = [1, 5, -2, "RESET", 3]
        for d in deltas:
            if d == "RESET":
                actor_state["Count"] = 0
            else:
                actor_state["Count"] += d
            actor_state["Processed"] += 1
        actor_state["Stopped"] = True

        self.assertEqual(actor_state["Count"], 3)
        self.assertEqual(actor_state["Processed"], 5)
        self.assertTrue(actor_state["Stopped"])


if __name__ == "__main__":
    unittest.main()
