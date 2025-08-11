# 🎮 AI Wumpus World Game

A sophisticated implementation of the classic Wumpus World AI problem with both graphical and console interfaces. Features intelligent KB (Knowledge Base) agents, visual effects, sound, and advanced gameplay mechanics.

## 🚀 Quick Start

### Installation
```bash

# Install required dependencies
pip install -r requirements.txt

# Run the game with default settings
python main.py

# Run the game with argument settings, using KB Agent
python main.py 4 1 0.01
```

## 🎯 Game Overview

The Wumpus World is a classic AI problem where an agent (hunter) navigates a dangerous cave system to find gold while avoiding deadly pits and the fearsome Wumpus creatures. The agent must use logical reasoning to safely explore the unknown world.

### 🎮 Game Elements

- **🏹 Hunter (Agent)**: Your character that explores the world
- **👹 Wumpus**: Deadly creatures that kill on contact (makes scream sound when killed)
- **🕳️ Pits**: Deadly traps that cause instant death
- **💰 Gold**: The treasure you must collect and bring home
- **🚪 Exit**: Starting position (0,0) where you must return with gold

### 🌟 Game Features

- **Dual Interface**: Beautiful GUI with fog of war effects OR console mode
- **Smart AI Agents**: Knowledge-based reasoning vs random behavior
- **Sound Effects**: Immersive audio including Wumpus scream when killed
- **Visual Effects**: Dynamic lighting, percept warnings, animations
- **Advanced Mechanics**: Moving Wumpus module for extra challenge
- **Flexible Configuration**: Customizable grid size, difficulty, and game modes

## 🎮 How to Play

### Basic Commands (GUI Mode)
- **Space**: Manual step-by-step execution
- **A**: Toggle auto-play mode
- **L**: Toggle fog of war lighting effect
- **M**: Toggle moving Wumpus module (advanced)
- **H**: Show/hide help and controls
- **R**: Restart game
- **Q**: Quit game

### Game Objective
1. **Explore** the cave system safely
2. **Find** the gold treasure
3. **Return** to the starting position (0,0)
4. **Climb** out to win with the gold

### Percepts (Clues)
The agent receives sensory information:
- **💨 Breeze**: Indicates adjacent pit
- **🦨 Stench**: Indicates adjacent Wumpus  
- **✨ Glitter**: Gold is in current cell
- **💥 Bump**: Hit a wall (boundary)
- **😱 Scream**: Wumpus killed by arrow

## 🛠️ Game Modes & Configuration

### Running the Game

#### Default Game (8x8 grid, 2 Wumpus, 20% pits, KB agent, GUI)
```bash
python main.py
```
#### Full Custom Configuration
```bash
python main.py [grid_size] [num_wumpus] [pit_probability] [agent]
```

### Command Line Arguments

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `grid_size` | Grid size (NxN world) | 8 | `4` for 4x4 |
| `num_wumpus` | Number of Wumpuses | 2 | `1` for single Wumpus |
| `pit_prob` | Pit probability (0.0-1.0) | 0.2 | `0.1` for 10% pits |
| `--console` | Console mode instead of GUI | GUI | Add for text mode |
| `-r, --random` | Use random agent | KB agent | Add for random behavior |
| `-a, --kb-agent` | Use KB agent (default) | KB agent | Explicit KB agent |

### Example Configurations

```bash
# Console mode for CLI-based play
python main.py 4 1 0.01 --console

# Random agent for
python main.py 4 1 0.01 -r

#GUI mode with KB Agent
python main.py 4 2 0.02 -a


## 🧠 AI Agents

### Knowledge-Based Agent (Default)
- **Logical Reasoning**: Uses propositional logic and inference rules
- **Safety Analysis**: Determines safe vs dangerous cells
- **Strategic Planning**: Plans optimal paths using A* algorithm
- **Memory**: Maintains knowledge base of discovered facts
- **Smart Shooting**: Only shoots arrows when Wumpus location is certain

### Random Agent
- **Comparison Baseline**: Shows performance without intelligence
- **Random Behavior**: Makes random legal moves
- **Simple Logic**: Basic gold collection and climbing

## 📁 Project Structure

```bash
AI-Wumpus-World/
├── Source/                     # Main game directory
│   ├── requirements.txt        # Requirement libraries
│   ├── README.md               # Description and instruction
│   ├── main.py                 # Main game with gui implement
│   ├── config.py               # Configuration and asset loading
│   ├── environment.py          # Game world and rules
│   ├── agent.py                # AI agent implementations
│   ├── knowledge_base.py       # Logic and inference engine
│   ├── planner.py              # A* pathfinding algorithm
│   ├── utils.py                # Utility functions
│   └── assets/                 # Game assets
│       ├── hunter/             # Hunter sprites
│       ├── wumpus/             # Wumpus sprites & sounds
│       ├── warnings/           # Percept indicators
│       ├── gold.png            # Gold sprite
│       ├── pit.png             # Pit sprite
│       ├── light.png           # Lighting/For effect

```

## 🎯 Game Strategies

### For KB Agent
1. **Explore Safely**: Only move to cells determined safe by logic
2. **Use Percepts**: Analyze breeze/stench patterns to locate dangers
3. **Strategic Shooting**: Shoot arrows only when Wumpus location is certain
4. **Efficient Pathfinding**: Use shortest safe paths to objectives
5. **Return Home**: Plan route back to (0,0) after collecting gold

### Scoring System
- **+1000**: Successfully climb out with gold
- **+10**: Collect gold
- **-1**: Each move action
- **-1**: Each turn action  
- **-10**: Shoot arrow
- **-1000**: Death (pit or Wumpus)

## 🔧 Advanced Features

### Moving Wumpus Module
- **Dynamic Threats**: Wumpuses move every 5 actions
- **Adaptive Strategy**: Agent must update knowledge when creatures move
- **Increased Challenge**: Requires more sophisticated reasoning
- **Toggle**: Press 'M' during gameplay to enable/disable

### Lighting System
- **Fog of War**: Limited visibility creates atmospheric effect
- **Strategic Element**: Adds exploration challenge
- **Performance Impact**: Can be disabled for better performance
- **Toggle**: Press 'L' during gameplay or use `--no-light`

## 🎵 Audio System

### Sound Effects
- **🦹 Wumpus Scream**: Plays when Wumpus is killed by arrow

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
