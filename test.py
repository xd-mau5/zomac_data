import random

class Character:
    def __init__(self, name, crit_rate):
        self.name = name
        self.crit_rate = crit_rate
        self.crit_count = 0
        self.total_hits = 0

    def attack(self):
        self.total_hits += 1
        if random.random() < self.crit_rate:
            self.crit_count += 1
            print(f"{self.name} landed a critical hit!")
        else:
            print(f"{self.name} attack!")

    def crit_probability(self):
        if self.total_hits == 0:
            return 0
        return self.crit_count / self.total_hits

# Example usage:
character = Character("Jingliu", 0.3)  # Assuming Jingliu has a 30% crit rate
for _ in range(10):
    character.attack()

print(f"Probability of critical hit for {character.name}: {character.crit_probability()}")