from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
from OpenGL.GLU import *
import random
import time
import math

fovY = 95
camera_pos = (0, 500, 500)
camera_mode_follow = False 
camera_orbit = 120
camera_height_offset = 0
AUTO_RELOCK_SEC = 1.5
last_free_orbit_time = 0.0
camera_distance = 10000
CAMERA_FOLLOW_DISTANCE = None
CAMERA_FOLLOW_HEIGHT = None
camera_lock_behind = True
camera_fp_mode = False

player_position = (0, 0, 0)
player_score = 0
player_health = 100
game_over = False
rotation_angle = 0
turret_angle = 0
player_overheated = False
player_shots_since_reset = 0
player_overheat_end_time = 0.0
player_hit_this_draw = False
ultra_mode = False
GRID_LENGTH = 12000
TANK_SCALE_MULTIPLIER = 4.0 * (GRID_LENGTH / 4000)
BORDER_WIDTH = 50
BOUNDARY_HEIGHT = 40
BOUNDARY_THICKNESS_MULTIPLIER = 3.0
BOUNDARY_HEIGHT_MULTIPLIER = 3.0

PLAYER_CHASSIS_COLOR = (0.2, 0.4, 0.2)

CAMERA_FOLLOW_DISTANCE = GRID_LENGTH * 0.35
CAMERA_FOLLOW_HEIGHT = GRID_LENGTH * 0.5

bullets = []
BULLET_SPEED = 100.0
MAX_BULLET_DISTANCE = GRID_LENGTH * 0.5
ENEMY_FIRE_COOLDOWN_MIN = 60   
ENEMY_FIRE_COOLDOWN_MAX = 180 
ENEMY_FIRE_CONE_DEG = 45
ENEMY_BULLET_SPEED = 86.0
AI_FIRE_INTERVAL_SEC = 1.2

ULTRA_SPLASH_SPEED = GRID_LENGTH * 0.045
ULTRA_SWORD_LENGTH_MULT = 80.0
ULTRA_SPLASH_WIDTH_MULT = 12.0
ULTRA_SPLASH_HEIGHT_MULT = 2.0
ultra_splash_projectiles = []

OVERHEAT_THRESHOLD = 20
SHOT_WINDOW_SEC = 6.0
shot_times = []

whole_tank_rotation_speed = 0
is_turret_rotating_left = False
is_turret_rotating_right = False
is_moving_forward = False
is_moving_backward = False
is_turret_realigning = False
TURRET_ROTATION_SPEED = 2
MOVEMENT_SPEED = 36
MOVEMENT_SPEED_MULTIPLIER = 1.0

HIT_RADIUS_MULT_PLAYER = 1.25
HIT_RADIUS_MULT_ENEMY = 1.15

DOMINANCE_RADIUS = GRID_LENGTH * 0.22
DOMINANCE_TIME_REQUIRED = 15.0
dominance_progress = 0.0
player_won = False
_last_idle_time = None

RESPAWN_DELAY_SEC = 2

enemy_tanks = []
friendly_tanks = []
MIN_DISTANCE_BETWEEN_TANKS = 200
EXTRA_SPAWN_GAP = 120
MAX_SPAWN_ATTEMPTS = 5000
ENEMY_MOVEMENT_SPEED = 21
ENEMY_TURN_SPEED = 2
ENEMY_BLOCKED_TURN_MIN = 60
ENEMY_BLOCKED_TURN_MAX = 180
ENEMY_DIRECTION_CHANGE_PROB = 0.002

FRIENDLY_MOVEMENT_SPEED = ENEMY_MOVEMENT_SPEED
FRIENDLY_BLOCKED_TURN_MIN = ENEMY_BLOCKED_TURN_MIN
FRIENDLY_BLOCKED_TURN_MAX = ENEMY_BLOCKED_TURN_MAX
FRIENDLY_DIRECTION_CHANGE_PROB = ENEMY_DIRECTION_CHANGE_PROB

def _deg_to_vector(angle_deg):
    rad = math.radians(angle_deg)
    return -math.sin(rad), math.cos(rad)

def is_enemy_move_blocked(nx, ny, radius, self_idx):
    wall_thickness = get_wall_thickness()
    limit = GRID_LENGTH - wall_thickness - radius
    if nx < -limit or nx > limit or ny < -limit or ny > limit:
        return True
    pr = tank_radius('player')
    dx = nx - player_position[0]
    dy = ny - player_position[1]
    if dx*dx + dy*dy < (radius + pr) ** 2:
        return True
    for i, e in enumerate(enemy_tanks):
        if e.get('dead'):
            continue
        if i == self_idx:
            continue
        ex, ey, _ = e['position']
        dx = nx - ex
        dy = ny - ey
        if dx*dx + dy*dy < (radius * 2) ** 2:  
            return True
    fr = tank_radius('friendly')
    for f in friendly_tanks:
        fx, fy, _ = f['position']
        dx = nx - fx
        dy = ny - fy
        if dx*dx + dy*dy < (radius + fr) ** 2:
            return True
    return False

def update_enemy_tanks():
    er = tank_radius('enemy')
    now = time.time()
    for i, en in enumerate(enemy_tanks):
        if en.get('dead') and now >= en.get('respawn_time', 0):
            respawn_enemy(i)
    for idx, e in enumerate(enemy_tanks):
        if e.get('dead'):
            continue
        now = time.time()
        if random.random() < ENEMY_DIRECTION_CHANGE_PROB:
            e['rotation'] += random.uniform(-45, 45)
        e['rotation'] %= 360
        vx, vy = _deg_to_vector(e['rotation'])
        ex, ey, ez = e['position']
        cand_x = ex - vx * ENEMY_MOVEMENT_SPEED  
        cand_y = ey - vy * ENEMY_MOVEMENT_SPEED
        if is_enemy_move_blocked(cand_x, cand_y, er, idx):
            e['rotation'] += random.uniform(ENEMY_BLOCKED_TURN_MIN, ENEMY_BLOCKED_TURN_MAX) * random.choice([-1, 1])
            e['rotation'] %= 360
        else:
            enemy_tanks[idx]['position'] = (cand_x, cand_y, ez)

        if 'next_fire_time' not in e:
            e['next_fire_time'] = now + random.uniform(0.0, AI_FIRE_INTERVAL_SEC)
        if not e.get('burst_in_progress', False) and now >= e['next_fire_time']:
            dxp = player_position[0] - ex
            dyp = player_position[1] - ey
            dist_sq = dxp*dxp + dyp*dyp
            if dist_sq > 1:
                inv_len = 1.0 / math.sqrt(dist_sq)
                pdx = dxp * inv_len
                pdy = dyp * inv_len
                fdx = -vx
                fdy = -vy
                dot = pdx * fdx + pdy * fdy
                if dot > 1:
                    dot = 1
                if dot < -1:
                    dot = -1
                angle_deg = math.degrees(math.acos(dot))
                if angle_deg <= ENEMY_FIRE_CONE_DEG:
                    pvx = 0.0
                    pvy = 0.0
                    if is_moving_forward or is_moving_backward:
                        pfx = -math.sin(math.radians(rotation_angle))
                        pfy =  math.cos(math.radians(rotation_angle))
                        sign = 1.0 if is_moving_forward else -1.0
                        pvx = pfx * MOVEMENT_SPEED * MOVEMENT_SPEED_MULTIPLIER * sign
                        pvy = pfy * MOVEMENT_SPEED * MOVEMENT_SPEED_MULTIPLIER * sign
                    tdx, tdy = _compute_lead_dir(ex, ey, player_position[0], player_position[1], pvx, pvy, ENEMY_BULLET_SPEED)
                    forward_offset = (110 - 45/2) * (1.2 * TANK_SCALE_MULTIPLIER)
                    spawn_x = ex + tdx * forward_offset
                    spawn_y = ey + tdy * forward_offset
                    spawn_z = 25 * (1.2 * TANK_SCALE_MULTIPLIER)
                    wall_thickness = get_wall_thickness()
                    limit = GRID_LENGTH - wall_thickness
                    remaining = limit - max(abs(spawn_x), abs(spawn_y))
                    bullets.append({
                        'position': [spawn_x, spawn_y, spawn_z],
                        'direction': (tdx, tdy),
                        'speed': ENEMY_BULLET_SPEED,
                        'owner': 'enemy',
                        'enemy_index': idx,
                        'total_path': remaining,
                        'traveled': 0.0,
                        'primary': True
                    })
                    e['burst_in_progress'] = True
                    e['burst_shots_fired'] = 1
                else:
                    e['next_fire_time'] = now + 0.2

