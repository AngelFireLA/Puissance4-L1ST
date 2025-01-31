import pygame
import random
import math
import sys

# =====================
# 1. Snake Game
# =====================
def snake_game():
    pygame.init()
    dis_width = 600
    dis_height = 400
    dis = pygame.display.set_mode((dis_width, dis_height))
    pygame.display.set_caption('Snake Game')
    clock = pygame.time.Clock()
    snake_block = 10
    snake_speed = 15
    font_style = pygame.font.SysFont("bahnschrift", 25)

    def our_snake(snake_block, snake_list):
        for x in snake_list:
            pygame.draw.rect(dis, (0, 0, 0), [x[0], x[1], snake_block, snake_block])

    # Initial snake position and food
    x1 = dis_width / 2
    y1 = dis_height / 2
    x1_change = 0
    y1_change = 0
    snake_List = []
    Length_of_snake = 1
    foodx = round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0
    foody = round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x1_change = -snake_block
                    y1_change = 0
                elif event.key == pygame.K_RIGHT:
                    x1_change = snake_block
                    y1_change = 0
                elif event.key == pygame.K_UP:
                    y1_change = -snake_block
                    x1_change = 0
                elif event.key == pygame.K_DOWN:
                    y1_change = snake_block
                    x1_change = 0

        if x1 >= dis_width or x1 < 0 or y1 >= dis_height or y1 < 0:
            running = False
            break

        x1 += x1_change
        y1 += y1_change
        dis.fill((50, 153, 213))  # Blue background
        pygame.draw.rect(dis, (0, 255, 0), [foodx, foody, snake_block, snake_block])
        snake_Head = [x1, y1]
        snake_List.append(snake_Head)
        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        # Self-collision check
        for segment in snake_List[:-1]:
            if segment == snake_Head:
                running = False
                break

        our_snake(snake_block, snake_List)
        pygame.display.update()

        # Check if food is eaten
        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0
            foody = round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0
            Length_of_snake += 1

        clock.tick(snake_speed)
    pygame.display.quit()


