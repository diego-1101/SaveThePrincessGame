# Save The Princess - Game Instructions

## How to Run
1. Install PgZero: `pip install pgzero`
2. Run the game: `pgzrun game.py`

## Asset Requirements
Ensure the `images/` and `sounds/` folders are in the same directory as `game.py`.
The code expects files named exactly as specified (e.g., `knight_idle_1.png`).

## Controls
- **Arrow Keys**: Move
- **Space**: Jump
- **Mouse**: Interact with menus

## Configuration
Inside `game.py`, you can modify:
- `PLAYER_SPEED` / `PLAYER_SPEED_CARRYING`
- `GRAVITY` / `GRAVITY_CARRYING`
- Window size (`WIDTH`, `HEIGHT`)
- Enemy timings in the classes `EnemyFire` / `EnemySword`
