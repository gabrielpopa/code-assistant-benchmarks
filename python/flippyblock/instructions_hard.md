You are an expert Python developer.

Create a complete, polished, self-contained Flappy Bird-style arcade game called **FlippyBlock Extreme** in Python using **only pygame**.

The game must be runnable directly with:

```bash
python main.py
```

Return only the final contents of `main.py`.

Do not use external assets of any kind. All graphics, UI elements, fonts, animations, particles, and other visuals must be created directly in code.

## Hard constraints

* Use Python and pygame only.
* Window resolution must be exactly **800x600**.
* The game must have **no sound**.
* Do not implement difficulty levels.
* Do not implement dynamic difficulty scaling.
* Do not implement high score persistence, save files, or external config files.
* Do not write tests.
* The game will be reviewed and run manually.

## Core gameplay

Implement a responsive Flappy Bird-style game where the player controls a square/block character that flaps upward and falls due to gravity.

The game must include:

* Smooth gravity and flap physics
* Pipe/obstacle pairs with gaps
* Collision detection with obstacles, ceiling, and ground
* Score increase when successfully passing obstacles
* Restart after game over
* Stable 60 FPS behavior
* No crashes during normal play

## Deterministic obstacle generation

The obstacle sequence must be deterministic.

* Use a fixed seed value of **1337**.
* The first 20 obstacle gaps must appear in the same order every time the game is launched.
* Restarting from game over must reset the game to the same initial obstacle sequence.
* Do not use fully random obstacle placement during gameplay.

## Required game states

Implement a clean state machine with at least these states:

1. Title screen
2. Help/instructions screen
3. Ready/countdown state
4. Playing state
5. Paused state
6. Game over state

The current state should be clear to the player at all times.

## Title screen

The title screen must include:

* Game title: **FlippyBlock Extreme**
* A short animated background
* Menu options:

  * Start Game
  * How to Play
  * Quit
* Keyboard instructions for selecting menu options
* A small animated preview of the player block flapping or bobbing

## Help screen

The help screen must explain all controls:

* Space / Up Arrow / Left Mouse Button: flap
* P or Escape: pause/resume
* R: restart after game over
* F3: toggle debug overlay
* V: toggle visual effects
* Q or Escape from title menu: quit

The help screen must have a clear way to return to the title screen.

## Countdown before play

When starting or restarting a run, show a visible countdown:

* 3
* 2
* 1
* GO

During the countdown, the player and obstacles should be visible but gameplay should not yet be active.

## Pause functionality

During gameplay, pressing P or Escape must pause the game.

While paused:

* Physics must stop
* Obstacles must stop
* Score must not change
* A pause overlay must appear
* The player must be able to resume, restart, return to title, or quit

## Game over screen

The game over screen must include:

* Final score
* Restart option
* Return to title option
* Quit option
* A short visual effect indicating the collision, such as screen shake, flash, or particles

## Visual polish requirements

Implement all of the following visual features directly in pygame code:

* Parallax background with at least three visual layers
* Animated ground or floor strip
* Player flap animation or squash/stretch effect
* Particles emitted when the player flaps
* Particles or burst effect on collision
* Score pop animation when gaining a point
* Screen shake or flash on collision
* Fade transition between major screens
* Clean HUD with readable score and control hints

Pressing **V** must toggle non-essential visual effects on/off. Core gameplay must remain unchanged.

## Debug overlay

Pressing **F3** must toggle a debug overlay.

When enabled, the overlay must show:

* FPS
* Current game state
* Player y-position
* Player vertical velocity
* Current score
* Number of active obstacles
* Fixed seed value
* Whether visual effects are enabled

When debug mode is enabled, draw visible hitboxes for:

* Player
* Obstacles
* Ground collision area

## Code organization

Even though everything is in one file, organize the code cleanly.

Use appropriate classes or structured components for:

* Game/application controller
* Player
* Obstacles
* Particles or visual effects
* Buttons/menu items or UI helpers
* State management

Avoid writing the entire game as one giant unstructured loop.

## Manual review expectations

The final result should feel like a complete small standalone pygame game, not a minimal prototype.

It should be easy for a human reviewer to evaluate:

* Whether the required states exist
* Whether the deterministic obstacle sequence works
* Whether controls are responsive
* Whether pause/restart/title flows are correct
* Whether the debug overlay is accurate
* Whether visual effects are implemented and toggleable
* Whether the code is clean and maintainable

## Process requirements

Before returning the final answer:

1. Produce the full implementation.
2. Review your own code for bugs, edge cases, and correctness.
3. Check that all required controls and states are implemented.
4. Correct any issues you find.
5. Return only the final corrected `main.py` code.

Return only code. Do not include explanations, markdown, comments outside the code, or review notes.

use pygame.K_F3 uppercase for F3 and pygame.K_v lowercase for v
