import pygame


def main() -> None:
    """Client entry point"""
    pygame.init()
    pygame.display.set_caption("Electric Elves Game")

    screen_size = (800, 600)
    screen = pygame.display.set_mode(screen_size)

    prey_position = (300, 200)
    prey_size = (10, 10)

    hunter_position = (500, 500)
    hunter_size = (40, 40)

    # TODO: Connect to the server!

    while True:
        for event in pygame.event.get():
            # Check if window should be closed
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return

        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (0, 0, 255), (prey_position[0], prey_position[1], prey_size[0], prey_size[1]))
        pygame.draw.rect(screen, (255, 0, 0), (hunter_position[0], hunter_position[1], hunter_size[0], hunter_size[1]))
        pygame.display.flip()


if __name__ == "__main__":
    main()
