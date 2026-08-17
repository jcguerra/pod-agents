"""
seed_niches.py — Load the niche taxonomy into Postgres (idempotent).
====================================================================
Source: "Cross-Niching Guide Book 2.0" (Hannah Ebeling). Five lists that get
cross-niched: holiday × career × family_relation × pet × hobby.

Run from the project root:
    ./venv/bin/python -m db.seed_niches

Re-runnable: uses ON CONFLICT (category, name, subcategory) DO NOTHING, so it
only inserts what is missing. Edit the lists below to grow the taxonomy.
"""

import psycopg
import config

# ---------------------------------------------------------------------------
# HOLIDAYS — (month, day_note, name)
# ---------------------------------------------------------------------------
HOLIDAYS = [
    (1, "1", "New Year's Day"), (1, "8", "Feast of the Epiphany"),
    (1, "varies", "Three Kings Day"), (1, "4", "Trivia Day"),
    (1, "5", "National Bird Day"), (1, "10", "Houseplant Appreciation Day"),
    (1, "16", "Martin Luther King's Birthday"), (1, "varies", "Chinese New Year"),
    (1, "25", "Opposite Day"), (1, "26", "Australia Day"),
    (2, "2", "Groundhog's Day"), (2, "3", "Feed the Birds Day"),
    (2, "12", "Lincoln's Birthday"), (2, "varies", "Super Bowl Sunday"),
    (2, "14", "Valentine's Day"), (2, "15", "Singles Awareness Day"),
    (2, "varies", "President's Day"), (2, "varies", "Mardi Gras (Fat Tuesday)"),
    (2, "varies", "Ash Wednesday"), (2, "22", "Washington's Birthday"),
    (3, "7", "Ides of March"), (3, "varies", "Purim"),
    (3, "8", "International Women's Day"), (3, "varies", "Oscar Night"),
    (3, "17", "St. Patrick's Day"), (3, "20", "International Earth Day"),
    (3, "20", "Spring Equinox"), (3, "varies", "Ramadan begins"),
    (3, "25", "Feast of the Annunciation"),
    (4, "1", "April Fool's Day"), (4, "1", "International Tatting Day"),
    (4, "varies", "Palm Sunday"), (4, "varies", "Passover"),
    (4, "varies", "Good Friday"), (4, "7", "National Walk to Work Day"),
    (4, "varies", "Easter Sunday"), (4, "15", "Income Taxes Due"),
    (4, "17", "Patriot's Day"), (4, "22", "Earth Day (U.S.)"),
    (4, "last Friday", "Arbor Day"),
    (5, "1", "May Day"), (5, "2", "National Teacher's Day"),
    (5, "4", "Star Wars Day"), (5, "5", "Cinco de Mayo"),
    (5, "varies", "Kentucky Derby"), (5, "8", "VE Day (WWII)"),
    (5, "2nd Sunday", "Mother's Day"), (5, "2nd Sunday", "Lilac Sunday"),
    (5, "22", "Armed Forces Day"), (5, "varies", "Victoria Day (Canada)"),
    (5, "last Monday", "Memorial Day"),
    (6, "26", "D-Day (WWII)"), (6, "14", "Flag Day"),
    (6, "3rd Sunday", "Father's Day"), (6, "19", "Juneteenth Day"),
    (6, "21", "Summer Solstice"), (6, "month", "Pride Month"),
    (7, "2", "Canada Day"), (7, "4", "Independence Day (USA)"),
    (7, "19", "National Hot Dog Day"), (7, "22", "Hammock Day"),
    (7, "varies", "Summer Olympics"), (7, "varies", "Summer Vacation"),
    (7, "varies", "Christmas in July"), (7, "month", "Parks & Rec Month"),
    (8, "1", "National Mountain Climbing Day"), (8, "3", "National Watermelon Day"),
    (8, "10", "National S'mores Day"), (8, "varies", "Summer Meteor Showers"),
    (8, "13", "Left Hander's Day"), (8, "14", "V-J Day"),
    (8, "28", "Stuffed Green Bell Peppers Day"), (8, "30", "National Marshmallow Toasting Day"),
    (8, "varies", "Back-to-School Season"),
    (9, "2", "VJ Day (WWII)"), (9, "1st Monday", "Labor Day"),
    (9, "11", "9/11 Remembrance"), (9, "10", "Grandparents Day"),
    (9, "varies", "Rosh Hashanah"), (9, "17", "Constitution Day"),
    (9, "16", "Oktoberfest begins"), (9, "21", "International Peace Day"),
    (9, "4th Friday", "Native American Day"), (9, "varies", "Autumnal Equinox"),
    (10, "1", "International Day for the Elderly"), (10, "varies", "Yom Kippur"),
    (10, "1st Friday", "World Smile Day"), (10, "2nd Monday", "Columbus / Indigenous People Day"),
    (10, "2nd Monday", "Thanksgiving Day (Canada)"), (10, "16", "Boss's Day"),
    (10, "3rd Saturday", "Sweetest Day"), (10, "24", "United Nations Day"),
    (10, "28", "Make a Difference Day"), (10, "31", "Halloween"),
    (11, "1", "All Saint's Day"), (11, "1-2", "Dia de los Muertos"),
    (11, "2", "All Soul's Day"), (11, "varies", "U.S. General Election Day"),
    (11, "11", "Veteran's Day"), (11, "13", "Caregiver Appreciation Day"),
    (11, "13", "Sadie Hawkins Day"), (11, "16", "Great American Smokeout"),
    (11, "20", "Universal Children's Day"), (11, "4th Thursday", "Thanksgiving Day"),
    (11, "day after Thanksgiving", "Black Friday"),
    (11, "Saturday after Thanksgiving", "Small Business Saturday"),
    (11, "Monday after Thanksgiving", "Cyber Monday"),
    (12, "varies", "Advent begins"), (12, "varies", "Chanukah"),
    (12, "7", "Pearl Harbor Day"), (12, "12", "Poinsettia Day"),
    (12, "21", "Winter Solstice"), (12, "25", "Christmas"),
    (12, "26", "Boxing Day"), (12, "26", "Kwanzaa"),
    (12, "27", "National Fruitcake Day"), (12, "31", "New Year's Eve"),
]

