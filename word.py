import pygame
from constants import SLOT_WIDTH, SLOT_HEIGHT, GAP
from letter import Letter


class Word:
    def __init__(self, word, font, screen_width, screen_height):
        self.word = word.upper()
        self.slots = []

        space_width = 24
        total_width = 0

        for char in self.word:
            if char == ' ':
                total_width += space_width
            else:
                total_width += SLOT_WIDTH
            total_width += GAP
        total_width -= GAP

        start_x = (screen_width - total_width) // 2
        y = (screen_height - SLOT_HEIGHT) // 2

        x = start_x
        for char in self.word:
            if char == ' ':
                x += space_width + GAP
            else:
                self.slots.append(Letter(x, y, font))
                x += SLOT_WIDTH + GAP

    def guess(self, letter):
        matched = False
        non_space_index = 0
        for char in self.word:
            if char == ' ':
                continue
            if char == letter.upper():
                self.slots[non_space_index].letter = char
                matched = True
            non_space_index += 1
        return matched

    def is_solved(self):
        return all(slot.letter is not None for slot in self.slots)

    def draw(self, screen):
        for slot in self.slots:
            slot.draw(screen)