# =====================
# 2. Connect 4 Game
# =====================
def connect4_game():
    pygame.init()

    def create_board():
        board = []
        for _ in range(6):
            board.append([0] * 7)
        return board

    def drop_piece(board, row, col, piece):
        board[row][col] = piece

    def is_valid_location(board, col):
        return board[0][col] == 0

    def get_next_open_row(board, col):
        for r in range(5, -1, -1):
            if board[r][col] == 0:
                return r

    def winning_move(board, piece):
        # Horizontal check
        for r in range(6):
            for c in range(7 - 3):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        # Vertical check
        for c in range(7):
            for r in range(6 - 3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
        # Diagonal (positive slope)
        for r in range(6 - 3):
            for c in range(7 - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
        # Diagonal (negative slope)
        for r in range(3, 6):
            for c in range(7 - 3):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True
        return False

    def draw_board(board, screen, square_size, radius):
        for c in range(7):
            for r in range(6):
                pygame.draw.rect(screen, (0, 0, 255), (c * square_size, (r + 1) * square_size, square_size, square_size))
                if board[r][c] == 0:
                    pygame.draw.circle(screen, (0, 0, 0),
                                       (int(c * square_size + square_size / 2), int((r + 1) * square_size + square_size / 2)),
                                       radius)
                elif board[r][c] == 1:
                    pygame.draw.circle(screen, (255, 0, 0),
                                       (int(c * square_size + square_size / 2), int((r + 1) * square_size + square_size / 2)),
                                       radius)
                elif board[r][c] == 2:
                    pygame.draw.circle(screen, (255, 255, 0),
                                       (int(c * square_size + square_size / 2), int((r + 1) * square_size + square_size / 2)),
                                       radius)
        pygame.display.update()

    square_size = 100
    width = 7 * square_size
    height = (6 + 1) * square_size  # Extra row for move indication
    radius = int(square_size / 2 - 5)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Connect 4")
    board = create_board()
    game_over = False
    turn = 0
    font = pygame.font.SysFont("monospace", 75)
    clock = pygame.time.Clock()

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
                return
            if event.type == pygame.MOUSEMOTION:
                pygame.draw.rect(screen, (0, 0, 0), (0, 0, width, square_size))
                posx = event.pos[0]
                if turn == 0:
                    pygame.draw.circle(screen, (255, 0, 0), (posx, int(square_size / 2)), radius)
                else:
                    pygame.draw.circle(screen, (255, 255, 0), (posx, int(square_size / 2)), radius)
                pygame.display.update()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pygame.draw.rect(screen, (0, 0, 0), (0, 0, width, square_size))
                posx = event.pos[0]
                col = int(math.floor(posx / square_size))
                if is_valid_location(board, col):
                    row = get_next_open_row(board, col)
                    if turn == 0:
                        drop_piece(board, row, col, 1)
                        if winning_move(board, 1):
                            label = font.render("Player 1 wins!", True, (255, 0, 0))
                            screen.blit(label, (40, 10))
                            game_over = True
                    else:
                        drop_piece(board, row, col, 2)
                        if winning_move(board, 2):
                            label = font.render("Player 2 wins!", True, (255, 255, 0))
                            screen.blit(label, (40, 10))
                            game_over = True
                    draw_board(board, screen, square_size, radius)
                    turn = (turn + 1) % 2
                    if game_over:
                        pygame.time.wait(3000)
                        return
        clock.tick(60)
    pygame.display.quit()


# =====================
# 3. Conway's Game of Life
# =====================
def game_of_life():
    pygame.init()
    CELL_SIZE = 10
    COLS = 80
    ROWS = 60
    WIDTH = COLS * CELL_SIZE
    HEIGHT = ROWS * CELL_SIZE
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Conway's Game of Life")
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    grid = [[random.choice([0, 1]) for _ in range(COLS)] for _ in range(ROWS)]
    clock = pygame.time.Clock()

    def draw_grid(screen, grid):
        for row in range(ROWS):
            for col in range(COLS):
                color = WHITE if grid[row][col] == 1 else BLACK
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect)
        pygame.display.update()

    def count_neighbors(grid, row, col):
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r = row + dr
                c = col + dc
                if 0 <= r < ROWS and 0 <= c < COLS:
                    count += grid[r][c]
        return count

    def update_grid(current_grid):
        new_grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        for row in range(ROWS):
            for col in range(COLS):
                alive_neighbors = count_neighbors(current_grid, row, col)
                if current_grid[row][col] == 1:
                    if alive_neighbors < 2 or alive_neighbors > 3:
                        new_grid[row][col] = 0
                    else:
                        new_grid[row][col] = 1
                else:
                    if alive_neighbors == 3:
                        new_grid[row][col] = 1
        return new_grid

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
        draw_grid(screen, grid)
        grid = update_grid(grid)
        clock.tick(10)
    pygame.display.quit()


# =====================
# 4. Flappy Bird Clone
# =====================
def flappy_bird_game():
    pygame.init()
    SCREEN_WIDTH = 400
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Flappy Bird Clone")
    clock = pygame.time.Clock()
    BIRD_X = 50
    BIRD_START_Y = SCREEN_HEIGHT // 2
    BIRD_RADIUS = 20
    bird_y = BIRD_START_Y
    bird_velocity = 0
    GRAVITY = 0.5
    FLAP_STRENGTH = -10
    PIPE_WIDTH = 70
    PIPE_GAP = 150
    PIPE_VELOCITY = 3
    pipe_frequency = 1500  # milliseconds between pipes
    last_pipe_time = pygame.time.get_ticks()
    pipes = []
    score = 0
    font = pygame.font.SysFont("Arial", 32)
    game_over = False

    def create_pipe():
        gap_y = random.randint(100, SCREEN_HEIGHT - 100)
        top_pipe = pygame.Rect(SCREEN_WIDTH, 0, PIPE_WIDTH, gap_y - PIPE_GAP // 2)
        bottom_pipe = pygame.Rect(SCREEN_WIDTH, gap_y + PIPE_GAP // 2, PIPE_WIDTH,
                                  SCREEN_HEIGHT - (gap_y + PIPE_GAP // 2))
        return top_pipe, bottom_pipe

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    bird_velocity = FLAP_STRENGTH
                if event.key == pygame.K_r and game_over:
                    bird_y = BIRD_START_Y
                    bird_velocity = 0
                    pipes = []
                    score = 0
                    game_over = False

        if not game_over:
            bird_velocity += GRAVITY
            bird_y += bird_velocity
            current_time = pygame.time.get_ticks()
            if current_time - last_pipe_time > pipe_frequency:
                last_pipe_time = current_time
                new_top, new_bottom = create_pipe()
                pipes.extend([new_top, new_bottom])
            for pipe in pipes:
                pipe.x -= PIPE_VELOCITY
            pipes = [pipe for pipe in pipes if pipe.x + PIPE_WIDTH > 0]
            bird_rect = pygame.Rect(BIRD_X - BIRD_RADIUS, int(bird_y) - BIRD_RADIUS,
                                    BIRD_RADIUS * 2, BIRD_RADIUS * 2)
            for pipe in pipes:
                if bird_rect.colliderect(pipe):
                    game_over = True
            if bird_y - BIRD_RADIUS < 0 or bird_y + BIRD_RADIUS > SCREEN_HEIGHT:
                game_over = True
            for pipe in pipes:
                if pipe.x + PIPE_WIDTH == BIRD_X:
                    score += 0.5

        screen.fill((135, 206, 235))
        pygame.draw.circle(screen, (255, 255, 0), (BIRD_X, int(bird_y)), BIRD_RADIUS)
        for pipe in pipes:
            pygame.draw.rect(screen, (0, 255, 0), pipe)
        score_text = font.render("Score: " + str(int(score)), True, (0, 0, 0))
        screen.blit(score_text, (10, 10))
        if game_over:
            over_text = font.render("Game Over! Press R to Restart", True, (255, 0, 0))
            screen.blit(over_text, (20, SCREEN_HEIGHT // 2 - 50))
        pygame.display.update()
        clock.tick(60)
    pygame.display.quit()


# =====================
# Graphical Launcher Menu
# =====================
def launcher_menu():
    # Initialize Pygame for the launcher menu
    pygame.init()
    menu_width = 600
    menu_height = 600
    screen = pygame.display.set_mode((menu_width, menu_height))
    pygame.display.set_caption("Game Launcher")
    font = pygame.font.SysFont("Arial", 30)
    clock = pygame.time.Clock()

    # Define button options and corresponding game functions
    button_options = [
        {"label": "Snake", "function": snake_game},
        {"label": "Connect 4", "function": connect4_game},
        {"label": "Conway's Game of Life", "function": game_of_life},
        {"label": "Flappy Bird", "function": flappy_bird_game},
        {"label": "Quit", "function": None}
    ]

    # Calculate button positions
    button_width = 300
    button_height = 50
    button_spacing = 20
    total_height = len(button_options) * button_height + (len(button_options) - 1) * button_spacing
    start_y = (menu_height - total_height) // 2
    buttons = []
    for index, option in enumerate(button_options):
        x = (menu_width - button_width) // 2
        y = start_y + index * (button_height + button_spacing)
        rect = pygame.Rect(x, y, button_width, button_height)
        buttons.append({"rect": rect, "label": option["label"], "function": option["function"]})

    running = True
    while running:
        screen.fill((100, 100, 100))  # Gray background

        # Draw title text
        title_text = font.render("Select a Game", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(menu_width // 2, 50))
        screen.blit(title_text, title_rect)

        # Draw buttons
        for button in buttons:
            pygame.draw.rect(screen, (0, 0, 200), button["rect"])
            text = font.render(button["label"], True, (255, 255, 255))
            text_rect = text.get_rect(center=button["rect"].center)
            screen.blit(text, text_rect)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for button in buttons:
                    if button["rect"].collidepoint(pos):
                        if button["function"] is None:
                            running = False
                        else:
                            pygame.display.quit()  # Close the launcher window
                            button["function"]()  # Launch the selected game
                            # Reinitialize the launcher after the game ends
                            pygame.init()
                            screen = pygame.display.set_mode((menu_width, menu_height))
                            pygame.display.set_caption("Game Launcher")
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    launcher_menu()