def is_friendly_move_blocked(nx, ny, radius, self_idx):
    wall_thickness = get_wall_thickness()
    limit = GRID_LENGTH - wall_thickness - radius
    if nx < -limit or nx > limit or ny < -limit or ny > limit:
        return True
    pr = tank_radius('player')
    dx = nx - player_position[0]
    dy = ny - player_position[1]
    if dx*dx + dy*dy < (radius + pr) ** 2:
        return True
    er = tank_radius('enemy')
    for e in enemy_tanks:
        if e.get('dead'):
            continue
        ex, ey, _ = e['position']
        dx = nx - ex
        dy = ny - ey
        if dx*dx + dy*dy < (radius + er) ** 2:
            return True
    for i, f in enumerate(friendly_tanks):
        if i == self_idx:
            continue
        fx, fy, _ = f['position']
        dx = nx - fx
        dy = ny - fy
        if dx*dx + dy*dy < (radius * 2) ** 2:
            return True
    return False

def update_friendly_tanks():
    fr = tank_radius('friendly')
    for idx, f in enumerate(friendly_tanks):
        now = time.time()
        if random.random() < FRIENDLY_DIRECTION_CHANGE_PROB:
            f['rotation'] += random.uniform(-45, 45)
        f['rotation'] %= 360
        vx, vy = _deg_to_vector(f['rotation'])
        fx, fy, fz = f['position']
        cand_x = fx - vx * FRIENDLY_MOVEMENT_SPEED
        cand_y = fy - vy * FRIENDLY_MOVEMENT_SPEED
        if is_friendly_move_blocked(cand_x, cand_y, fr, idx):             
            f['rotation'] += random.uniform(FRIENDLY_BLOCKED_TURN_MIN, FRIENDLY_BLOCKED_TURN_MAX) * random.choice([-1, 1])
            f['rotation'] %= 360
        else:
            friendly_tanks[idx]['position'] = (cand_x, cand_y, fz)

        if 'next_fire_time' not in f:
            f['next_fire_time'] = now + random.uniform(0.0, AI_FIRE_INTERVAL_SEC)

        if not f.get('burst_in_progress', False) and enemy_tanks and now >= f['next_fire_time']:
            fdx = -vx
            fdy = -vy
            target_in_cone = False
            for e in enemy_tanks:
                if e.get('dead'):
                    continue
                ex, ey, _ = e['position']
                dx = ex - fx
                dy = ey - fy
                dist_sq = dx*dx + dy*dy
                if dist_sq <= 1:
                    continue
                inv_len = 1.0 / math.sqrt(dist_sq)
                tdx = dx * inv_len
                tdy = dy * inv_len
                dot = tdx * fdx + tdy * fdy
                if dot > 1:
                    dot = 1
                if dot < -1:
                    dot = -1
                angle_deg = math.degrees(math.acos(dot))
                if angle_deg <= ENEMY_FIRE_CONE_DEG:
                    target_in_cone = True
                    break
            if target_in_cone:
                best = None
                best_d2 = 1e18
                for e in enemy_tanks:
                    if e.get('dead'):
                        continue
                    ex, ey, _ = e['position']
                    dx = ex - fx
                    dy = ey - fy
                    d2 = dx*dx + dy*dy
                    if d2 < best_d2 and d2 > 1:
                        invl = 1.0 / math.sqrt(d2)
                        tdx = dx * invl
                        tdy = dy * invl
                        dot = tdx * fdx + tdy * fdy
                        dot = max(-1.0, min(1.0, dot))
                        angdeg = math.degrees(math.acos(dot))
                        if angdeg <= ENEMY_FIRE_CONE_DEG:
                            evx = -math.sin(math.radians(e.get('rotation', 0))) * ENEMY_MOVEMENT_SPEED
                            evy =  math.cos(math.radians(e.get('rotation', 0))) * ENEMY_MOVEMENT_SPEED
                            ldx, ldy = _compute_lead_dir(fx, fy, ex, ey, evx, evy, ENEMY_BULLET_SPEED)
                            best = (ldx, ldy)
                            best_d2 = d2
                adx, ady = best if best else (fdx, fdy)
                forward_offset = (110 - 45/2) * (1.2 * TANK_SCALE_MULTIPLIER)
                spawn_x = fx + adx * forward_offset
                spawn_y = fy + ady * forward_offset
                spawn_z = 25 * (1.2 * TANK_SCALE_MULTIPLIER)
                wall_thickness = get_wall_thickness()
                limit = GRID_LENGTH - wall_thickness
                remaining = limit - max(abs(spawn_x), abs(spawn_y))
                bullets.append({
                    'position': [spawn_x, spawn_y, spawn_z],
                    'direction': (adx, ady),
                    'speed': ENEMY_BULLET_SPEED,
                    'owner': 'friendly',
                    'friendly_index': idx,
                    'total_path': remaining,
                    'traveled': 0.0,
                    'primary': True
                })
                f['burst_in_progress'] = True
                f['burst_shots_fired'] = 1
            else:
                f['next_fire_time'] = now + 0.2

def get_wall_thickness():
    return BORDER_WIDTH * BOUNDARY_THICKNESS_MULTIPLIER

def tank_base_scale(tank_type):
    base_scale = TANK_SCALE_MULTIPLIER
    if tank_type == 'enemy':
        return 1.2 * base_scale
    if tank_type == 'friendly':
        return 1.2 * base_scale
    return 1.5 * base_scale

def tank_radius(tank_type='player'):
    s = tank_base_scale(tank_type)
    half_w = 50.0 * s
    half_l = 50.0 * s
    return (half_w**2 + half_l**2) ** 0.5

