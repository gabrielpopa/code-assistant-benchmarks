# FlippyBlock Extreme manual review

Run the game normally and award one point for each item. Record the manual score
separately from the automated score; do not expose this rubric to the model during
generation.

- [ ] Title, help, countdown, playing, paused, and game-over states are visually distinct.
- [ ] Menu selection, flap, pause/resume, restart, title-return, and quit controls work.
- [ ] Countdown visibly shows 3, 2, 1, and GO before physics begins.
- [ ] Pausing freezes player physics, obstacles, and score.
- [ ] Collisions with pipes, ceiling, and ground reliably end the run.
- [ ] Passing one obstacle pair awards exactly one point.
- [ ] Two fresh launches produce the same first 20 gap positions.
- [ ] Restarting after game over reproduces that same initial gap sequence.
- [ ] F3 shows accurate values and player, obstacle, and ground hitboxes.
- [ ] V visibly disables non-essential effects without changing gameplay physics.
- [ ] All required visual effects are visible and transitions are smooth.
- [ ] The game remains responsive and near 60 FPS through repeated play/restart cycles.

Manual score: `__/12`
