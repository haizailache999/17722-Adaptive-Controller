import pygame
import random
import sys
import math

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BLUE = (0, 100, 255)
DARK_BLUE = (0, 50, 150)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Game settings - initial values
BUBBLE_SPEED = 2
BUBBLE_SPAWN_RATE = 0.02
BUBBLE_SIZE = 20
OBSTACLE_WIDTH = 80

class Player:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.width = 60
        self.height = 30
        self.y_speed = 0
        self.max_speed = 8
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def update(self, mouse_y_ratio):
        # mouse_y_ratio is between 0 and 1, where 0 is top and 1 is bottom
        # Convert to speed range from -max_speed to +max_speed
        self.y_speed = (mouse_y_ratio * 2 - 1) * self.max_speed
        
        # Update position
        self.y += self.y_speed
        
        # Keep player on screen
        if self.y < 0:
            self.y = 0
        elif self.y > SCREEN_HEIGHT - self.height:
            self.y = SCREEN_HEIGHT - self.height
            
        # Update rect for collision detection
        self.rect.y = self.y
        
    def draw(self, screen):
        # Draw fish body
        fish_color = (255, 165, 0)  # Orange
        pygame.draw.ellipse(screen, fish_color, (self.x, self.y, self.width, self.height))
        
        # Draw tail
        tail_points = [
            (self.x, self.y + self.height // 2),
            (self.x - 20, self.y),
            (self.x - 20, self.y + self.height)
        ]
        pygame.draw.polygon(screen, fish_color, tail_points)
        
        # Draw eye
        pygame.draw.circle(screen, WHITE, (self.x + self.width - 15, self.y + 10), 8)
        pygame.draw.circle(screen, (0, 0, 0), (self.x + self.width - 12, self.y + 10), 4)
        
class Bubble:
    def __init__(self):
        self.size = random.randint(5, BUBBLE_SIZE)
        self.x = SCREEN_WIDTH + self.size
        self.y = random.randint(self.size, SCREEN_HEIGHT - self.size)
        self.speed = BUBBLE_SPEED * (0.5 + random.random())
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        
    def update(self):
        self.x -= self.speed
        self.rect.x = self.x
        
    def draw(self, screen):
        # Grey bubble with a lighter highlight
        bubble_color = (180, 180, 180)  # Grey color
        pygame.draw.circle(screen, bubble_color, (self.x, self.y), self.size)
        # Add a little reflection highlight
        highlight_color = (220, 220, 220)  # Light grey for highlight
        pygame.draw.circle(screen, highlight_color, (self.x - self.size//3, self.y - self.size//3), self.size//4)

class Obstacle:
    def __init__(self, obstacle_speed):
        self.width = OBSTACLE_WIDTH
        self.height = random.randint(100, 300)
        self.x = SCREEN_WIDTH + self.width
        # Randomly place obstacle at top or bottom
        self.is_top = random.choice([True, False])
        if self.is_top:
            self.y = 0
        else:
            self.y = SCREEN_HEIGHT - self.height
        self.speed = obstacle_speed
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.color = DARK_BLUE
        
    def update(self):
        self.x -= self.speed
        self.rect.x = self.x
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Add some detail to the obstacle (like coral or seaweed)
        if self.is_top:
            for i in range(3):
                x_pos = self.x + i * (self.width // 3) + 10
                weed_height = random.randint(20, 50)
                pygame.draw.line(screen, GREEN, (x_pos, self.height), 
                                (x_pos + random.randint(-10, 10), self.height - weed_height), 5)
        else:
            for i in range(3):
                x_pos = self.x + i * (self.width // 3) + 10
                pygame.draw.circle(screen, (255, 100, 100), 
                                  (x_pos, self.y + random.randint(10, 30)), 10)

def generate_bubbles(bubbles, spawn_rate):
    if random.random() < spawn_rate:
        bubbles.append(Bubble())
    return bubbles

def generate_obstacles(obstacles, spawn_rate, obstacle_speed):
    # Check if we should spawn a new obstacle
    if random.random() < spawn_rate:
        # Check if there's enough distance from the last obstacle
        min_distance = 10  # Minimum pixel gap between obstacles
        can_spawn = True
        
        # Find the rightmost obstacle (closest to screen edge)
        rightmost_x = 0
        for obstacle in obstacles:
            if obstacle.x > rightmost_x:
                rightmost_x = obstacle.x
        
        # Only spawn if there's enough distance or no obstacles
        if obstacles and (SCREEN_WIDTH - rightmost_x) < min_distance:
            can_spawn = False
            
        if can_spawn:
            obstacles.append(Obstacle(obstacle_speed))
    
    return obstacles

def main():
    # Set up the screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Fish Tank Game - 1D Control")
    clock = pygame.time.Clock()
    
    # Game objects
    player = Player()
    bubbles = []
    obstacles = []
    score = 0
    game_over = False
    
    # Game difficulty variables - these can be modified inside the function
    obstacle_spawn_rate = 0.01
    obstacle_speed = 3
    
    # Game loop
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game_over and event.key == pygame.K_SPACE:
                    # Restart game
                    player = Player()
                    bubbles = []
                    obstacles = []
                    score = 0
                    game_over = False
                    obstacle_spawn_rate = 0.01  # Reset difficulty
                    obstacle_speed = 3
        
        if not game_over:
            # Get mouse position for 1D control (only using Y position)
            _, mouse_y = pygame.mouse.get_pos()
            mouse_y_ratio = mouse_y / SCREEN_HEIGHT  # Between 0 and 1
            
            # Update player
            player.update(mouse_y_ratio)
            
            # Generate and update bubbles
            bubbles = generate_bubbles(bubbles, BUBBLE_SPAWN_RATE)
            bubbles = [bubble for bubble in bubbles if bubble.x + bubble.size > 0]
            for bubble in bubbles:
                bubble.update()
                
            # Generate and update obstacles
            obstacles = generate_obstacles(obstacles, obstacle_spawn_rate, obstacle_speed)
            obstacles = [obstacle for obstacle in obstacles if obstacle.x + obstacle.width > 0]
            for obstacle in obstacles:
                obstacle.update()
            
            # Collision detection
            for bubble in bubbles[:]:
                if player.rect.colliderect(bubble.rect):
                    bubbles.remove(bubble)
                    score += 1
                    
            for obstacle in obstacles:
                if player.rect.colliderect(obstacle.rect):
                    game_over = True
                    
            # Increase difficulty over time
            if score > 0 and score % 10 == 0:
                obstacle_spawn_rate = min(0.05, obstacle_spawn_rate + 0.001)
                obstacle_speed = min(8, obstacle_speed + 0.1)
        
        # Drawing
        # Draw background - just a solid blue
        screen.fill(BLUE)
        
        # Draw game objects
        for bubble in bubbles:
            bubble.draw(screen)
            
        for obstacle in obstacles:
            obstacle.draw(screen)
            
        player.draw(screen)
        
        # Draw score
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Draw difficulty level
        speed_text = font.render(f"Speed: {obstacle_speed:.1f}", True, WHITE)
        screen.blit(speed_text, (10, 50))
        
        # Draw game over
        if game_over:
            font = pygame.font.SysFont(None, 72)
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 
                                         SCREEN_HEIGHT//2 - game_over_text.get_height()//2))
            
            font = pygame.font.SysFont(None, 36)
            restart_text = font.render("Press SPACE to restart", True, YELLOW)
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 
                                      SCREEN_HEIGHT//2 + 50))
        
        # Draw 1D control indicator
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 30, 0, 20, SCREEN_HEIGHT))
        # Draw control position indicator
        indicator_y = mouse_y_ratio * SCREEN_HEIGHT
        pygame.draw.circle(screen, RED, (SCREEN_WIDTH - 20, int(indicator_y)), 15)
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
