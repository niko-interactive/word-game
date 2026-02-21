import pygame
import random

from constants import SCREEN_SIZE

from puzzles import PUZZLES
from topic import Topic
from word import Word
from alphabet import Alphabet
from strikes import Strikes
from popup import Popup


def reset_game(font):
    phrase, topic = random.choice(PUZZLES)
    word = Word(phrase, font, *SCREEN_SIZE)
    alphabet = Alphabet(font, *SCREEN_SIZE)
    strikes = Strikes(font, SCREEN_SIZE[0])
    topic = Topic(topic, font, *SCREEN_SIZE)
    return word, alphabet, strikes, topic


pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption('Claude of Fortune')
clock = pygame.time.Clock()
running = True

font = pygame.font.SysFont('Arial', 32)
word, alphabet, strikes, topic = reset_game(font)
popup = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if popup and popup.handle_click(event.pos):
                word, alphabet, strikes, topic = reset_game(font)
                popup = None

        if event.type == pygame.KEYDOWN and popup is None:
            if event.unicode.isalpha():
                letter = event.unicode.upper()
                if letter not in alphabet.guessed:
                    matched = word.guess(letter)
                    alphabet.guess(letter)
                    if not matched:
                        strikes.add_strike()

                    if word.is_solved():
                        popup = Popup('You Win!', font, *SCREEN_SIZE)
                    elif strikes.is_game_over():
                        popup = Popup('You Lose!', font, *SCREEN_SIZE)

    screen.fill('black')
    word.draw(screen)
    alphabet.draw(screen)
    topic.draw(screen)
    strikes.draw(screen)
    if popup:
        popup.draw(screen)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
