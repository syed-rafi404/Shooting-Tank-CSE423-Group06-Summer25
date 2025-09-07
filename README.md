# 3D Tank Shooter Game 🎮

A sophisticated 3D tank combat game built with Python and OpenGL, featuring advanced AI, dual gameplay modes, and immersive 3D graphics.

## 🚀 Features

### Dual Combat Modes
- **Tank Mode**: Classic armored vehicle combat with turret control
- **Ultra Mode**: Transform into a melee robot with energy sword attacks

### Advanced AI System
- **Enemy AI**: Intelligent pathfinding, collision avoidance, and tactical shooting
- **Friendly AI**: Allied tanks that assist in combat against enemies
- **Dynamic Respawning**: Fallen enemies respawn after delay to maintain challenge

### Immersive 3D Graphics
- **Detailed Tank Models**: Fully 3D rendered chassis, treads, turrets, and weapons
- **Dynamic Camera System**: Multiple camera modes including first-person and orbital views
- **Environmental Design**: Bounded arena with realistic wall collision detection

### Combat Mechanics
- **Weapon Overheating**: Realistic firing rate limitations with cooldown periods
- **Health System**: Damage tracking with visual feedback
- **Scoring System**: Point-based rewards for tactical gameplay
- **Dominance Victory**: Control center area to achieve alternative win condition

## 🎯 Gameplay

### Objective
Survive waves of enemy tanks while maintaining control of the battlefield. Win by either:
- Achieving dominance by controlling the center circle for 15 seconds
- Maximizing your score through tactical combat

### Combat Modes
1. **Tank Mode**: Traditional vehicle combat with independent turret rotation
2. **Ultra Mode**: Close-quarters melee combat with energy sword projectiles

## 🕹️ Controls

### Movement (Tank Mode)
- `W` - Move backward / `S` - Move forward
- `A` / `D` - Rotate tank chassis
- `Q` / `E` - Rotate turret independently
- `Shift` + movement - Increased speed

### Movement (Ultra Mode)  
- `W` - Move forward
- `A` / `D` - Rotate

### Combat
- `Space` / `Left Click` - Fire weapon/attack
- `X` - Toggle between Tank and Ultra modes

### Camera
- `Arrow Keys` - Manual camera orbit
- `Right Click` - Toggle first-person view
- Auto-lock camera follows player movement

## 🛠️ Technical Implementation

### Core Technologies
- **Python 3.x** - Primary programming language
- **OpenGL** - 3D graphics rendering
- **PyOpenGL** - Python OpenGL bindings
- **GLUT** - Window management and input handling

### Advanced Features
- Real-time 3D collision detection
- Predictive AI targeting with ballistic calculations
- Dynamic lighting and 3D model rendering
- Optimized game loop with smooth 60 FPS performance

### Architecture Highlights
- Modular AI behavior system
- Efficient spatial collision detection
- Object-oriented game entity management
- Real-time physics simulation

## 📋 Requirements

```
Python 3.7+
PyOpenGL >= 3.1.0
PyOpenGL-accelerate >= 3.1.0 (recommended)
```

## 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/3d-tank-shooter.git
cd 3d-tank-shooter
```

2. **Install dependencies**
```bash
pip install PyOpenGL PyOpenGL-accelerate
```

3. **Run the game**
```bash
python tank_shooter.py
```

## 🎮 Game Mechanics

### Weapon System
- **Firing Rate Limiting**: Overheat protection prevents spam firing
- **Ballistic Physics**: Realistic projectile trajectories and collision
- **Burst Fire**: AI enemies use tactical burst firing patterns

### AI Behavior
- **Pathfinding**: Enemies navigate around obstacles and other units
- **Target Leading**: AI calculates player movement for accurate shots
- **Formation Behavior**: Units maintain strategic spacing
- **Adaptive Difficulty**: AI becomes more aggressive as game progresses

### Victory Conditions
- **Dominance Mode**: Control center area while preventing enemy occupation
- **Survival Mode**: Achieve high score through combat effectiveness
- **Health Management**: Avoid damage while maximizing offensive capability

## 🔧 Configuration

The game includes several configurable parameters:
- `GRID_LENGTH`: Arena size (default: 12000 units)
- `ENEMY_COUNT`: Number of enemy tanks (default: 5)
- `FRIENDLY_COUNT`: Number of allied tanks (default: 3)
- `OVERHEAT_THRESHOLD`: Maximum shots before cooldown (default: 20)
- `DOMINANCE_TIME_REQUIRED`: Seconds to hold center for victory (default: 15)

## 🤝 Contributing

This project welcomes contributions! Areas for enhancement:
- Additional weapon types and effects
- New AI behavior patterns
- Enhanced graphics and particle effects
- Multiplayer networking capabilities
- Level editor and custom arena designs

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 About

This project demonstrates advanced game development concepts including 3D graphics programming, AI systems, and real-time physics simulation. Built as part of ongoing exploration into computational graphics and interactive systems.

***

**Note**: This game requires OpenGL-compatible graphics hardware. For best performance, ensure your system has dedicated GPU support.
