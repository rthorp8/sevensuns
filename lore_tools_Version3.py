import random

def random_history(burg_name):
    events = [
        f"{burg_name} was founded after a devastating storm.",
        f"{burg_name} rose on the ruins of ancient settlements.",
        f"{burg_name} is famous for its miraculous well.",
        f"Legend says {burg_name} was built overnight by faerie folk.",
        f"{burg_name} survived a rebellion in the Year of Soot."
    ]
    return random.choice(events)

def random_festival():
    festival_types = ['Harvest', 'Solstice', 'Remembrance', 'Lights', 'Trade']
    descriptors = ['Grand', 'Silent', 'Ancient', 'Day of', 'Festival of']
    days = ['Dawn', 'Lights', 'Plenty', 'Remembrance', 'Wellsprings']
    return f"{random.choice(descriptors)} {random.choice(random.choice([festival_types, days]))}"

def random_rulers():
    surnames = ["Ashfall", "Velora", "Silvervein", "Dorn", "Gleam"]
    titles = ["Lord", "Lady", "Baron", "Duke", "Chancellor"]
    firstnames = ["Gerin", "Mirala", "Edris", "Tharan", "Cyra"]
    return [f"{random.choice(titles)} {random.choice(firstnames)} {random.choice(surnames)}" for _ in range(random.randint(1, 3))]

def random_myth():
    subjects = ["Stag", "Well", "Spirit", "Oak", "Torrent", "Star"]
    adjectives = ["Silver", "Endless", "Hollow", "Sacred", "Lost"]
    legends = [
        "The {adj} {subj} guards the town's luck.",
        "{adj} {subj} appears every century.",
        "Only the worthy see the {adj} {subj} at dawn."
    ]
    myth = random.choice(legends).format(
        adj=random.choice(adjectives),
        subj=random.choice(subjects)
    )
    return myth

# Example for a burg:
def generate_burg_lore(burg_name):
    return {
        "history": random_history(burg_name),
        "festivals": [random_festival() for _ in range(random.randint(1, 2))],
        "rulers": random_rulers(),
        "myths": [random_myth() for _ in range(random.randint(1,2))]
    }