"""
坦克大战（单文件）
说明：使用 Python + Pygame 运行
依赖：pip install pygame
运行：python tank_battle.py

双人本地对战：
 玩家1: W/A/S/D 移动, Q/E 旋转炮塔, SPACE 开火
 玩家2: Up/Left/Down/Right 移动, , , /?（使用 J/L 旋转炮塔）, RCTRL 开火
（注：如果键位显示有问题，实际代码里标注了按键）

特性：
 - 转向炮塔与车身分离
 - 子弹碰撞、墙体阻挡
 - 血量和得分，第一位到达 5 分获胜
 - 简易障碍地图
"""

import pygame
import math
import random

# --------- 配置 ---------
SCREEN_W, SCREEN_H = 960, 640
FPS = 60
TANK_SIZE = (40, 30)  # 车身矩形大小
BULLET_SPEED = 8
BULLET_LIFE = 90  # 帧
MAX_SCORE = 5

# 颜色
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (130,130,130)
RED = (200,40,40)
BLUE = (40,80,200)
GREEN = (40,200,60)

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("坦克大战 - Python Pygame")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
large_font = pygame.font.SysFont(None, 48)

# --------- 类定义 ---------
class Tank:
    def __init__(self, x, y, color, controls):
        self.x = x
        self.y = y
        self.angle = 0            # 车身朝向（弧度）
        self.turret_angle = 0     # 炮塔朝向（弧度）
        self.color = color
        self.speed = 2.6
        self.turn_speed = math.radians(3.2)
        self.size = TANK_SIZE
        self.controls = controls
        self.health = 3
        self.respawn()
        self.score = 0
        self.respawn_timer = 0

    def respawn(self):
        self.health = 3
        self.respawn_timer = 0

    def rect(self):
        w,h = self.size
        return pygame.Rect(self.x - w//2, self.y - h//2, w, h)

    def update(self, keys, walls):
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            return
        # 移动
        forward = 0
        turn = 0
        if keys[self.controls['up']]: forward += 1
        if keys[self.controls['down']]: forward -= 1
        if keys[self.controls['left']]: turn -= 1
        if keys[self.controls['right']]: turn += 1

        # 车身旋转
        self.angle += turn * self.turn_speed
        # 前进后退
        vx = math.cos(self.angle) * forward * self.speed
        vy = math.sin(self.angle) * forward * self.speed
        newrect = self.rect().move(vx, vy)
        # 碰撞检测：墙
        blocked = False
        for w in walls:
            if newrect.colliderect(w):
                blocked = True
                break
        if not blocked:
            self.x += vx
            self.y += vy
        # 炮塔控制（独立旋转）
        if keys[self.controls['turret_left']]:
            self.turret_angle -= self.turn_speed
        if keys[self.controls['turret_right']]:
            self.turret_angle += self.turn_speed
        # 保持角度范围
        self.turret_angle %= (2*math.pi)

    def draw(self, surf):
        if self.respawn_timer > 0:
            # 闪烁效果
            if (self.respawn_timer // 6) % 2 == 0:
                return
        # 画车身（旋转矩形）
        w,h = self.size
        body_surf = pygame.Surface((w,h), pygame.SRCALPHA)
        pygame.draw.rect(body_surf, self.color, (0,0,w,h), border_radius=6)
        # 画车轮/装饰
        pygame.draw.rect(body_surf, BLACK, (2, h//3, w-4, h//6))
        body = pygame.transform.rotate(body_surf, -math.degrees(self.angle))
        br = body.get_rect(center=(self.x, self.y))
        surf.blit(body, br)
        # 炮塔
        turret_len = max(w,h)
        tx = self.x + math.cos(self.turret_angle)*turret_len*0.6
        ty = self.y + math.sin(self.turret_angle)*turret_len*0.6
        pygame.draw.line(surf, BLACK, (self.x, self.y), (tx,ty), 6)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 12)
        # 生命条
        for i in range(self.health):
            pygame.draw.rect(surf, RED, (self.x-18 + i*12, self.y + 26, 8, 6))

    def fire(self):
        if self.respawn_timer > 0:
            return None
        # 子弹从炮筒口发出
        start_x = self.x + math.cos(self.turret_angle)* (max(self.size)//1.6)
        start_y = self.y + math.sin(self.turret_angle)* (max(self.size)//1.6)
        return Bullet(start_x, start_y, self.turret_angle, self)

class Bullet:
    def __init__(self, x, y, angle, owner):
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner
        self.speed = BULLET_SPEED
        self.life = BULLET_LIFE
        self.radius = 4

    def update(self, walls):
        self.x += math.cos(self.angle)*self.speed
        self.y += math.sin(self.angle)*self.speed
        self.life -= 1
        # 墙体碰撞
        brect = pygame.Rect(self.x-self.radius, self.y-self.radius, self.radius*2, self.radius*2)
        for w in walls:
            if brect.colliderect(w):
                self.life = 0
                return

    def draw(self, surf):
        pygame.draw.circle(surf, BLACK, (int(self.x), int(self.y)), self.radius)

# --------- 地图与障碍 ---------
def make_walls():
    walls = []
    # 外围墙
    pad = 10
    walls.append(pygame.Rect(0,0,SCREEN_W,pad))
    walls.append(pygame.Rect(0,0,pad,SCREEN_H))
    walls.append(pygame.Rect(0,SCREEN_H-pad,SCREEN_W,pad))
    walls.append(pygame.Rect(SCREEN_W-pad,0,pad,SCREEN_H))
    # 中间、障碍
    for i in range(5):
        w = pygame.Rect(160 + i*120, 200, 40, 200)
        walls.append(w)
    # 随机小障碍
    for i in range(6):
        rx = random.randint(80, SCREEN_W-80)
        ry = random.randint(80, SCREEN_H-80)
        walls.append(pygame.Rect(rx, ry, 60, 20))
    return walls

# --------- 控制设置 ---------
controls_p1 = {
    'up': pygame.K_w,
    'down': pygame.K_s,
    'left': pygame.K_a,
    'right': pygame.K_d,
    'turret_left': pygame.K_q,
    'turret_right': pygame.K_e,
    'fire': pygame.K_SPACE
}
controls_p2 = {
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'turret_left': pygame.K_COMMA,   # , 键
    'turret_right': pygame.K_PERIOD, # . 键
    'fire': pygame.K_RCTRL
}

# --------- 游戏主循环 ---------
def draw_walls(surf, walls):
    for w in walls:
        pygame.draw.rect(surf, GRAY, w)


def draw_text(surf, txt, x, y, color=BLACK):
    surf.blit(font.render(txt, True, color), (x,y))


def main():
    walls = make_walls()
    p1 = Tank(120, SCREEN_H//2, BLUE, controls_p1)
    p2 = Tank(SCREEN_W-120, SCREEN_H//2, GREEN, controls_p2)
    bullets = []
    running = True
    winner = None

    shoot_cooldowns = {p1:0, p2:0}

    while running:
        dt = clock.tick(FPS)
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == p1.controls['fire'] and shoot_cooldowns[p1] <= 0:
                    b = p1.fire()
                    if b: bullets.append(b); shoot_cooldowns[p1] = 18
                if event.key == p2.controls['fire'] and shoot_cooldowns[p2] <= 0:
                    b = p2.fire()
                    if b: bullets.append(b); shoot_cooldowns[p2] = 18
                # 重置游戏
                if event.key == pygame.K_r and winner:
                    p1.score = p2.score = 0
                    winner = None
                    p1.respawn_timer = p2.respawn_timer = 0
                    bullets.clear()
                    walls = make_walls()
        # 更新
        p1.update(keys, walls)
        p2.update(keys, walls)
        for k in list(shoot_cooldowns.keys()):
            if shoot_cooldowns[k] > 0: shoot_cooldowns[k] -= 1

        for b in bullets[:]:
            b.update(walls)
            if b.life <= 0:
                bullets.remove(b)
                continue
            # 子弹击中坦克
            for t in (p1, p2):
                if t is b.owner: continue
                if t.respawn_timer>0: continue
                if t.rect().collidepoint(b.x, b.y):
                    bullets.remove(b)
                    t.health -= 1
                    if t.health <= 0:
                        b.owner.score += 1
                        t.respawn_timer = FPS * 2  # 2 秒复活时间
                        t.health = 0
                        # 检查胜利
                        if b.owner.score >= MAX_SCORE:
                            winner = b.owner
                    break

        # 绘制
        screen.fill((200, 220, 240))
        draw_walls(screen, walls)
        for b in bullets:
            b.draw(screen)
        p1.draw(screen)
        p2.draw(screen)

        # HUD
        draw_text(screen, f"玩家1 (蓝) 分数: {p1.score}", 10, 8)
        draw_text(screen, f"玩家2 (绿) 分数: {p2.score}", 10, 30)
        draw_text(screen, "按 R 重开", SCREEN_W-110, 8)
        draw_text(screen, "按 ESC 退出", SCREEN_W-110, 28)

        if winner:
            win_text = "玩家1 赢了！" if winner is p1 else "玩家2 赢了！"
            txt = large_font.render(win_text, True, BLACK)
            rect = txt.get_rect(center=(SCREEN_W//2, 60))
            screen.blit(txt, rect)
            sub = font.render("按 R 重开", True, BLACK)
            screen.blit(sub, (SCREEN_W//2 - 50, 110))

        pygame.display.flip()

        # 退出键
        if keys[pygame.K_ESCAPE]:
            running = False

    pygame.quit()

if __name__ == '__main__':
    main()
