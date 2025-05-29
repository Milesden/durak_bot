
import random

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {rank: i for i, rank in enumerate(RANKS)}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank}{self.suit}"

    def beats(self, other, trump_suit):
        if self.suit == other.suit:
            return RANK_VALUES[self.rank] > RANK_VALUES[other.rank]
        elif self.suit == trump_suit:
            return True
        return False

class DurakGame:
    def __init__(self):
        self.deck = [Card(s, r) for s in SUITS for r in RANKS]
        random.shuffle(self.deck)
        self.trump = self.deck[-1].suit
        self.player_hand = [self.deck.pop() for _ in range(6)]
        self.bot_hand = [self.deck.pop() for _ in range(6)]
        self.field = []

    def get_state(self):
        return {
            "trump": self.trump,
            "player_hand": self.player_hand,
            "bot_hand": self.bot_hand,
            "field": self.field
        }

    def play_card(self, player_card):
        self.field.append((player_card, None))

    def bot_defend(self):
        attack_card = self.field[-1][0]
        for i, card in enumerate(self.bot_hand):
            if card.beats(attack_card, self.trump):
                self.field[-1] = (attack_card, card)
                del self.bot_hand[i]
                return card
        return None