def will_collide_player(nx, ny, pr):
    pr_sq = pr * pr
    for e in enemy_tanks:
        if e.get('dead'):
            continue
        ex, ey, _ = e['position']
        er = tank_radius('enemy')
        dx = nx - ex
        dy = ny - ey
        limit = pr + er
        if dx*dx + dy*dy < limit * limit:
            return True
    for f in friendly_tanks:
        fx, fy, _ = f['position']
        fr = tank_radius('friendly')
        dx = nx - fx
        dy = ny - fy
        limit = pr + fr
        if dx*dx + dy*dy < limit * limit:
            return True
    return False

def clamp_position(x, y, radius):
    wall_thickness = get_wall_thickness()
    limit = GRID_LENGTH - wall_thickness - radius
    if limit < 0:
        limit = 0
    x = max(-limit, min(x, limit))
    y = max(-limit, min(y, limit))
    return x, y

def can_place_candidate(x, y, radius, existing_lists):
    pr = tank_radius('player')
    dxp = x - player_position[0]
    dyp = y - player_position[1]
    required_player = radius + pr + EXTRA_SPAWN_GAP
    if dxp*dxp + dyp*dyp < required_player * required_player:
        return False
    for tank_list, t_type in existing_lists:
        for t in tank_list:
            tx, ty, _ = t['position']
            other_r = tank_radius(t_type)
            dx = x - tx
            dy = y - ty
            required = radius + other_r + EXTRA_SPAWN_GAP
            if dx*dx + dy*dy < required * required:
                return False
    return True

def initialize_units():
    global player_position
    player_position = (0,0,0)
    wall_thickness = get_wall_thickness()
    enemy_r = tank_radius('enemy')
    friendly_r = tank_radius('friendly')
    max_r = max(enemy_r, friendly_r)
    playable_area = GRID_LENGTH - wall_thickness - max_r - EXTRA_SPAWN_GAP
    enemy_tanks.clear()
    friendly_tanks.clear()

    desired_enemies = 5
    attempts = 0
    while len(enemy_tanks) < desired_enemies and attempts < MAX_SPAWN_ATTEMPTS:
        attempts += 1
        x = random.uniform(-playable_area, playable_area)
        y = random.uniform(-playable_area, playable_area)
        if can_place_candidate(x, y, enemy_r, [ (enemy_tanks, 'enemy'), (friendly_tanks, 'friendly') ]):
            cx, cy = clamp_position(x, y, enemy_r)
            enemy_tanks.append({'position': (cx, cy, 0), 'rotation': random.uniform(0,360), 'next_fire_time': time.time() + random.uniform(0.0, AI_FIRE_INTERVAL_SEC), 'burst_shots_fired':0, 'burst_in_progress': False})

    desired_friendlies = 3
    attempts = 0
    while len(friendly_tanks) < desired_friendlies and attempts < MAX_SPAWN_ATTEMPTS:
        attempts += 1
        x = random.uniform(-playable_area, playable_area)
        y = random.uniform(-playable_area, playable_area)
        if can_place_candidate(x, y, friendly_r, [ (enemy_tanks, 'enemy'), (friendly_tanks, 'friendly') ]):
            cx, cy = clamp_position(x, y, friendly_r)
            friendly_tanks.append({'position': (cx, cy, 0), 'rotation': random.uniform(0,360), 'next_fire_time': time.time() + random.uniform(0.0, AI_FIRE_INTERVAL_SEC), 'burst_shots_fired': 0, 'burst_in_progress': False})


def draw_tank(position, chassis_angle, turret_angle, tank_type='player'):
    glPushMatrix()
    glTranslatef(*position)
    glRotatef(chassis_angle, 0, 0, 1)

    base_scale = TANK_SCALE_MULTIPLIER
    if tank_type == 'enemy':
        scale_factor = 1.2 * base_scale
        CHASSIS_COLOR = (0.8, 0.1, 0.1)
        TREAD_COLOR = (0.3, 0.0, 0.0)
    elif tank_type == 'friendly':
        scale_factor = 1.2 * base_scale
        CHASSIS_COLOR = (0.1, 0.1, 0.8)
        TREAD_COLOR = (0.0, 0.0, 0.3)
    else:
        scale_factor = 1.5 * base_scale
        CHASSIS_COLOR = (0.2, 0.4, 0.2)
        TREAD_COLOR = (0.2, 0.2, 0.2)
    
    global player_overheated
    if tank_type == 'player' and player_overheated:
        GUN_COLOR = (0.8, 0.0, 0.0)
        TURRET_BOX_COLOR = (CHASSIS_COLOR[0]*0.7, CHASSIS_COLOR[1]*0.7, CHASSIS_COLOR[2]*0.7)
    else:
        GUN_COLOR = (0.25, 0.25, 0.25)
        TURRET_BOX_COLOR = (CHASSIS_COLOR[0]*0.7, CHASSIS_COLOR[1]*0.7, CHASSIS_COLOR[2]*0.7)

    glColor3f(*CHASSIS_COLOR)
    glPushMatrix()
    glScalef(60 * scale_factor, 90 * scale_factor, 25 * scale_factor)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(*TREAD_COLOR)
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side * 40 * scale_factor, 0, 0)
        glScalef(20 * scale_factor, 100 * scale_factor, 30 * scale_factor)
        glutSolidCube(1)
        glPopMatrix()
    
    glColor3f(TREAD_COLOR[0]*0.5, TREAD_COLOR[1]*0.5, TREAD_COLOR[2]*0.5)
    wheel_radius = 12 * scale_factor
    wheel_height = 22 * scale_factor
    quad = gluNewQuadric()
    
    for i in range(-2, 2):
        for side_mult in [-1, 1]:
            glPushMatrix()
            glTranslatef(side_mult * 40 * scale_factor, i * 25 * scale_factor, -5 * scale_factor)
            glRotatef(90 * side_mult, 0, 1, 0)
            gluCylinder(quad, wheel_radius, wheel_radius, wheel_height, 10, 1)
            glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 25 * scale_factor)
    glRotatef(turret_angle, 0, 0, 1)
    
    glColor3f(*TURRET_BOX_COLOR)
    glPushMatrix()
    glScalef(45 * scale_factor, 45 * scale_factor, 20 * scale_factor)
    glutSolidCube(1)
    glPopMatrix()
    
    glColor3f(*GUN_COLOR)
    glPushMatrix()
    glTranslatef(0, (45 * scale_factor) / 2, 0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 5 * scale_factor, 5 * scale_factor, 110 * scale_factor, 15, 5)
    glPopMatrix()
    
    glPopMatrix()
    glPopMatrix()