# ---------------------------------------------------------------------------
# CAREERS
# ---------------------------------------------------------------------------
CAREERS = [
    # Generic money keywords (not in the guide, but the strongest sellers).
    "Teacher", "Nurse",
    "Dentist", "Registered Nurse", "Pharmacist", "Computer Systems Analyst",
    "Physician", "Database Administrator", "Software Developer", "Physical Therapist",
    "Web Developer", "Dental Hygienist", "Occupational Therapist", "Veterinarian",
    "Computer Programmer", "School Psychologist", "Physical Therapist Assistant",
    "Interpreter & Translator", "Mechanical Engineer", "Veterinary Technician",
    "Epidemiologist", "IT Manager", "Market Research Analyst",
    "Diagnostic Medical Sonographer", "Computer Systems Admin", "Respiratory Therapist",
    "Medical Secretary", "Civil Engineer", "Substance Abuse Counselor",
    "Speech-Language Pathologist", "Landscaper & Groundskeeper", "Radiologic Technologist",
    "Cost Estimator", "Financial Advisor", "Marriage & Family Therapist",
    "Medical Assistant", "Lawyer", "Accountant", "Compliance Officer",
    "High School Teacher", "Clinical Laboratory Technician", "Maintenance & Repair Worker",
    "Bookkeeping, Accounting, & Audit Clerk", "Financial Manager",
    "Recreation & Fitness Worker", "Insurance Agent", "Elementary School Teacher",
    "Dental Assistant", "Management Analyst", "Home Health Aide", "Pharmacy Technician",
    "Construction Manager", "Public Relations Specialist", "Middle School Teacher",
    "Massage Therapist", "Paramedic", "Preschool Teacher", "Hairdresser",
    "Marketing Manager", "Patrol Officer", "School Counselor", "Executive Assistant",
    "Financial Analyst", "Personal Care Aide", "Clinical Social Worker",
    "Business Operations Manager", "Loan Officer", "Meeting, Convention & Event Planner",
    "Mental Health Counselor", "Nursing Aide", "Sales Representative", "Architect",
    "Sales Manager", "HR Specialist", "Plumber", "Real Estate Agent", "Glazier",
    "Art Director", "Customer Service Rep", "Logistician", "Auto Mechanic", "Bus Driver",
    "Restaurant Cook", "Child & Family Social Worker", "Administrative Assistant",
    "Receptionist", "Paralegal", "Cement Mason", "Painter", "Sports Coach",
    "Teacher Assistant", "Brickmason & Blockmason", "Cashier", "Janitor", "Electrician",
    "Delivery Truck Driver", "Maid & Housekeeper", "Carpenter", "Security Guard",
    "Construction Worker", "Fabricator", "Telemarketer",
]

