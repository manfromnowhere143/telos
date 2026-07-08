# Agent Handoff Notes

Implemented the next narrow safety layer in `main.py`:
- Added board-boundary checks to prevent moving off the board.
- Added self-collision checks to prevent moving into our own body (excluding the tail which moves).
- Added opponent-body collision checks to prevent moving into other snakes' bodies (excluding their tails).

The edits are bounded and preserve the existing random safe move logic.