def draw_robot(position, chassis_angle):
    s = 1.2 * TANK_SCALE_MULTIPLIER  
    glPushMatrix()
    glTranslatef(*position)
    glRotatef(chassis_angle, 0, 0, 1)

    pr, pg, pb = PLAYER_CHASSIS_COLOR
    BODY = (min(pr * 1.10, 1.0), min(pg * 1.10, 1.0), min(pb * 1.10, 1.0))  
    ACCENT = (max(pr * 0.70, 0.0), max(pg * 0.70, 0.0), max(pb * 0.70, 0.0)) 
    DARK = (max(pr * 0.50, 0.0), max(pg * 0.50, 0.0), max(pb * 0.50, 0.0))   
    BLADE = (0.85, 0.85, 0.9)

    glColor3f(*DARK)
    glPushMatrix()
    glTranslatef(0, 0, 25*s)
    glScalef(45*s, 25*s, 20*s)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(*BODY)
    glPushMatrix()
    glTranslatef(0, 0, 70*s)
    glScalef(60*s, 30*s, 70*s)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 110*s)

    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glScalef(36*s, 26*s, 24*s)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.08, 0.08, 0.08)
    glPushMatrix()
    glTranslatef(0, 14*s, 0)
    glScalef(28*s, 2*s, 16*s)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.2, 0.8, 1.0)
    glPushMatrix()
    glTranslatef(0, 15*s, 2*s)
    glScalef(18*s, 1*s, 3*s)
    glutSolidCube(1)
    glPopMatrix()

    y_eye = 15.55*s  
    z_eye = 2*s
    glColor3f(0.6, 0.95, 1.0)
    half_w_core = 1.6*s
    half_h_core = 0.8*s
    cx = -6.0*s
    glBegin(GL_QUADS)
    glVertex3f(cx - half_w_core, y_eye, z_eye - half_h_core)
    glVertex3f(cx + half_w_core, y_eye, z_eye - half_h_core)
    glVertex3f(cx + half_w_core, y_eye, z_eye + half_h_core)
    glVertex3f(cx - half_w_core, y_eye, z_eye + half_h_core)
    glEnd()
    cx = 6.0*s
    glBegin(GL_QUADS)
    glVertex3f(cx - half_w_core, y_eye, z_eye - half_h_core)
    glVertex3f(cx + half_w_core, y_eye, z_eye - half_h_core)
    glVertex3f(cx + half_w_core, y_eye, z_eye + half_h_core)
    glVertex3f(cx - half_w_core, y_eye, z_eye + half_h_core)
    glEnd()

    glColor3f(0.08, 0.08, 0.08)
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side*20*s, 0, 0)
        glScalef(4*s, 18*s, 14*s)
        glutSolidCube(1)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 10*s, -14*s)
    glScalef(18*s, 4*s, 6*s)
    glutSolidCube(1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 16*s)
    glScalef(10*s, 16*s, 4*s)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

    glColor3f(*DARK)
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side*18*s, 0, 10*s)
        glScalef(20*s, 20*s, 40*s)
        glutSolidCube(1)
        glPopMatrix()

    glColor3f(*DARK)
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side*45*s, 0, 85*s)
        glScalef(20*s, 20*s, 20*s)
        glutSolidCube(1)
        glPopMatrix()

    grip_z = 90*s
    grip_y = 40*s
    fore_len = 35*s
    glColor3f(*DARK)
    for side in (-1, 1):
        glPushMatrix()
        glTranslatef(side*25*s, 15*s, grip_z)
        glRotatef(-15*side, 0, 0, 1)
        glRotatef(-20, 1, 0, 0)
        glTranslatef(0, grip_y/2, 0)
        glScalef(14*s, fore_len, 14*s)
        glutSolidCube(1)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(25*s, 15*s, grip_z)
    glRotatef(-15, 0, 0, 1)
    glRotatef(-20, 1, 0, 0)

    glColor3f(0.25, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, grip_y+15*s, 0)
    glScalef(10*s, 30*s, 10*s)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.6, 0.55, 0.4)
    glPushMatrix()
    glTranslatef(0, grip_y+30*s, 0)
    glScalef(40*s, 4*s, 8*s)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(*BLADE)
    glPushMatrix()
    glTranslatef(0, grip_y+55*s, 0)
    glScalef(8*s, 80*s, 4*s)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.95, 0.95, 1.0)
    t = 0.4 * s  
    y0 = grip_y + 30*s
    y1 = grip_y + 110*s
    zf = 2*s
    glBegin(GL_QUADS)
    glVertex3f(-t, y0, zf)
    glVertex3f( t, y0, zf)
    glVertex3f( t, y1, zf)
    glVertex3f(-t, y1, zf)
    zb = -2*s
    glVertex3f(-t, y0, zb)
    glVertex3f( t, y0, zb)
    glVertex3f( t, y1, zb)
    glVertex3f(-t, y1, zb)
    glEnd()
    glPopMatrix()

    glPopMatrix()

def draw_boundary():
    INNER_GRID_LENGTH = GRID_LENGTH - BORDER_WIDTH
    glColor3f(139/255, 69/255, 19/255)
    wall_height = BOUNDARY_HEIGHT * BOUNDARY_HEIGHT_MULTIPLIER * (GRID_LENGTH / 4000)
    wall_thickness = BORDER_WIDTH * BOUNDARY_THICKNESS_MULTIPLIER
    for i in [-1, 1]:
        glPushMatrix()
        glTranslatef(0, i * (GRID_LENGTH - wall_thickness/2), wall_height / 2)
        glScalef(GRID_LENGTH * 2, wall_thickness, wall_height)
        glutSolidCube(1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(i * (GRID_LENGTH - wall_thickness/2), 0, wall_height / 2)
        glScalef(wall_thickness, (GRID_LENGTH - wall_thickness) * 2, wall_height)
        glutSolidCube(1)
        glPopMatrix()

def setupCamera():
    R = GRID_LENGTH
    target_fov = fovY
    wall_height = BOUNDARY_HEIGHT * BOUNDARY_HEIGHT_MULTIPLIER * (R / 4000)
    min_height = max(wall_height * 1.2, R * 0.06)
    cam_height = max(CAMERA_FOLLOW_HEIGHT + camera_height_offset, min_height)

    px, py, pz = player_position
    if camera_fp_mode:
        if ultra_mode:
            s = 1.2 * TANK_SCALE_MULTIPLIER
            fx = -math.sin(math.radians(rotation_angle))
            fy =  math.cos(math.radians(rotation_angle))
            head_front = 14.0 * s
            eps = 2.0 * s
            eye_x = px + fx * (head_front + eps)
            eye_y = py + fy * (head_front + eps)
            eye_z = pz + (110.0 * s)
            look_x = eye_x + fx * (R * 0.05)
            look_y = eye_y + fy * (R * 0.05)
            look_z = eye_z
        else:
            s = 1.5 * TANK_SCALE_MULTIPLIER
            final_angle = (rotation_angle + turret_angle) % 360
            rad = math.radians(final_angle)
            fx = math.sin(rad)
            fy = -math.cos(rad)
            half_len = (45.0 * s) * 0.5
            back = 6.0 * s
            eye_x = px + fx * (half_len - back)
            eye_y = py + fy * (half_len - back)
            eye_z = pz + (35.0 * s) + (4.0 * s)
            look_x = eye_x + fx * (R * 0.05)
            look_y = eye_y + fy * (R * 0.05)
            look_z = eye_z

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        far_clip = max(15000, R * 6)
        gluPerspective(target_fov, 1.25, 5.0, far_clip)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(eye_x, eye_y, eye_z, look_x, look_y, look_z, 0, 0, 1)
        return
    effective_lock = camera_lock_behind or (ultra_mode and whole_tank_rotation_speed != 0)
    if effective_lock:
        if ultra_mode:
            fx = -math.sin(math.radians(rotation_angle))
            fy =  math.cos(math.radians(rotation_angle))
        else:
            fx =  math.sin(math.radians(rotation_angle))
            fy = -math.cos(math.radians(rotation_angle))
        cam_x = px - fx * CAMERA_FOLLOW_DISTANCE
        cam_y = py - fy * CAMERA_FOLLOW_DISTANCE
        cam_z = cam_height
        look_x = px + fx * (R * 0.05)
        look_y = py + fy * (R * 0.05)
        look_z = pz
    else:
        ang = math.radians(camera_orbit)
        cam_x = px + math.cos(ang) * CAMERA_FOLLOW_DISTANCE
        cam_y = py + math.sin(ang) * CAMERA_FOLLOW_DISTANCE
        cam_z = cam_height
        look_x = px
        look_y = py
        look_z = pz

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    far_clip = max(15000, R * 6)
    gluPerspective(target_fov, 1.25, 5.0, far_clip)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 0, 1)

