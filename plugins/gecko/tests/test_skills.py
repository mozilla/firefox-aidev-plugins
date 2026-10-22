"""Offline checks for the gecko plugin skills.

Run from the repository root:
  python3 -m unittest discover -s plugins/gecko/tests -v

The profiler-cli checks need `profiler-cli` on PATH. They are skipped when it is
missing, unless GECKO_TESTS_REQUIRE_TOOLS=1 is set, as in CI.
"""
import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from fmt_tables import format_text

PLUGIN = Path(__file__).resolve().parents[1]
REPO = PLUGIN.parents[1]
SKILLS = PLUGIN / "skills"
REQUIRE_TOOLS = os.environ.get("GECKO_TESTS_REQUIRE_TOOLS") == "1"


def frontmatter(path: Path) -> dict:
    """The top-level keys of a SKILL.md frontmatter block, folded `>` values joined."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    data, key = {}, None
    for line in m.group(1).splitlines():
        top = re.match(r"([A-Za-z][\w-]*):\s*(.*)", line)
        if top:
            key, value = top.groups()
            data[key] = "" if value in (">", "|") else value.strip()
        elif key and line.startswith(" "):
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def code_spans(text: str) -> list:
    """Inline code spans and the lines of fenced code blocks."""
    spans = []
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
        spans.extend(block.splitlines())
    without_blocks = re.sub(r"```.*?```", "", text, flags=re.S)
    spans.extend(re.findall(r"`([^`\n]+)`", without_blocks))
    return spans


def profiler_cli_commands() -> list:
    """(file, command path, flags) for each profiler-cli command the skills tell the agent to run."""
    found = []
    for md in sorted(SKILLS.rglob("*.md")):
        for span in code_spans(md.read_text(encoding="utf-8")):
            span = span.split("#", 1)[0]
            m = re.match(r"\s*profiler-cli\s+(.*)", span)
            rest = m.group(1) if m else span if re.match(r"(thread|marker|profile|zoom|session) [a-z]", span) else None
            if rest is None:
                continue
            tokens = rest.split()
            path = []
            for tok in tokens:
                if not re.fullmatch(r"[a-z][a-z-]*", tok) or len(path) == 2:
                    break
                path.append(tok)
            if not path:
                continue
            flags = sorted({t for t in tokens if re.fullmatch(r"--[a-z][a-z-]*", t)})
            found.append((md.relative_to(PLUGIN).as_posix(), path, flags))
    return found


class TestPluginFiles(unittest.TestCase):
    def test_plugin_and_marketplace_agree(self):
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], PLUGIN.name)
        market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        entries = [p for p in market["plugins"] if p["name"] == manifest["name"]]
        self.assertEqual(len(entries), 1, "the plugin needs one marketplace entry")
        self.assertEqual(entries[0]["source"], f"./plugins/{PLUGIN.name}")

    def test_every_skill_has_valid_frontmatter(self):
        skills = sorted(p for p in SKILLS.iterdir() if p.is_dir())
        self.assertTrue(skills)
        for skill in skills:
            meta = frontmatter(skill / "SKILL.md")
            self.assertEqual(meta.get("name"), skill.name, f"{skill.name}: name must match the folder")
            self.assertTrue(meta.get("description"), f"{skill.name}: no description")

    def test_every_skill_can_be_invoked(self):
        # The plugin has no hub skill that calls the others, so a hidden skill
        # cannot be reached with its slash command.
        for skill_md in SKILLS.glob("*/SKILL.md"):
            self.assertNotEqual(frontmatter(skill_md).get("user-invocable"), "false",
                                f"{skill_md.parent.name}: hidden from the slash menu")

    def test_no_skill_pre_approves_every_shell_command(self):
        # allowed-tools runs the listed tools without a prompt, so Bash must be
        # scoped to the commands the skill needs, as Bash(<command> *).
        for skill_md in SKILLS.glob("*/SKILL.md"):
            tools = frontmatter(skill_md).get("allowed-tools", "")
            items = [t.strip() for t in tools.strip("[]").split(",")]
            self.assertNotIn("Bash", items, f"{skill_md.parent.name}: allowed-tools pre-approves all of Bash")

    def test_relative_links_resolve(self):
        for md in PLUGIN.rglob("*.md"):
            for target in re.findall(r"\]\(([^)#:\s]+)\)", md.read_text(encoding="utf-8")):
                self.assertTrue((md.parent / target).exists(),
                                f"{md.relative_to(PLUGIN)}: broken link to {target}")

    def test_tables_are_aligned(self):
        # Fix with: python3 plugins/gecko/tests/fmt_tables.py <file>
        for md in sorted(PLUGIN.rglob("*.md")):
            text = md.read_text(encoding="utf-8")
            self.assertEqual(format_text(text), text, f"{md.relative_to(PLUGIN)}: a table is not aligned")

    def test_every_domain_file_is_linked_from_its_skill(self):
        # A pack or catalog that its skill does not link is never read.
        for skill in SKILLS.iterdir():
            text = (skill / "SKILL.md").read_text(encoding="utf-8") if skill.is_dir() else ""
            for sub in ("domains", "references", "knowledge"):
                for f in sorted((skill / sub).glob("*.md")):
                    self.assertIn(f"]({sub}/{f.name})", text,
                                  f"{skill.name}: {sub}/{f.name} is not in the skill's table")


class TestSpecCheckHosts(unittest.TestCase):
    def setUp(self):
        self.text = (SKILLS / "spec-check/SKILL.md").read_text(encoding="utf-8")
        start = self.text.index("Only fetch from these trusted domains")
        self.allowed = self.text[start:self.text.index("\n\n", start)]

    def test_dom_and_css_spec_hosts_are_trusted(self):
        for host in ("`*.spec.whatwg.org`", "`drafts.csswg.org`", "`w3c.github.io`", "`tc39.es`"):
            self.assertIn(host, self.allowed)

    def test_every_linked_spec_host_is_trusted(self):
        hosts = set()
        for md in [SKILLS / "spec-check/SKILL.md", *sorted((SKILLS / "spec-check/references").glob("*.md"))]:
            hosts |= set(re.findall(r"https://([a-z0-9.-]+)", md.read_text(encoding="utf-8")))
        for host in sorted(hosts):
            if host.endswith(".spec.whatwg.org") or host == "github.com":
                continue
            self.assertIn(f"`{host}`", self.allowed, f"spec-check links to {host} but does not trust it")


@unittest.skipUnless(shutil.which("profiler-cli") or REQUIRE_TOOLS, "profiler-cli is not installed")
class TestProfilerCliCommands(unittest.TestCase):
    def help(self, path):
        r = subprocess.run(["profiler-cli", *path, "--help"], capture_output=True, text=True, timeout=60)
        return r.stdout + r.stderr

    def test_commands_were_found(self):
        self.assertGreater(len(profiler_cli_commands()), 10)

    def test_every_command_and_flag_exists(self):
        for where, path, flags in profiler_cli_commands():
            with self.subTest(where=where, command=" ".join(path)):
                out = self.help(path)
                usage = re.search(r"Usage: profiler-cli ([a-z -]*?)(?: \[| <|$)", out, re.M)
                self.assertIsNotNone(usage, out[:200])
                self.assertEqual(usage.group(1).split(), path, f"profiler-cli has no command {' '.join(path)!r}")
                for flag in flags:
                    self.assertRegex(out, rf"(?<![\w-]){re.escape(flag)}(?![\w-])",
                                     f"profiler-cli {' '.join(path)} has no {flag}")


class TestProfilerSessionCleanup(unittest.TestCase):
    # A profiler-cli session is a daemon that keeps the whole profile in memory
    # and never exits on its own, so analyze-profile must stop and verify it.
    def setUp(self):
        self.text = (SKILLS / "analyze-profile/SKILL.md").read_text(encoding="utf-8")
        # A command has a placeholder; a bare name such as `profiler-cli load` is prose.
        self.commands = [c for c in code_spans(self.text)
                         if c.lstrip().startswith("profiler-cli ") and "<" in c]

    def test_checklist_comes_before_step_1(self):
        self.assertLess(self.text.index("## ⚠️ Session cleanup checklist (REQUIRED)"),
                        self.text.index("## Step 1"))

    def test_every_load_names_its_session(self):
        loads = [c for c in self.commands if re.match(r"\s*profiler-cli load\b", c)]
        self.assertTrue(loads)
        for c in loads:
            self.assertIn("--session <id>", c)

    def test_every_stop_is_verified(self):
        stops = [c for c in self.commands if re.match(r"\s*profiler-cli stop\b", c)]
        self.assertTrue(stops)
        for c in stops:
            self.assertIn("--session <id>", c)
            self.assertIn('profiler-cli session list | grep -F -- "<id>"', c, f"stop without verify: {c}")

    def test_never_stops_every_session(self):
        for line in self.text.splitlines():
            if "stop --all" in line:
                self.assertRegex(line, r"Never run `profiler-cli stop --all`")

    def test_report_says_the_session_was_stopped(self):
        report = self.text[self.text.index("## Step 4"):]
        self.assertRegex(report, r"Session:\s+<id> stopped")


if __name__ == "__main__":
    unittest.main()
