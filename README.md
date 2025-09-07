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