def _get_forward_vec(deg):
    r = math.radians(deg)
    return math.sin(r), -math.cos(r)

def _grid_edge_intersection(px, py, dirx, diry, half):
    t_vals = []
    eps = 1e-6
    if abs(dirx) > eps:
        t = (half - px) / dirx
        if t > 0:
            y = py + t * diry
            if -half <= y <= half:
                t_vals.append((t, (half, y)))
        t = (-half - px) / dirx
        if t > 0:
            y = py + t * diry
            if -half <= y <= half:
                t_vals.append((t, (-half, y)))
    if abs(diry) > eps:
        t = (half - py) / diry
        if t > 0:
            x = px + t * dirx
            if -half <= x <= half:
                t_vals.append((t, (x, half)))
        t = (-half - py) / diry
        if t > 0:
            x = px + t * dirx
            if -half <= x <= half:
                t_vals.append((t, (x, -half)))
    if not t_vals:
        return px, py  
    t_vals.sort(key=lambda a: a[0])
    return t_vals[0][1]

def _line_point_distance_sq(ax, ay, bx, by, px, py):
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    ab_len_sq = abx*abx + aby*aby
    if ab_len_sq <= 1e-9:
        return apx*apx + apy*apy
    t = (apx*abx + apy*aby) / ab_len_sq
    if t < 0:
        t = 0
    elif t > 1:
        t = 1
    cx = ax + t * abx
    cy = ay + t * aby
    dx = px - cx
    dy = py - cy
    return dx*dx + dy*dy

def _compute_lead_dir(sx, sy, tx, ty, tvx, tvy, ps):
    rx = tx - sx
    ry = ty - sy
    a = (tvx*tvx + tvy*tvy) - (ps*ps)
    b = 2.0 * (rx*tvx + ry*tvy)
    c = rx*rx + ry*ry
    t = None
    eps = 1e-6
    if abs(a) < eps:
        if abs(b) > eps:
            t_lin = -c / b
            if t_lin > 0:
                t = t_lin
    else:
        disc = b*b - 4*a*c
        if disc >= 0:
            sqrt_d = math.sqrt(disc)
            t1 = (-b - sqrt_d) / (2*a)
            t2 = (-b + sqrt_d) / (2*a)
            candidates = [tt for tt in (t1, t2) if tt > 0]
            if candidates:
                t = min(candidates)
    dirx = rx + (tvx * t) if t is not None else rx
    diry = ry + (tvy * t) if t is not None else ry
    norm = math.hypot(dirx, diry)
    if norm < eps:
        norm = math.hypot(rx, ry) or 1.0
        dirx, diry = rx / norm, ry / norm
    else:
        dirx /= norm
        diry /= norm
    return dirx, diry

def perform_ultra_splash():
    global ultra_splash_projectiles
    if not ultra_mode:
        return
    s = 1.2 * TANK_SCALE_MULTIPLIER
    fx, fy = _get_forward_vec(rotation_angle)
    origin_x = player_position[0] + fx * (40*s + 55*s)
    origin_y = player_position[1] + fy * (40*s + 55*s)
    origin_z = 75 * s
    proj = {
        'pos': (origin_x, origin_y, origin_z),
        'dir': (-fx, -fy),
        'length': ULTRA_SWORD_LENGTH_MULT * s,
        'width': ULTRA_SPLASH_WIDTH_MULT * s,
        'height': ULTRA_SPLASH_HEIGHT_MULT * s,
    'speed': ULTRA_SPLASH_SPEED
    }
    ultra_splash_projectiles.append(proj)

def keyboardListener(key, x, y):

    global camera_orbit, camera_height_offset
    global is_turret_rotating_left, is_turret_rotating_right, is_turret_realigning
    global whole_tank_rotation_speed, is_moving_forward, is_moving_backward, MOVEMENT_SPEED_MULTIPLIER
    global game_over, player_health, player_score, bullets
    global ultra_mode, camera_lock_behind
    global dominance_progress, player_won, _last_idle_time

    if key == b'a':
        mult = 2 if (glutGetModifiers() & GLUT_ACTIVE_SHIFT) else 1
        whole_tank_rotation_speed = -2 * mult
        is_turret_realigning = True
    elif key == b'd':
        mult = 2 if (glutGetModifiers() & GLUT_ACTIVE_SHIFT) else 1
        whole_tank_rotation_speed = 2 * mult
        is_turret_realigning = True
    elif key == b'w':
        if ultra_mode:
            is_moving_forward = True
            is_moving_backward = False
        else:
            is_moving_backward = True
            is_moving_forward = False
        MOVEMENT_SPEED_MULTIPLIER = 2.0 if (glutGetModifiers() & GLUT_ACTIVE_SHIFT) else 1.0
        is_turret_realigning = True
        camera_lock_behind = True
    elif key == b's':
        if ultra_mode:
            return
        else:
            is_moving_forward = True
            is_moving_backward = False
            MOVEMENT_SPEED_MULTIPLIER = 2.0 if (glutGetModifiers() & GLUT_ACTIVE_SHIFT) else 1.0
            is_turret_realigning = True
            camera_lock_behind = True
    elif key == b'q':
        is_turret_rotating_left = True
        is_turret_realigning = False
    elif key == b'e':
        is_turret_rotating_right = True
        is_turret_realigning = False
    elif key == b'x':
        px, py, _ = player_position
        if not ultra_mode:
            if (px*px + py*py) <= (DOMINANCE_RADIUS * DOMINANCE_RADIUS):
                return
        ultra_mode = not ultra_mode
        is_turret_rotating_left = False
        is_turret_rotating_right = False
        is_turret_realigning = False
        whole_tank_rotation_speed = 0
        is_moving_forward = False
        is_moving_backward = False
        MOVEMENT_SPEED_MULTIPLIER = 1.0
        return
    elif key == b'r' and (game_over or player_won):
        player_health = 100
        player_score = 0
        bullets = []
        global player_overheated, player_shots_since_reset, player_overheat_end_time
        player_overheated = False
        player_shots_since_reset = 0
        player_overheat_end_time = 0.0
        shot_times.clear()
        initialize_units()
        game_over = False
        dominance_progress = 0.0
        player_won = False
        _last_idle_time = time.time()
        return
    elif key == b' ':
        if ultra_mode:
            perform_ultra_splash()
        else:
            fire_player()

