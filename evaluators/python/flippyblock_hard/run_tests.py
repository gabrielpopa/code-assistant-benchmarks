"""Operator-only evaluator for python/flippyblock/instructions_hard.md."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


Check = Callable[["Context"], None]
CHECKS: list[tuple[str, Check]] = []


def check(name: str):
    def register(function: Check) -> Check:
        CHECKS.append((name, function))
        return function

    return register


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def compact(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


@dataclass
class Context:
    task_directory: Path
    module_path: Path
    source: str
    tree: ast.Module

    @property
    def identifiers(self) -> set[str]:
        result: set[str] = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                result.add(node.id.lower())
            elif isinstance(node, ast.Attribute):
                result.add(node.attr.lower())
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                result.add(node.name.lower())
        return result

    @property
    def strings(self) -> list[str]:
        return [
            node.value
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ]

    @property
    def numbers(self) -> list[float | int]:
        return [
            node.value
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        ]

    def has_identifier_fragment(self, *fragments: str) -> bool:
        return any(
            any(fragment.lower() in identifier for fragment in fragments)
            for identifier in self.identifiers
        )

    def has_string(self, text: str) -> bool:
        needle = compact(text)
        return any(needle in compact(value) for value in self.strings)

    def pygame_constants(self) -> set[str]:
        return {
            node.attr
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "pygame"
        }

    def event_constants(self) -> set[str]:
        """Return pygame constants used either qualified or directly imported."""
        constants = set(self.pygame_constants())
        constants.update(
            node.id
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Name)
            and (node.id.startswith("K_") or node.id in {"QUIT", "MOUSEBUTTONDOWN"})
        )
        return constants


@check("exactly one candidate Python source file")
def _(context: Context) -> None:
    sources = sorted(
        path.name
        for path in context.task_directory.glob("*.py")
        if path.is_file()
    )
    require(sources == ["main.py"], f"expected only main.py, found: {sources}")


@check("valid Python syntax")
def _(context: Context) -> None:
    compile(context.source, str(context.module_path), "exec")


@check("pygame is imported")
def _(context: Context) -> None:
    roots = imported_roots(context.tree)
    require("pygame" in roots, "main.py does not import pygame")


@check("no third-party libraries besides pygame")
def _(context: Context) -> None:
    roots = imported_roots(context.tree)
    allowed = set(sys.stdlib_module_names) | {"pygame", "__future__"}
    unexpected = sorted(roots - allowed)
    require(not unexpected, f"unexpected imports: {', '.join(unexpected)}")


@check("no sound APIs")
def _(context: Context) -> None:
    forbidden = {"mixer", "music", "sound", "sndarray"}
    used = sorted(forbidden & context.identifiers)
    require(not used, f"sound-related APIs found: {', '.join(used)}")


@check("no external assets, saves, config, or tests")
def _(context: Context) -> None:
    allowed_names = {"main.py", "instructions.md", "instructions_hard.md"}
    extras = []
    for path in context.task_directory.iterdir():
        if path.name in allowed_names or path.name == "__pycache__":
            continue
        extras.append(path.name)
    require(not extras, f"unexpected files or directories: {', '.join(sorted(extras))}")
    forbidden_calls = {"open", "write_text", "write_bytes", "json.dump", "pickle.dump"}
    calls = call_names(context.tree)
    used = sorted(name for name in forbidden_calls if name in calls)
    require(not used, f"possible persistence/file output found: {', '.join(used)}")


@check("guarded direct entry point")
def _(context: Context) -> None:
    found = False
    for node in ast.walk(context.tree):
        if not isinstance(node, ast.If):
            continue
        comparison = ast.dump(node.test, include_attributes=False)
        if "__name__" in comparison and "__main__" in comparison:
            found = True
            break
    require(found, "missing if __name__ == '__main__' entry-point guard")


@check("exact 800 by 600 display")
def _(context: Context) -> None:
    assignments = assigned_numeric_constants(context.tree)
    named = assignments.get("width") == 800 and assignments.get("height") == 600
    literal_tuple = any(
        isinstance(node, (ast.Tuple, ast.List))
        and [constant_number(item) for item in node.elts] == [800, 600]
        for node in ast.walk(context.tree)
    )
    require(named or literal_tuple, "could not establish an exact 800x600 display")


@check("60 FPS frame cap")
def _(context: Context) -> None:
    assignments = assigned_numeric_constants(context.tree)
    has_tick = "tick" in context.identifiers
    has_rate = 60 in context.numbers or assignments.get("fps") == 60
    require(has_tick and has_rate, "expected a clock.tick-based 60 FPS loop")


@check("fixed seed 1337")
def _(context: Context) -> None:
    require(1337 in context.numbers, "fixed seed 1337 not found")
    require(
        context.has_identifier_fragment("random", "rng", "seed"),
        "no deterministic random generator is apparent",
    )


@check("restart resets deterministic obstacle generator")
def _(context: Context) -> None:
    candidates = [
        node
        for node in ast.walk(context.tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and ("reset" in node.name.lower() or "restart" in node.name.lower())
    ]
    deterministic_reset = any(
        any(
            isinstance(item, (ast.Name, ast.Attribute))
            and any(word in node_name(item).lower() for word in ("rng", "random", "seed"))
            for item in ast.walk(function)
        )
        for function in candidates
    )
    require(deterministic_reset, "restart/reset does not visibly reset RNG state")


@check("all six required game states")
def _(context: Context) -> None:
    searchable = {compact(value) for value in context.strings} | {
        compact(value) for value in context.identifiers
    }
    missing = []
    aliases = {
        "title": ("title", "menu"),
        "help": ("help", "instructions"),
        "ready": ("ready", "countdown"),
        "playing": ("playing", "play"),
        "paused": ("paused", "pause"),
        "game over": ("gameover",),
    }
    for label, options in aliases.items():
        if not any(any(compact(option) in value for value in searchable) for option in options):
            missing.append(label)
    require(not missing, f"missing states: {', '.join(missing)}")


@check("state labels match their declared state names")
def _(context: Context) -> None:
    mappings = assigned_string_constants(context.tree)
    expected = ("title", "help", "ready", "playing", "paused", "gameover")
    mismatches = []
    for name in expected:
        if name not in mappings:
            continue
        if compact(mappings[name]) != compact(name):
            mismatches.append(f"{name.upper()}={mappings[name]!r}")
    require(not mismatches, f"state/debug labels are misleading: {', '.join(mismatches)}")


@check("structured game components")
def _(context: Context) -> None:
    class_names = [node.name.lower() for node in context.tree.body if isinstance(node, ast.ClassDef)]
    groups = {
        "game/controller": ("game", "controller", "application"),
        "player": ("player", "bird", "block"),
        "obstacle": ("obstacle", "pipe"),
        "particle/effect": ("particle", "effect"),
        "button/menu UI": ("button", "menu", "ui"),
    }
    missing = [
        label
        for label, aliases in groups.items()
        if not any(any(alias in name for alias in aliases) for name in class_names)
    ]
    require(not missing, f"missing component classes: {', '.join(missing)}")


@check("title and complete title menu")
def _(context: Context) -> None:
    required = ("FlippyBlock Extreme", "Start Game", "How to Play", "Quit")
    missing = [text for text in required if not context.has_string(text)]
    require(not missing, f"missing title/menu text: {', '.join(missing)}")


@check("help screen documents every required control")
def _(context: Context) -> None:
    terms = ("Space", "Up", "Mouse", "P", "Escape", "R", "F3", "V", "Q", "title")
    help_text = " ".join(context.strings).lower()
    missing = [term for term in terms if term.lower() not in help_text]
    require(not missing, f"help/control text is missing: {', '.join(missing)}")


@check("flap keyboard and mouse controls")
def _(context: Context) -> None:
    constants = context.event_constants()
    missing = {"K_SPACE", "K_UP", "MOUSEBUTTONDOWN"} - constants
    require(not missing, f"missing flap event constants: {', '.join(sorted(missing))}")


@check("mouse flap is restricted to the left button")
def _(context: Context) -> None:
    mouse_branches = [
        node
        for node in ast.walk(context.tree)
        if isinstance(node, ast.If)
        and "mousebuttondown" in ast.dump(node.test, include_attributes=False).lower()
    ]
    require(mouse_branches, "mouse-button event handling not found")
    require(
        any(
            any(
                isinstance(item, ast.Constant)
                and item.value == 1
                and not isinstance(item.value, bool)
                for item in ast.walk(branch.test)
            )
            for branch in mouse_branches
        ),
        "mouse flap is not visibly restricted to button 1",
    )


@check("pause, restart, and quit controls")
def _(context: Context) -> None:
    constants = context.event_constants()
    required = {"K_p", "K_ESCAPE", "K_r", "K_q", "QUIT"}
    missing = required - constants
    require(not missing, f"missing control constants: {', '.join(sorted(missing))}")


@check("exact F3 and lowercase-v toggle constants")
def _(context: Context) -> None:
    constants = context.pygame_constants()
    require("K_F3" in constants, "must use pygame.K_F3 for the debug toggle")
    require("K_v" in constants, "must use pygame.K_v for the effects toggle")


@check("visible 3-2-1-GO countdown")
def _(context: Context) -> None:
    for number in (1, 2, 3):
        require(number in context.numbers, f"countdown value {number} not found")
    require(context.has_string("GO"), "countdown GO label not found")
    require(
        context.has_identifier_fragment("countdown", "ready_timer", "readytime"),
        "no countdown timing structure found",
    )


@check("obstacles are populated during countdown")
def _(context: Context) -> None:
    require(
        countdown_populates_obstacles(context.tree),
        "countdown can begin with no visible obstacles; populate or advance the obstacle field before play",
    )


@check("countdown freezes gameplay")
def _(context: Context) -> None:
    branches = state_branches(context.tree, "ready") + state_branches(context.tree, "countdown")
    require(branches, "countdown/ready update branch not found")
    violations = gameplay_updates_in(branches)
    require(not violations, f"gameplay advances during countdown: {', '.join(sorted(violations))}")


@check("obstacle gaps and movement")
def _(context: Context) -> None:
    require(context.has_identifier_fragment("gap"), "obstacle gap logic not found")
    require(
        context.has_identifier_fragment("speed", "velocity", "scroll"),
        "obstacle movement logic not found",
    )
    require("rect" in context.identifiers, "pygame rectangle geometry not found")


@check("gap generation uses the resettable seeded RNG")
def _(context: Context) -> None:
    uses_instance_rng = False
    uses_global_rng = False
    for function in (
        node
        for node in ast.walk(context.tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        dump = ast.dump(function, include_attributes=False).lower()
        if "gap" not in function.name.lower() and "gap" not in dump:
            continue
        for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
            name = dotted_call_name(call)
            if any(owner in name for owner in ("self.rng.", "self.random.", "self.generator.")):
                if name.endswith((".uniform", ".randint", ".randrange", ".choice")):
                    uses_instance_rng = True
                    break
            if name in {"random.uniform", "random.randint", "random.randrange", "random.choice"}:
                uses_global_rng = True
        if uses_instance_rng:
            break

    reseeds_global_rng = any(
        dotted_call_name(call) == "random.seed"
        for function in (
            node
            for node in ast.walk(context.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(word in node.name.lower() for word in ("reset", "restart", "start", "new_run"))
        )
        for call in (node for node in ast.walk(function) if isinstance(node, ast.Call))
    )
    require(
        uses_instance_rng or (uses_global_rng and reseeds_global_rng),
        "obstacle gaps do not visibly use RNG state that restart resets",
    )


@check("obstacles continue spawning without long empty stretches")
def _(context: Context) -> None:
    maximum_lead, allowed_lead, spawned = simulate_obstacle_continuity(context)
    require(spawned, "obstacle simulation did not produce any new obstacles")
    require(
        maximum_lead <= allowed_lead,
        f"next obstacle drifted {maximum_lead:.0f}px ahead; expected at most {allowed_lead:.0f}px",
    )


@check("collision with obstacles, ceiling, and ground")
def _(context: Context) -> None:
    require(
        context.has_identifier_fragment("collid", "collision"),
        "collision checking not found",
    )
    require(context.has_identifier_fragment("ground", "floor"), "ground collision not apparent")
    require(
        context.has_identifier_fragment("ceiling", "top") or "y" in context.identifiers,
        "ceiling collision not apparent",
    )


@check("ceiling collision ends the run")
def _(context: Context) -> None:
    collision_functions = [
        node
        for node in ast.walk(context.tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    ceiling_branches = []
    for function in collision_functions:
        for branch in (node for node in ast.walk(function) if isinstance(node, ast.If)):
            test_dump = ast.dump(branch.test, include_attributes=False).lower()
            has_upper_boundary = (
                "ceiling" in test_dump
                or "upper" in test_dump
                or "attr='top'" in test_dump
                or "id='top'" in test_dump
                or (("id='y'" in test_dump or "attr='y'" in test_dump) and "value=0" in test_dump)
            )
            if has_upper_boundary:
                ceiling_branches.append(branch)
    require(ceiling_branches, "explicit ceiling collision branch not found")
    require(
        any(branch_ends_run(branch) for branch in ceiling_branches),
        "ceiling contact is detected but does not transition to game over",
    )


@check("score and one-pass obstacle scoring")
def _(context: Context) -> None:
    require("score" in context.identifiers, "score state not found")
    require(
        context.has_identifier_fragment("scored", "passed"),
        "per-obstacle passed/scored guard not found",
    )


@check("pause menu offers all required actions")
def _(context: Context) -> None:
    required = ("Resume", "Restart", "Title", "Quit")
    missing = [text for text in required if not context.has_string(text)]
    require(not missing, f"pause action text is missing: {', '.join(missing)}")


@check("menu navigation does not apply a key movement twice")
def _(context: Context) -> None:
    duplicates = []
    for class_node in (
        node
        for node in context.tree.body
        if isinstance(node, ast.ClassDef) and any(word in node.name.lower() for word in ("menu", "button", "ui"))
    ):
        for function in (
            node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(word in node.name.lower() for word in ("key", "move", "navigate"))
        ):
            for statements in statement_lists(function):
                for first, second in zip(statements, statements[1:]):
                    if ast.dump(first, include_attributes=False) == ast.dump(second, include_attributes=False):
                        duplicates.append(f"{class_node.name}.{function.name}")
    require(not duplicates, f"duplicate consecutive navigation update in: {', '.join(sorted(set(duplicates)))}")


@check("paused state freezes gameplay")
def _(context: Context) -> None:
    branches = state_branches(context.tree, "paused") + state_branches(context.tree, "pause")
    require(branches, "paused update branch not found")
    violations = gameplay_updates_in(branches)
    require(not violations, f"gameplay advances while paused: {', '.join(sorted(violations))}")


@check("game-over screen content")
def _(context: Context) -> None:
    required = ("Game Over", "Score", "Restart", "Title", "Quit")
    missing = [text for text in required if not context.has_string(text)]
    require(not missing, f"game-over content is missing: {', '.join(missing)}")


@check("new run resets player, obstacles, and score")
def _(context: Context) -> None:
    candidates = [
        node
        for node in ast.walk(context.tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            word in node.name.lower()
            for word in ("start_run", "new_run", "restart", "reset_game", "reset_run")
        )
    ]
    complete_reset = False
    for function in candidates:
        calls = [dotted_call_name(node) for node in ast.walk(function) if isinstance(node, ast.Call)]
        resets_player = any("player" in name and name.endswith(".reset") for name in calls)
        resets_obstacles = any(
            any(owner in name for owner in ("obstacle", "pipe", "field"))
            and name.endswith((".reset", ".clear", ".restart"))
            for name in calls
        )
        resets_score = any(
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Attribute)
                and target.attr.lower() == "score"
                for target in assignment_targets(node)
            )
            and constant_number(node.value) == 0
            for node in ast.walk(function)
        )
        if resets_player and resets_obstacles and resets_score:
            complete_reset = True
            break
    require(complete_reset, "new-run flow does not visibly reset player, obstacles, and score together")


@check("required visual-effect systems")
def _(context: Context) -> None:
    groups = {
        "parallax background": ("parallax", "background", "layer"),
        "player animation": ("squash", "stretch", "flap_anim", "flaptime"),
        "particles": ("particle",),
        "score pop": ("score_pop", "scorepop"),
        "collision flash/shake/burst": ("shake", "flash", "burst"),
        "fade transition": ("fade", "transition"),
    }
    missing = [
        label
        for label, fragments in groups.items()
        if not context.has_identifier_fragment(*fragments)
    ]
    if not animated_ground_is_apparent(context.tree):
        missing.append("animated ground")
    require(not missing, f"visual systems not apparent: {', '.join(missing)}")


@check("visual-effects toggle has stored state")
def _(context: Context) -> None:
    require(
        context.has_identifier_fragment(
            "visual_effect", "effects_enabled", "effects_on", "fx_enabled", "fx_on", "vfx", "visuals"
        ),
        "no stored visual-effects enabled/disabled state found",
    )


@check("complete debug overlay data")
def _(context: Context) -> None:
    debug_text = " ".join(value for value in context.strings if compact(value)).lower()
    terms = {
        "FPS": ("fps",),
        "state": ("state",),
        "player position": ("player", "position", "player y"),
        "vertical velocity": ("velocity", "vel", "vy"),
        "score": ("score",),
        "obstacles": ("obstacle", "pipe"),
        "seed": ("seed",),
        "visual effects": ("effect", "fx"),
    }
    missing = [label for label, aliases in terms.items() if not any(term in debug_text for term in aliases)]
    require(not missing, f"debug overlay labels are missing: {', '.join(missing)}")


@check("debug hitbox rendering")
def _(context: Context) -> None:
    require(context.has_identifier_fragment("debug"), "debug state/rendering not found")
    require("draw" in context.identifiers and "rect" in context.identifiers, "hitbox drawing not found")
    require(context.has_identifier_fragment("hitbox") or "colliderect" in context.identifiers,
            "visible collision geometry is not apparent")


@check("no runtime difficulty scaling")
def _(context: Context) -> None:
    gameplay_constants = {
        name
        for name in assigned_numeric_constants(context.tree)
        if any(word in name for word in ("gravity", "flap", "pipe_speed", "gap", "spacing"))
    }
    mutations: set[str] = set()
    for function in (
        node
        for node in ast.walk(context.tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        for node in ast.walk(function):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for target in assignment_targets(node):
                    if isinstance(target, ast.Name) and target.id.lower() in gameplay_constants:
                        mutations.add(target.id)
    require(not mutations, f"gameplay constants change at runtime: {', '.join(sorted(mutations))}")


@check("headless launch remains stable")
def _(context: Context) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "SDL_VIDEODRIVER": "dummy",
            "SDL_AUDIODRIVER": "dummy",
            "PYGAME_HIDE_SUPPORT_PROMPT": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=context.task_directory,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(1.5)
        return_code = process.poll()
        if return_code is not None:
            stdout, stderr = process.communicate(timeout=1)
            detail = (stderr or stdout).strip()[-1000:]
            raise AssertionError(f"game exited early with code {return_code}: {detail}")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)


def imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                roots.add("<relative>")
            elif node.module:
                roots.add(node.module.split(".")[0])
    return roots


def node_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = node_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def call_names(tree: ast.AST) -> set[str]:
    return {
        node_name(node.func).lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }


def constant_number(node: ast.AST):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    return None


def assignment_targets(node: ast.AST) -> list[ast.expr]:
    if isinstance(node, ast.Assign):
        return node.targets
    if isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        return [node.target]
    return []


def assigned_numeric_constants(tree: ast.Module) -> dict[str, float | int]:
    result: dict[str, float | int] = {}
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
        if value is None:
            continue
        if isinstance(value, (ast.Tuple, ast.List)):
            values = [constant_number(item) for item in value.elts]
            if len(targets) == 1 and isinstance(targets[0], (ast.Tuple, ast.List)):
                for target, number in zip(targets[0].elts, values):
                    if isinstance(target, ast.Name) and number is not None:
                        result[target.id.lower()] = number
        else:
            number = constant_number(value)
            if number is not None:
                for target in targets:
                    if isinstance(target, ast.Name):
                        result[target.id.lower()] = number
    return result


def assigned_string_constants(tree: ast.Module) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if len(targets) != 1:
            continue
        target = targets[0]
        if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                result[target.id.lower()] = node.value.value
        elif isinstance(target, (ast.Tuple, ast.List)) and isinstance(node.value, (ast.Tuple, ast.List)):
            for item, value in zip(target.elts, node.value.elts):
                if (
                    isinstance(item, ast.Name)
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    result[item.id.lower()] = value.value
    return result


def statement_lists(node: ast.AST):
    for child in ast.walk(node):
        for field in ("body", "orelse", "finalbody"):
            statements = getattr(child, field, None)
            if isinstance(statements, list) and statements:
                yield statements


def dotted_call_name(call: ast.Call) -> str:
    return node_name(call.func).lower()


def is_ready_test(test: ast.AST) -> bool:
    return "ready" in ast.dump(test, include_attributes=False).lower()


def state_branches(tree: ast.Module, state_name: str) -> list[ast.If]:
    needle = state_name.lower().replace("_", "")
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        normalized = ast.dump(node.test, include_attributes=False).lower().replace("_", "")
        if needle in normalized:
            result.append(node)
    return result


def gameplay_updates_in(branches: list[ast.If]) -> set[str]:
    violations: set[str] = set()
    for branch in branches:
        branch_module = ast.Module(body=branch.body, type_ignores=[])
        for call in (node for node in ast.walk(branch_module) if isinstance(node, ast.Call)):
            name = dotted_call_name(call)
            if name.endswith(".update") and any(
                owner in name for owner in ("player", "bird", "block", "obstacle", "pipe", "field")
            ):
                if not (call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value is False):
                    violations.add(name)
        for node in ast.walk(branch_module):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for target in assignment_targets(node):
                    if isinstance(target, ast.Attribute) and target.attr.lower() == "score":
                        violations.add(node_name(target))
    return violations


def branch_ends_run(branch: ast.If) -> bool:
    body = ast.Module(body=branch.body, type_ignores=[])
    for node in ast.walk(body):
        if isinstance(node, ast.Call):
            name = dotted_call_name(node).replace("_", "")
            if any(word in name for word in ("die", "gameover", "endrun", "killplayer")):
                return True
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value_dump = ast.dump(node.value, include_attributes=False).lower().replace("_", "")
            if "gameover" in value_dump or "dead" in value_dump:
                return True
    return False


def is_obstacle_receiver_call(call: ast.Call, methods: set[str]) -> bool:
    name = dotted_call_name(call)
    parts = name.split(".")
    if not parts or parts[-1] not in methods:
        return False
    return any(word in name for word in ("obstacle", "pipe", "field"))


def countdown_populates_obstacles(tree: ast.Module) -> bool:
    """Recognize common ways of ensuring READY has at least one obstacle.

    A solution may advance/spawn its obstacle manager in the READY branch, spawn
    explicitly when starting a run, or pre-populate the obstacle manager's reset.
    Merely clearing/resetting a field does not count.
    """
    populate_methods = {"update", "spawn", "add", "append", "populate", "create"}

    for branch in (node for node in ast.walk(tree) if isinstance(node, ast.If)):
        if not is_ready_test(branch.test):
            continue
        for item in ast.walk(ast.Module(body=branch.body, type_ignores=[])):
            if isinstance(item, ast.Call) and is_obstacle_receiver_call(item, populate_methods):
                return True

    for function in (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(word in node.name.lower() for word in ("start", "restart", "begin", "new_run"))
    ):
        for item in ast.walk(function):
            if isinstance(item, ast.Call) and is_obstacle_receiver_call(
                item, {"spawn", "add", "append", "populate", "create"}
            ):
                return True

    for class_node in (
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(word in node.name.lower() for word in ("obstacle", "pipe", "field"))
    ):
        for function in class_node.body:
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if "reset" not in function.name.lower() and function.name != "__init__":
                continue
            for item in ast.walk(function):
                if isinstance(item, ast.Call):
                    call_name = dotted_call_name(item)
                    if call_name.endswith(".append") or any(
                        word in call_name.split(".")[-1] for word in ("spawn", "populate", "create")
                    ):
                        return True
    return False


def animated_ground_is_apparent(tree: ast.Module) -> bool:
    """Check for a ground/floor component whose update mutates animation state."""
    for class_node in tree.body:
        if not isinstance(class_node, ast.ClassDef):
            continue
        if not any(word in class_node.name.lower() for word in ("ground", "floor")):
            continue
        methods = {
            node.name: node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        update = methods.get("update")
        if update is None or "draw" not in methods:
            continue
        has_arithmetic = any(isinstance(node, (ast.BinOp, ast.AugAssign)) for node in ast.walk(update))
        mutated_self_fields = {
            node.attr
            for node in ast.walk(update)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and isinstance(node.ctx, ast.Store)
        }
        if has_arithmetic and mutated_self_fields:
            return True

    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        methods = {
            node.name: node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        ground_drawers = [
            function
            for name, function in methods.items()
            if "ground" in name.lower() or "floor" in name.lower()
        ]
        if not ground_drawers:
            continue
        animation_fields = {
            node.attr
            for function in ground_drawers
            for node in ast.walk(function)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
        }
        for function in methods.values():
            for node in ast.walk(function):
                if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    continue
                if not any(isinstance(item, (ast.BinOp, ast.AugAssign)) for item in ast.walk(node)):
                    continue
                for target in assignment_targets(node):
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                        and target.attr in animation_fields
                    ):
                        return True
    return False


def simulate_obstacle_continuity(context: Context) -> tuple[float, float, bool]:
    """Run a common obstacle-manager component without starting the game loop."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    module_name = f"flippyblock_continuity_{os.getpid()}_{time.time_ns()}"
    spec = importlib.util.spec_from_file_location(module_name, context.module_path)
    require(spec is not None and spec.loader is not None, "could not import candidate module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        field_classes = [
            value
            for name, value in vars(module).items()
            if inspect.isclass(value)
            and any(word in name.lower() for word in ("obstaclefield", "pipefield", "obstacles"))
            and callable(getattr(value, "update", None))
        ]
        require(field_classes, "no independently testable obstacle-field component found")
        field_class = field_classes[0]
        try:
            field = field_class()
        except TypeError as exc:
            raise AssertionError(f"could not construct {field_class.__name__}: {exc}") from exc
        reset = getattr(field, "reset", None)
        if callable(reset):
            reset()

        list_attribute = obstacle_list_attribute(field)
        if list_attribute is None:
            call_obstacle_update(field, module)
            list_attribute = obstacle_list_attribute(field)
        require(list_attribute is not None, "could not locate the obstacle collection")

        initial = list(getattr(field, list_attribute))
        require(initial, "obstacle manager starts empty and does not spawn on its first update")
        initial_x = sorted(float(item.x) for item in initial if hasattr(item, "x"))
        require(initial_x, "obstacles do not expose horizontal positions")

        width = float(getattr(module, "WIDTH", 800))
        player_x = float(getattr(module, "PLAYER_X", width * 0.2))
        initial_ahead = [x for x in initial_x if x >= player_x]
        require(initial_ahead, "no initial obstacle appears ahead of the player")
        initial_lead = min(initial_ahead) - player_x
        spacings = [b - a for a, b in zip(initial_x, initial_x[1:]) if b > a]
        configured_spacing = getattr(module, "OBSTACLE_SPACING", getattr(module, "PIPE_SPACING", width / 3))
        spacing = min(spacings) if spacings else float(configured_spacing)
        allowed_lead = max(width, initial_lead + spacing * 1.25)

        initial_ids = {id(item) for item in initial}
        spawned = False
        maximum_lead = initial_lead
        for _ in range(3600):
            call_obstacle_update(field, module)
            obstacles = list(getattr(field, list_attribute))
            spawned = spawned or any(id(item) not in initial_ids for item in obstacles)
            ahead = [float(item.x) - player_x for item in obstacles if hasattr(item, "x") and item.x >= player_x]
            if not ahead:
                return float("inf"), allowed_lead, spawned
            maximum_lead = max(maximum_lead, min(ahead))
        return maximum_lead, allowed_lead, spawned
    finally:
        sys.modules.pop(module_name, None)


