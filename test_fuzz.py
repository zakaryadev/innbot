from thefuzz import fuzz
from thefuzz import process

choices = {
    1: "Qaraqalpaqstan Respublikasi Dosliq orayi",
    2: "Nukus shahar markazi",
    3: "Dosliq MFY",
    4: "Respublika o'smirlar dispanseri"
}

query = "dslq"

best = process.extract(query, choices, limit=3, scorer=fuzz.WRatio)
print("WRatio:", best)

best2 = process.extract(query, choices, limit=3, scorer=fuzz.partial_ratio)
print("partial_ratio:", best2)

best3 = process.extract(query, choices, limit=3, scorer=fuzz.token_set_ratio)
print("token_set_ratio:", best3)
