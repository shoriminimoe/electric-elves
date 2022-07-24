import pygame


def main() -> None:
    """Client entry point"""
    pygame.init()
    pygame.display.set_caption("Electric Elves Game")

    screen_size = (800, 600)
    screen = pygame.display.set_mode(screen_size)

    # TODO: Connect to the server!

    while True:
        for event in pygame.event.get():
            # Check if window should be closed
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()

        screen.fill((0, 0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