def keyboardUpListener(key, x, y):
    global is_turret_rotating_left, is_turret_rotating_right
    global whole_tank_rotation_speed, is_moving_forward, is_moving_backward, MOVEMENT_SPEED_MULTIPLIER

    if key == b'a' or key == b'd':
        whole_tank_rotation_speed = 0
    if key == b'w':
        if ultra_mode:
            is_moving_forward = False
        else:
            is_moving_backward = False
        MOVEMENT_SPEED_MULTIPLIER = 1.0
    if key == b's':
        if ultra_mode:
            pass
        else:
            is_moving_forward = False
            MOVEMENT_SPEED_MULTIPLIER = 1.0
    if key == b'q':
        is_turret_rotating_left = False
    if key == b'e':
        is_turret_rotating_right = False

def specialKeyListener(key, x, y):
    global camera_orbit, camera_height_offset, camera_lock_behind, last_free_orbit_time

    if key == GLUT_KEY_LEFT:
        camera_orbit -= 5
        camera_orbit %= 360
        camera_lock_behind = False
        last_free_orbit_time = time.time()
    elif key == GLUT_KEY_RIGHT:
        camera_orbit += 5
        camera_orbit %= 360
        camera_lock_behind = False
        last_free_orbit_time = time.time()

    if key == GLUT_KEY_UP:
        camera_height_offset += 50
    elif key == GLUT_KEY_DOWN:
        camera_height_offset -= 50


def idle():
    global rotation_angle, turret_angle, player_position, is_turret_realigning, bullets, player_health, game_over
    global player_overheated, player_overheat_end_time, player_shots_since_reset
    global player_hit_this_draw
    global ultra_splash_projectiles, player_score
    global is_moving_backward, is_moving_forward, ultra_mode
    global dominance_progress, player_won, _last_idle_time
    global camera_lock_behind, last_free_orbit_time
    if game_over or player_won:
        glutPostRedisplay()
        return
    if not camera_lock_behind:
        if (time.time() - last_free_orbit_time) >= AUTO_RELOCK_SEC:
            camera_lock_behind = True
    if player_overheated and time.time() >= player_overheat_end_time:
        player_overheated = False
        player_shots_since_reset = 0
        shot_times.clear()
    rotation_angle += whole_tank_rotation_speed
    rotation_angle %= 360
    
    if is_turret_rotating_left:
        turret_angle -= TURRET_ROTATION_SPEED
    elif is_turret_rotating_right:
        turret_angle += TURRET_ROTATION_SPEED
    elif is_turret_realigning:
        if abs(turret_angle) > TURRET_ROTATION_SPEED:
            turret_angle -= math.copysign(TURRET_ROTATION_SPEED, turret_angle)
        else:
            turret_angle = 0
            is_turret_realigning = False
            
    turret_angle %= 360
    
    if ultra_mode and is_moving_backward:
        is_moving_backward = False
    if is_moving_forward or is_moving_backward:
        fx = -math.sin(math.radians(rotation_angle))
        fy =  math.cos(math.radians(rotation_angle))
        x, y, z = player_position
        step = (MOVEMENT_SPEED * MOVEMENT_SPEED_MULTIPLIER) * (1 if is_moving_forward else -1)
        cand_x = x + fx * step
        cand_y = y + fy * step
        pr = tank_radius('player')
        cand_x, cand_y = clamp_position(cand_x, cand_y, pr)
        if not will_collide_player(cand_x, cand_y, pr):
            player_position = (cand_x, cand_y, z)

    update_enemy_tanks()
    update_friendly_tanks()

    er = tank_radius('enemy')
    fr = tank_radius('friendly')
    for e in enemy_tanks:
        if e.get('dead'):
            continue
        ex, ey, ez = e['position']
        ex, ey = clamp_position(ex, ey, er)
        e['position'] = (ex, ey, ez)
    for f in friendly_tanks:
        fx, fy, fz = f['position']
        fx, fy = clamp_position(fx, fy, fr)
        f['position'] = (fx, fy, fz)

    if bullets:
        updated = []
        wall_thickness = get_wall_thickness()
        impact_limit = GRID_LENGTH - wall_thickness
        player_r = tank_radius('player') * HIT_RADIUS_MULT_PLAYER
        pr_sq = player_r * player_r
        enemy_r = tank_radius('enemy') * HIT_RADIUS_MULT_ENEMY
        enemy_r_sq = enemy_r * enemy_r
        friendly_r = tank_radius('friendly')
        friendly_r_sq = friendly_r * friendly_r
        for b in bullets:
            b['position'][0] += b['direction'][0] * b['speed']
            b['position'][1] += b['direction'][1] * b['speed']
            if b.get('owner') == 'enemy':
                if 'total_path' in b:
                    b['traveled'] += b['speed']
                if b.get('primary') and 'total_path' in b:
                    if b['traveled'] >= (b['total_path'] / 3.0):
                        ei = b.get('enemy_index')
                        if ei is not None and 0 <= ei < len(enemy_tanks):
                            e = enemy_tanks[ei]
                            if e.get('burst_in_progress') and e.get('burst_shots_fired',0) == 1:
                                for _ in range(2):
                                    spawn_x2 = b['position'][0]
                                    spawn_y2 = b['position'][1]
                                    spawn_z2 = b['position'][2]
                                    bullets.append({'position': [spawn_x2, spawn_y2, spawn_z2], 'direction': b['direction'], 'speed': ENEMY_BULLET_SPEED, 'owner': 'enemy', 'enemy_index': ei, 'secondary': True})
                                e['burst_shots_fired'] = 3
            elif b.get('owner') == 'friendly':
                if 'total_path' in b:
                    b['traveled'] += b['speed']
                if b.get('primary') and 'total_path' in b:
                    if b['traveled'] >= (b['total_path'] / 3.0):
                        fi = b.get('friendly_index')
                        if fi is not None and 0 <= fi < len(friendly_tanks):
                            f = friendly_tanks[fi]
                            if f.get('burst_in_progress') and f.get('burst_shots_fired',0) == 1:
                                for _ in range(2):
                                    spawn_x2 = b['position'][0]
                                    spawn_y2 = b['position'][1]
                                    spawn_z2 = b['position'][2]
                                    bullets.append({'position': [spawn_x2, spawn_y2, spawn_z2], 'direction': b['direction'], 'speed': ENEMY_BULLET_SPEED, 'owner': 'friendly', 'friendly_index': fi, 'secondary': True})
                                f['burst_shots_fired'] = 3
            else:
                bx = b['position'][0]
                by = b['position'][1]
                hit_friendly_index = None
                for fi, f in enumerate(friendly_tanks):
                    fx, fy, _ = f['position']
                    dx = bx - fx
                    dy = by - fy
                    if dx*dx + dy*dy <= friendly_r_sq:
                        hit_friendly_index = fi
                        break
                if hit_friendly_index is not None:
                    convert_friendly_to_enemy(hit_friendly_index)
                    continue
                hit_enemy_index = None
                for ei, e in enumerate(enemy_tanks):
                    if e.get('dead'):
                        continue
                    ex, ey, _ = e['position']
                    dx = bx - ex
                    dy = by - ey
                    if dx*dx + dy*dy <= enemy_r_sq:
                        hit_enemy_index = ei
                        break
                if hit_enemy_index is not None:
                    global player_score
                    player_score += 2
                    enemy_tanks[hit_enemy_index]['dead'] = True
                    enemy_tanks[hit_enemy_index]['respawn_time'] = time.time() + RESPAWN_DELAY_SEC
                    continue
            x = b['position'][0]
            y = b['position'][1]
            if b.get('owner') == 'enemy':
                dxp = x - player_position[0]
                dyp = y - player_position[1]
                if dxp*dxp + dyp*dyp <= pr_sq:
                    if not player_hit_this_draw:
                        player_health = max(0, player_health - 0.5)
                        if player_health == 0:
                            game_over = True
                        player_hit_this_draw = True
                    continue
            elif b.get('owner') == 'friendly':
                bx = b['position'][0]
                by = b['position'][1]
                hit_enemy_index = None
                for ei, e in enumerate(enemy_tanks):
                    if e.get('dead'):
                        continue
                    ex, ey, _ = e['position']
                    dx = bx - ex
                    dy = by - ey
                    if dx*dx + dy*dy <= enemy_r_sq:
                        hit_enemy_index = ei
                        break
                if hit_enemy_index is not None:
                    enemy_tanks[hit_enemy_index]['dead'] = True
                    enemy_tanks[hit_enemy_index]['respawn_time'] = time.time() + RESPAWN_DELAY_SEC
                    continue
            if abs(x) >= impact_limit or abs(y) >= impact_limit:
                if b.get('owner') == 'enemy':
                    ei = b.get('enemy_index')
                    if ei is not None and 0 <= ei < len(enemy_tanks):
                        pass
                continue
            updated.append(b)
        bullets = updated

        for idx, e in enumerate(enemy_tanks):
            if e.get('burst_in_progress'):
                remaining = 0
                for b in bullets:
                    if b.get('owner') == 'enemy' and b.get('enemy_index') == idx:
                        remaining += 1
                if remaining == 0:
                    e['burst_in_progress'] = False
                    e['active_bullet'] = False
                    e['burst_shots_fired'] = 0
                    e['next_fire_time'] = time.time() + AI_FIRE_INTERVAL_SEC

        for idx, f in enumerate(friendly_tanks):
            if f.get('burst_in_progress'):
                remaining = 0
                for b in bullets:
                    if b.get('owner') == 'friendly' and b.get('friendly_index') == idx:
                        remaining += 1
                if remaining == 0:
                    f['burst_in_progress'] = False
                    f['burst_shots_fired'] = 0
                    f['next_fire_time'] = time.time() + AI_FIRE_INTERVAL_SEC

    if ultra_splash_projectiles:
        wall_thickness = get_wall_thickness()
        half = GRID_LENGTH - wall_thickness
        enemy_r = tank_radius('enemy')
        enemy_r_sq = enemy_r * enemy_r
        kept_proj = []
        for p in ultra_splash_projectiles:
            x, y, z = p['pos']
            dx, dy = p['dir']
            v = p['speed']
            nx = x + dx * v
            ny = y + dy * v
            if abs(nx) >= half or abs(ny) >= half:
                continue
            Lh = p['length'] * 0.5
            Wh = p['width'] * 0.5
            pxn = -dy
            pyn = dx
            den = math.hypot(pxn, pyn) or 1.0
            pxn /= den
            pyn /= den
            ax = nx - pxn * Lh
            ay = ny - pyn * Lh
            bx = nx + pxn * Lh
            by = ny + pyn * Lh
            destroyed = None
            for ei, e in enumerate(enemy_tanks):
                if e.get('dead'):
                    continue
                ex, ey, _ = e['position']
                if _line_point_distance_sq(ax, ay, bx, by, ex, ey) <= (Wh + enemy_r) ** 2:
                    destroyed = ei
                    break
            if destroyed is not None:
                player_score += 2
                enemy_tanks[destroyed]['dead'] = True
                enemy_tanks[destroyed]['respawn_time'] = time.time() + RESPAWN_DELAY_SEC
            p['pos'] = (nx, ny, z)
            kept_proj.append(p)
        ultra_splash_projectiles = kept_proj

    glutPostRedisplay()

    now = time.time()
    if _last_idle_time is None:
        _last_idle_time = now
    dt = now - _last_idle_time
    _last_idle_time = now

    px, py, _ = player_position
    inside = (px*px + py*py) <= (DOMINANCE_RADIUS * DOMINANCE_RADIUS)
    no_enemy_inside = True
    if inside:
        r2 = DOMINANCE_RADIUS * DOMINANCE_RADIUS
        for e in enemy_tanks:
            if e.get('dead'):
                continue
            ex, ey, _ = e['position']
            if (ex*ex + ey*ey) <= r2:
                no_enemy_inside = False
                break
    if inside and not ultra_mode and no_enemy_inside:
        dominance_progress += dt
        if dominance_progress >= DOMINANCE_TIME_REQUIRED:
            player_won = True
    else:
        dominance_progress = 0.0

