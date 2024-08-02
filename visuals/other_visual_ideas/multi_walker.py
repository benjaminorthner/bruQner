import pygame
import random
import sys

# Constants
WIDTH, HEIGHT = 1080/2, 1920/2  # 9:16 vertical grid
BACKGROUND_COLOR = (0, 0, 0)
WALKER_COLOR = (255, 255, 255)
RECT_BORDER_COLOR = (255, 0, 0)
TEXT_COLOR = (255, 255, 255)
CROSSHAIR_COLOR = (0, 255, 0)
NUM_WALKERS = 10
MAX_TRAIL_LENGTH = 100  # Maximum number of positions to keep in history
ROWS, COLS = 5, 2  # 2x5 grid

class Walker:
    def __init__(self, x, y, rect, label):
        self.positions = [(x, y)]
        self.rect = rect
        self.label = label

    def move(self, data):
        dx, dy = data
        new_x = self.positions[-1][0] + dx
        new_y = self.positions[-1][1] + dy

        # if reaches right edge
        if new_x > self.rect[0] + self.rect[2]:
            new_x = self.rect[0] + (new_y - self.rect[0])
            new_y = self.rect[1] + self.rect[3] - 1
        
        # if reaches from the top edge
        if new_y < self.rect[1]:
            new_y = self.rect[1] + (new_x - self.rect[0])
            new_x = self.rect[0]

        self.positions.append((new_x, new_y))
        if len(self.positions) > MAX_TRAIL_LENGTH:
            self.positions.pop(0)

    def draw(self, screen, font):
        # Draw the trail
        if len(self.positions) > 1:
            pygame.draw.lines(screen, WALKER_COLOR, False, self.positions)

        # Draw the label text
        text_surface = font.render(self.label, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(self.rect[0] + self.rect[2] // 2, self.rect[1] + self.rect[3] // 2))
        screen.blit(text_surface, text_rect)

        # Draw crosshair at the center
        center_x = self.rect[0] + self.rect[2] // 2
        center_y = self.rect[1] + self.rect[3] // 2
        pygame.draw.line(screen, CROSSHAIR_COLOR, (center_x - 10, center_y), (center_x + 10, center_y), 1)
        pygame.draw.line(screen, CROSSHAIR_COLOR, (center_x, center_y - 10), (center_x, center_y + 10), 1)
        
        # Draw diagonal line from the center towards the top rigth
        end_x = self.rect[0] + self.rect[2]
        end_y = self.rect[1] + self.rect[3] // 2 - self.rect[2]//2
        pygame.draw.line(screen, CROSSHAIR_COLOR, (center_x, center_y), (end_x, end_y), 1)

def get_live_data():
    # This function should be replaced with your actual data streaming code.
    # For now, it returns random movements.
    dx = random.choice([1, 0])
    dy = random.choice([-1, 0])
    return dx, dy

def draw_grid(screen, font, border_padding, rect_padding, row_labels, col_labels):
    rects = []
    label_space_x = 100  # Space for row labels
    label_space_y = 50   # Space for column labels

    # Adjust dimensions based on padding and label space
    usable_width = WIDTH - 2 * border_padding - label_space_x
    usable_height = HEIGHT - 2 * border_padding - label_space_y

    # Calculate individual rectangle dimensions
    rect_width = (usable_width - (COLS - 1) * rect_padding) // COLS
    rect_height = (usable_height - (ROWS - 1) * rect_padding) // ROWS

    for row in range(ROWS):
        # Draw row labels
        row_label_surface = font.render(row_labels[row], True, TEXT_COLOR)
        row_label_rect = row_label_surface.get_rect(center=(border_padding + label_space_x // 2, border_padding + label_space_y + row * (rect_height + rect_padding) + rect_height // 2))
        screen.blit(row_label_surface, row_label_rect)

        for col in range(COLS):
            # Draw column labels for the first row only
            if row == 0:
                col_label_surface = font.render(col_labels[col], True, TEXT_COLOR)
                col_label_rect = col_label_surface.get_rect(center=(border_padding + label_space_x + col * (rect_width + rect_padding) + rect_width // 2, border_padding + label_space_y // 2))
                screen.blit(col_label_surface, col_label_rect)

            x = border_padding + label_space_x + col * (rect_width + rect_padding)
            y = border_padding + label_space_y + row * (rect_height + rect_padding)
            pygame.draw.rect(screen, RECT_BORDER_COLOR, (x, y, rect_width, rect_height), 2)
            rects.append((x, y, rect_width, rect_height))
    return rects

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Random Walkers in 2x5 Grid with Labels and Crosshairs')
    font = pygame.font.Font(None, 36)

    border_padding = 50  # Example padding around the border
    rect_padding = 20    # Example padding between rectangles
    row_labels = [f"Row {i + 1}" for i in range(ROWS)]
    col_labels = [f"Col {i + 1}" for i in range(COLS)]

    walkers = []
    rects = draw_grid(screen, font, border_padding, rect_padding, row_labels, col_labels)
    for i, rect in enumerate(rects):
        x = rect[0] + rect[2] // 2  # Center x
        y = rect[1] + rect[3] // 2  # Center y
        label = ""
        walkers.append(Walker(x, y, rect, label))

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BACKGROUND_COLOR)

        rects = draw_grid(screen, font, border_padding, rect_padding, row_labels, col_labels)  # Redraw grid borders with padding

        for walker in walkers:
            data = get_live_data()
            walker.move(data)
            walker.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)  # Maintain 60 frames per second

if __name__ == "__main__":
    main()
