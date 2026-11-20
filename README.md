# Puissance4-L1ST

Connect Four in Python with a Pygame interface: play against a bot or over the network.
The game, the interface, the network code and five generations of AI are written from scratch (the interface is in French).

## Features

- **Solo mode** against a bot with four difficulty levels (search depth 2, 4, 6 and 12)
- **Online multiplayer** over TCP sockets: one player hosts, the other joins with an IP and a port
- **Options menu** with a music volume slider
- **Bot-vs-bot tournaments** (`tournoi.py`): plays many games in parallel processes and counts wins and draws

## The bots

Each version of the Negamax bot (`bots/negamax.py` to `bots/negamaxv5.py`) adds one idea:

| Version | What it adds |
| --- | --- |
| v1 | Plain Negamax search with an evaluation function |
| v2 | Alpha-beta pruning |
| v3 | Iterative deepening under a time limit |
| v4 | Center-first move ordering, and playing/undoing moves on the same board instead of copying it |
| v5 | Transposition table |

`tests.py` benchmarks the board implementation and measures how deep each bot can search.

## Run it

Tested with Python 3.11.

```sh
pip install pygame pygame-widgets
python main.py
```

For online games, the default port and address are in `config.json`.

To compare two bots, edit the bots at the bottom of `tournoi.py` and run:

```sh
python tournoi.py
```

## Project layout

| Folder | Content |
| --- | --- |
| `moteur/` | Game rules: board and game state |
| `bots/` | Random bot and the five Negamax versions |
| `interface/` | Pygame menus and game screen |
| `multijoueur/` | Server and client |
| `assets/` | Interface images |

Started as a university project.