def mouseListener(button, state, x, y):
    if game_over:
        return
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        global camera_fp_mode
        camera_fp_mode = not camera_fp_mode
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if ultra_mode:
            perform_ultra_splash()
        else:
            fire_player()

def fire_player():
    if game_over:
        return
    global player_shots_since_reset, player_overheated, player_overheat_end_time, shot_times
    global ultra_mode
    if ultra_mode:
        return
    if player_overheated:
        return
    now = time.time()
    i = 0
    for t in shot_times:
        if now - t <= SHOT_WINDOW_SEC:
            break
        i += 1
    if i:
        del shot_times[:i]
    if len(shot_times) >= OVERHEAT_THRESHOLD:
        player_overheated = True
        player_overheat_end_time = now + 8.0
        return
    final_angle = (rotation_angle + turret_angle) % 360
    rad = math.radians(final_angle)
    dir_x = math.sin(rad)
    dir_y = -math.cos(rad)
    scale_factor = 1.5 * TANK_SCALE_MULTIPLIER
    forward_offset = (110 - 45/2) * scale_factor
    turret_height = 25 * scale_factor
    spawn_x = player_position[0] + dir_x * forward_offset
    spawn_y = player_position[1] + dir_y * forward_offset
    spawn_z = turret_height
    bullets.append({
        'position': [spawn_x, spawn_y, spawn_z],
        'direction': (dir_x, dir_y),
        'speed': BULLET_SPEED,
        'owner': 'player'
    })
    shot_times.append(now)
    player_shots_since_reset += 1
    if len(shot_times) >= OVERHEAT_THRESHOLD:
        player_overheated = True
        player_overheat_end_time = now + 8.0
