import pygame

pygame.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))

player_x = 400
player_y = 500

def update_game(command):

    global player_x

    if command == "LEFT":
        player_x -= 5

    if command == "RIGHT":
        player_x += 5

    screen.fill((0,0,0))

    pygame.draw.rect(screen,(255,0,0),(player_x,player_y,50,50))

    pygame.display.update()