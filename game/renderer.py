import pygame
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .game import GameManager


class Renderer:
    # Define some colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    FACTOR = 10

    def __init__(self):
        self.screen = pygame.display.set_mode((1600, 900))
        self.clock = pygame.time.Clock()

    def start(self):
        pygame.init()
        pygame.display.set_caption("CG Search Race")

    def end(self):
        pygame.quit()

    def render(self, game: 'GameManager'):
        self.screen.fill(Renderer.WHITE)

        num_checkpt = (len(game.checkpoints) - 1) // 3
        for i in range(num_checkpt):
            checkpoint = game.checkpoints[i]
            color = Renderer.GREEN if i == game.pod.nextCheckPointId else Renderer.BLACK
            x, y = checkpoint.x // Renderer.FACTOR, checkpoint.y // Renderer.FACTOR
            pygame.draw.circle(self.screen, color, (x, y), checkpoint.r // Renderer.FACTOR, width=3)

            font = pygame.font.SysFont(None, 48)
            img = font.render(str(i), True, color)
            rect = img.get_rect()
            self.screen.blit(img, [x - rect.width/2, y - rect.height/2])

        start = pygame.Vector2(game.pod.x // Renderer.FACTOR, game.pod.y // Renderer.FACTOR)

        ra = math.radians(game.pod.angle)
        px = game.pod.x + math.cos(ra) * max(1000, game.pod.speed * 10)
        py = game.pod.y + math.sin(ra) * max(1000, game.pod.speed * 10)
        end = pygame.Vector2(px // Renderer.FACTOR, py // Renderer.FACTOR)

        self.draw_arrow(self.screen, start, end, Renderer.BLACK, body_width=5, head_width=10, head_height=10)

        pygame.display.flip()
        self.clock.tick(60)

    def draw_arrow(
                  self,
                  surface: pygame.Surface,
                  start: pygame.Vector2,
                  end: pygame.Vector2,
                  color: pygame.Color,
                  body_width: int = 2,
                  head_width: int = 4,
                  head_height: int = 4,
                  ):
        """Draw an arrow between start and end with the arrow head at the end.

        Args:
            surface (pygame.Surface): The surface to draw on
            start (pygame.Vector2): Start position
            end (pygame.Vector2): End position
            color (pygame.Color): Color of the arrow
            body_width (int, optional): Defaults to 2.
            head_width (int, optional): Defaults to 4.
            head_height (float, optional): Defaults to 2.
        """
        arrow = start - end
        angle = arrow.angle_to(pygame.Vector2(0, -1))
        body_length = arrow.length() - head_height

        # Create the triangle head around the origin
        head_verts = [
            pygame.Vector2(0, head_height / 2),  # Center
            pygame.Vector2(head_width / 2, -head_height / 2),  # Bottomright
            pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
        ]
        # Rotate and translate the head into place
        translation = pygame.Vector2(0, arrow.length() - (head_height / 2)).rotate(-angle)
        for i in range(len(head_verts)):
            head_verts[i].rotate_ip(-angle)
            head_verts[i] += translation
            head_verts[i] += start

        pygame.draw.polygon(surface, color, head_verts)

        # Stop weird shapes when the arrow is shorter than arrow head
        if arrow.length() >= head_height:
            # Calculate the body rect, rotate and translate into place
            body_verts = [
                pygame.Vector2(-body_width / 2, body_length / 2),  # Topleft
                pygame.Vector2(body_width / 2, body_length / 2),  # Topright
                pygame.Vector2(body_width / 2, -body_length / 2),  # Bottomright
                pygame.Vector2(-body_width / 2, -body_length / 2),  # Bottomleft
            ]
            translation = pygame.Vector2(0, body_length / 2).rotate(-angle)
            for i in range(len(body_verts)):
                body_verts[i].rotate_ip(-angle)
                body_verts[i] += translation
                body_verts[i] += start

            pygame.draw.polygon(surface, color, body_verts)