def respawn_enemy(index):
    if index < 0 or index >= len(enemy_tanks):
        return
    enemy_r = tank_radius('enemy')
    wall_thickness = get_wall_thickness()
    friendly_r = tank_radius('friendly')
    max_r = max(enemy_r, friendly_r)
    playable_area = GRID_LENGTH - wall_thickness - max_r - EXTRA_SPAWN_GAP
    attempts = 0
    while attempts < MAX_SPAWN_ATTEMPTS:
        attempts += 1
        x = random.uniform(-playable_area, playable_area)
        y = random.uniform(-playable_area, playable_area)
        if can_place_candidate(x, y, enemy_r, [(enemy_tanks, 'enemy'), (friendly_tanks, 'friendly')]):
            cx, cy = clamp_position(x, y, enemy_r)
            enemy_tanks[index] = {
                'position': (cx, cy, 0),
                'rotation': random.uniform(0,360),
                'next_fire_time': time.time() + random.uniform(0.0, AI_FIRE_INTERVAL_SEC),
                'burst_shots_fired': 0,
                'burst_in_progress': False
            }
            return
def convert_friendly_to_enemy(f_index):

    if f_index < 0 or f_index >= len(friendly_tanks):
        return
    f = friendly_tanks.pop(f_index)
    global player_score
    player_score = max(0, player_score - 1)
    enemy_tanks.append({
        'position': f['position'],
        'rotation': f.get('rotation', random.uniform(0,360)),
        'next_fire_time': time.time() + random.uniform(0.0, AI_FIRE_INTERVAL_SEC),
        'burst_shots_fired': 0,
        'burst_in_progress': False,
    })


def compute_text_width(text, font=GLUT_BITMAP_HELVETICA_18):
    return 0

def begin_overlay():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    return 1000, 800

def end_overlay():
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1.0,1.0,1.0)):
    glColor3f(*color)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def showScreen():
    global player_hit_this_draw
    player_hit_this_draw = False
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    setupCamera()

    glBegin(GL_QUADS)
    glColor3f(205/255, 133/255, 63/255)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, -5.0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, -5.0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, -5.0)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, -5.0)
    glEnd()
    
    draw_boundary()

    glColor3f(1.0, 1.0, 1.0)
    ring_outer = DOMINANCE_RADIUS
    ring_inner = max(0.0, ring_outer - (GRID_LENGTH * 0.015))  
    segments = 256
    ring_z = 0.1  
    glBegin(GL_QUADS)
    for i in range(segments):
        a0 = (2*math.pi * i) / segments
        a1 = (2*math.pi * (i+1)) / segments
        x0o = math.cos(a0) * ring_outer
        y0o = math.sin(a0) * ring_outer
        x1o = math.cos(a1) * ring_outer
        y1o = math.sin(a1) * ring_outer
        x0i = math.cos(a0) * ring_inner
        y0i = math.sin(a0) * ring_inner
        x1i = math.cos(a1) * ring_inner
        y1i = math.sin(a1) * ring_inner
        glVertex3f(x0i, y0i, ring_z)
        glVertex3f(x1i, y1i, ring_z)
        glVertex3f(x1o, y1o, ring_z)
        glVertex3f(x0o, y0o, ring_z)
    glEnd()
    
    if ultra_mode:
        draw_robot(player_position, rotation_angle)
    else:
        draw_tank(player_position, rotation_angle, turret_angle, tank_type='player')
    for enemy in enemy_tanks:
        if enemy.get('dead'):
            continue
        draw_tank(enemy['position'], enemy['rotation'], 0, tank_type='enemy')
    for friendly in friendly_tanks:
        draw_tank(friendly['position'], friendly['rotation'], 0, tank_type='friendly')

    if ultra_splash_projectiles:
        glColor3f(0.5, 0.85, 1.0)
        glBegin(GL_QUADS)
        for p in ultra_splash_projectiles:
            x, y, z = p['pos']
            dx, dy = p['dir']
            Lh = p['length'] * 0.5
            Wh = p['width'] * 0.5
            pxn = -dy
            pyn = dx
            norm = math.hypot(pxn, pyn) or 1.0
            pxn /= norm
            pyn /= norm
            z0 = z - p['height'] * 0.5
            z1 = z + p['height'] * 0.5
            c1x = x - pxn*Lh - dx*Wh
            c1y = y - pyn*Lh - dy*Wh
            c2x = x + pxn*Lh - dx*Wh
            c2y = y + pyn*Lh - dy*Wh
            c3x = x + pxn*Lh + dx*Wh
            c3y = y + pyn*Lh + dy*Wh
            c4x = x - pxn*Lh + dx*Wh
            c4y = y - pyn*Lh + dy*Wh
            glVertex3f(c1x, c1y, z1)
            glVertex3f(c2x, c2y, z1)
            glVertex3f(c3x, c3y, z1)
            glVertex3f(c4x, c4y, z1)
            glVertex3f(c1x, c1y, z0)
            glVertex3f(c2x, c2y, z0)
            glVertex3f(c3x, c3y, z0)
            glVertex3f(c4x, c4y, z0)
        glEnd()

    if bullets:
        glColor3f(1, 1, 0)
        for b in bullets:
            glPushMatrix()
            glTranslatef(b['position'][0], b['position'][1], b['position'][2])
            bullet_scale = 10 * TANK_SCALE_MULTIPLIER
            glScalef(bullet_scale, bullet_scale, bullet_scale)
            glutSolidCube(1)
            glPopMatrix()

    glClear(GL_DEPTH_BUFFER_BIT)
    ow, oh = begin_overlay()
    top_y = int(oh * 0.91)
    second_y = int(top_y - 35)
    now = time.time()
    j = 0
    for t in shot_times:
        if now - t <= SHOT_WINDOW_SEC:
            break
        j += 1
    if j:
        del shot_times[:j]
    shots_in_window = len(shot_times)
    mode_text = 'ULTRA' if ultra_mode else 'TANK'
    dom_elapsed = int(min(dominance_progress, DOMINANCE_TIME_REQUIRED)) if (not ultra_mode) else '—'
    draw_text(10, top_y, f'Mode: {mode_text}   Score: {player_score}   Health: {player_health}%   Shots(6s): {shots_in_window}/{OVERHEAT_THRESHOLD}   Circle: {dom_elapsed}s')
    global player_overheated, player_overheat_end_time
    if player_overheated:
        remaining = int(max(0, player_overheat_end_time - time.time()))
        if (int(time.time()) % 2) == 0:
            label = 'OVERHEAT!'
            draw_text(ow - 180, top_y, label, color=(1.0,0.2,0.2))
        countdown_text = f'Cooldown in: {remaining} seconds'
        draw_text(ow - 240, second_y, countdown_text)
    if player_won:
        over1 = 'YOU WIN!'
        over2 = f'Score: {player_score}'
        over3 = 'Press R to restart the game'
        draw_text(420, 420, over1)
        draw_text(430, 390, over2)
        draw_text(360, 360, over3)
    elif game_over:
        over1 = 'GAME OVER'
        over2 = f'Final Score: {player_score}'
        over3 = 'Press R to restart the game'
        draw_text(420, 420, over1)
        draw_text(400, 390, over2)
        draw_text(360, 360, over3)
    end_overlay()

    glutSwapBuffers()

def main():
    glutInit()
    initialize_units()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Shooting Tank")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)
    glEnable(GL_DEPTH_TEST)
    glutMouseFunc(mouseListener)
    glutMainLoop()

if __name__ == "__main__":
    main()

