# Agent Notes

I have implemented Step 1 (preventing the snake from moving out of bounds) and Step 2 (preventing the snake from colliding with itself) in `main.py`.

- **Step 1**: Added checks against `board_width` and `board_height` to ensure the snake doesn't move off the board.
- **Step 2**: Added checks against `my_body` to ensure the snake doesn't move into a cell occupied by its own body.

These are safe, bounded improvements to the bot's survival logic.