# ---------------------------------------------------------------------------
# FAMILY RELATIONS — {subcategory: [names]}
# ---------------------------------------------------------------------------
FAMILY = {
    "mom_name": ["mother", "mommy", "mama", "momma", "mamma", "ma", "bonus mom",
                 "stepmother", "mom", "mum", "mamae"],
    "dad_name": ["father", "daddy", "papa", "pop", "pa", "poppa", "pater", "dad", "dada"],
    "grandfather_name": ["Papa", "Pop/Pop-Pop", "Pawpaw", "Granddad", "Papaw", "Grampy",
                         "Poppy", "Grandfather", "Abuelo/Abuelito", "Gramps"],
    "grandmother_name": ["Nana", "Grammy/Grammie", "Granny/Grannie", "Nanny", "Mamaw",
                         "Mawmaw", "Mimi", "Grandmother", "Memaw", "Abuela/Abuelita"],
    "other_family": ["Aunt", "Uncle", "Cousin", "Niece", "Nephew", "Brother", "Sister",
                     "Great Aunt", "Great Uncle"],
}

# ---------------------------------------------------------------------------
# PETS — {subcategory: [types]}
# ---------------------------------------------------------------------------
PETS = {
    "dog_breed": [
        "French Bulldogs", "Labrador Retrievers", "Golden Retrievers",
        "German Shepherd Dogs", "Poodles", "Bulldogs", "Rottweilers", "Beagles",
        "Dachshunds", "German Shorthaired Pointers", "Pembroke Welsh Corgis",
        "Australian Shepherds", "Yorkshire Terriers", "Cavalier King Charles Spaniels",
        "Doberman Pinschers", "Boxers", "Miniature Schnauzers", "Cane Corso",
        "Great Danes", "Shih Tzu", "Siberian Huskies", "Bernese Mountain Dogs",
        "Pomeranians", "Boston Terriers", "English Springer Spaniels",
        "Shetland Sheepdogs", "Brittanys", "Cocker Spaniels", "Border Collies",
        "Miniature American Shepherds", "Belgian Malinois", "Vizslas", "Chihuahuas",
        "Pugs", "Basset Hounds", "Mastiffs", "Maltese", "Collies",
        "English Cocker Spaniels", "Rhodesian Ridgebacks", "Newfoundlands", "Shiba Inu",
        "Weimaraners", "West Highland White Terriers", "Portuguese Water Dogs",
        "Bichons Frises", "Australian Cattle Dogs", "Dalmatians", "Bloodhounds", "Havanese",
    ],
    "cat_breed": ["Ragdoll", "Maine Coon", "Exotic Short Hair", "Devon Rex", "Persian",
                  "British Short Hair", "Abyssinian", "American Short Hair",
                  "Scottish Fold", "Sphynx"],
    "other_pet": [
        # Generic money keywords ("Dog Mom", "Cat Dad" are top sellers).
        "Dog", "Cat",
        "Ferret", "Iguana", "Guinea Pig", "Hamster", "Gerbil", "Parakeet", "Macaw",
        "Parrot", "Song Bird", "Rat", "Mouse", "Fish", "Ball Python", "Corn Snake",
        "Flying Squirrel", "Turtle", "Tortoise", "Hedgehog", "Chicken", "Lizard",
        "Rabbit", "Hare", "Fennec Fox", "Axolotl", "Tarantula", "Capybara", "Chinchilla",
        "Squirrel", "Deer", "Hermit Crab", "Sea Star", "Bearded Dragon", "Bengal Cat",
        "Fox", "Sugar Glider", "Squirrel Monkey",
    ],
}

# ---------------------------------------------------------------------------
# HOBBIES
# ---------------------------------------------------------------------------
HOBBIES = [
    "Reading", "Writing", "Painting", "Drawing", "Photography", "Gardening", "Cooking",
    "Baking", "Playing an instrument", "Singing", "Dancing", "Knitting", "Sewing",
    "Crocheting", "Pottery", "Sculpting", "Woodworking", "DIY crafts", "Scrapbooking",
    "Calligraphy", "Origami", "Hiking", "Camping", "Cycling", "Running", "Swimming",
    "Yoga", "Pilates", "Martial arts", "Chess", "Board games", "Video gaming",
    "Collecting stamps", "Coin collecting", "Comic book collecting", "Antiquing",
    "Birdwatching", "Fishing", "Hunting", "Geocaching", "Model building", "Home brewing",
    "Wine tasting", "Beer tasting", "Traveling", "Exploring new cuisines",
    "Learning a new language", "Writing poetry", "Playing sports", "Volunteering",
    "Meditation", "Astronomy", "Bird-keeping", "Beekeeping", "Chessboxing",
    "Stand-up comedy", "Filmmaking", "Cosplaying", "Magic tricks", "Archery",
    "Rock climbing", "Scuba diving", "Surfing", "Skydiving", "Paragliding",
    "Bungee jumping", "Horseback riding", "Wine making", "Kayaking",
    "Home improvement/DIY", "Genealogy (Family history)", "Coin flipping",
    "Puzzle solving", "Soapmaking", "Candle making", "Collecting vinyl records",
    "Creative writing", "Stand-up paddleboarding", "Brewing kombucha", "Urban gardening",
    "Mountain biking", "Learning and practicing magic", "Geology and rock collecting",
    "Model rocketry", "Playing tabletop role-playing games", "Essential Oils", "Resin Art",
]