def obstacle_list_attribute(field: object) -> str | None:
    preferred = ("obstacles", "pipes", "items")
    for name in preferred:
        value = getattr(field, name, None)
        if isinstance(value, list) and (not value or all(hasattr(item, "x") for item in value)):
            return name
    for name, value in vars(field).items():
        if isinstance(value, list) and (not value or all(hasattr(item, "x") for item in value)):
            return name
    return None


def call_obstacle_update(field: object, module: object) -> None:
    update = field.update
    parameters = list(inspect.signature(update).parameters.values())
    arguments = []
    for parameter in parameters:
        name = parameter.name.lower()
        if "dt" in name or "delta" in name:
            arguments.append(1 / 60)
        elif "speed" in name:
            arguments.append(float(getattr(module, "PIPE_SPEED", 220.0)))
        elif parameter.default is inspect.Parameter.empty:
            arguments.append(1 / 60)
    update(*arguments)


def load_context(task_directory: Path) -> Context:
    module_path = task_directory / "main.py"
    if not module_path.is_file():
        raise FileNotFoundError(f"candidate output not found: {module_path}")
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    return Context(task_directory, module_path, source, tree)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 run_tests.py PATH_TO_FLIPPYBLOCK_DIRECTORY")
        return 2

    task_directory = Path(sys.argv[1]).resolve()
    try:
        context = load_context(task_directory)
    except Exception as exc:
        print(f"Could not load candidate: {type(exc).__name__}: {exc}")
        print(f"0/{len(CHECKS)} automated checks passed")
        return 1

    failures: list[tuple[str, str]] = []
    for name, function in CHECKS:
        try:
            function(context)
        except Exception as exc:
            failures.append((name, f"{type(exc).__name__}: {exc}"))

    passed = len(CHECKS) - len(failures)
    print(f"{passed}/{len(CHECKS)} automated checks passed")
    if failures:
        print("Failures:")
        for name, detail in failures:
            print(f"- {name}: {detail}")
    print("Manual visual review is still required; see MANUAL_REVIEW.md.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