# ---------------------------------------------------------------------------
# POPULARITY — curated "money" items per category. Higher = better seller.
# Everything else defaults to 0. Used to rank cross-niching suggestions.
# ---------------------------------------------------------------------------
POPULAR = {
    "holiday": {
        "Christmas": 3, "Halloween": 3,
        "Valentine's Day": 2, "Mother's Day": 2, "Father's Day": 2,
        "Thanksgiving Day": 2, "Easter Sunday": 2, "New Year's Day": 2,
        "St. Patrick's Day": 2, "Independence Day (USA)": 2, "Cinco de Mayo": 2,
        "Back-to-School Season": 2, "Dia de los Muertos": 2,
    },
    "career": {
        "Teacher": 3, "Nurse": 3, "Registered Nurse": 2,
        "Elementary School Teacher": 2, "High School Teacher": 2,
        "Middle School Teacher": 2, "Preschool Teacher": 2, "Dentist": 2,
        "Veterinarian": 2, "Hairdresser": 2, "Accountant": 2, "Physician": 2,
        "Nursing Aide": 2, "Paramedic": 2, "Massage Therapist": 2,
        "Real Estate Agent": 2,
    },
    "family_relation": {
        "mom": 3, "mama": 2, "mommy": 2, "mum": 2, "dad": 3, "daddy": 2,
        "papa": 2, "pop": 2, "Nana": 2, "Grandmother": 2, "Grandfather": 2,
        "Grammy/Grammie": 2, "Aunt": 2, "Uncle": 2,
    },
    "pet": {
        "Dog": 3, "Cat": 3, "French Bulldogs": 2, "Labrador Retrievers": 2,
        "Golden Retrievers": 2, "German Shepherd Dogs": 2, "Dachshunds": 2,
        "Chihuahuas": 2, "Pugs": 2, "Pembroke Welsh Corgis": 2, "Poodles": 2,
        "Ragdoll": 2, "Maine Coon": 2,
    },
    "hobby": {
        "Gardening": 2, "Fishing": 2, "Hunting": 2, "Camping": 2, "Reading": 2,
        "Cooking": 2, "Baking": 2, "Yoga": 2, "Running": 2, "Hiking": 2,
        "Video gaming": 2, "Photography": 2,
    },
}


def _popularity(category, name):
    return POPULAR.get(category, {}).get(name, 0)


def _seasonality(month):
    if month in (10, 11, 12):
        return "Q4"
    if month in (6, 7, 8):
        return "summer"
    if month in (3, 4, 5):
        return "spring"
    return "winter"


def _rows():
    """Yield (category, name, subcategory, month, day_note, seasonality) tuples."""
    for month, day_note, name in HOLIDAYS:
        yield ("holiday", name, "", month, day_note, _seasonality(month))
    for name in CAREERS:
        yield ("career", name, "", None, None, None)
    for sub, names in FAMILY.items():
        for name in names:
            yield ("family_relation", name, sub, None, None, None)
    for sub, names in PETS.items():
        for name in names:
            yield ("pet", name, sub, None, None, None)
    for name in HOBBIES:
        yield ("hobby", name, "", None, None, None)


def seed():
    rows = list(_rows())
    inserted = 0
    with psycopg.connect(config.DATABASE_URL) as conn, conn.cursor() as cur:
        for category, name, sub, month, day_note, seasonality in rows:
            cur.execute(
                "INSERT INTO niche_items (category, name, subcategory, month, day_note, seasonality, popularity) "
                "VALUES (%s::niche_category, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (category, name, subcategory) DO UPDATE SET popularity = EXCLUDED.popularity",
                (category, name, sub, month, day_note, seasonality, _popularity(category, name)),
            )
            inserted += cur.rowcount
        conn.commit()
        cur.execute("SELECT category, count(*) FROM niche_items GROUP BY category ORDER BY category")
        counts = cur.fetchall()
    print(f"Seed done: {inserted} new row(s) inserted (of {len(rows)} candidates).")
    for category, n in counts:
        print(f"  {category:<16} {n}")


if __name__ == "__main__":
    seed()
