"""Word rules for the bread roll study.

Each word has a whole-word pattern (letters may not touch either side) and a list of exclusion
rules. Every exclusion has a short reason that is written to data/roll_word_matches.csv, so a
reader can see why a name was dropped. The rules were written after reading every match for the
rarer words and large samples for the commoner ones (see code/02_audit.py).

classify(name) returns a list of (word, kept, reason) tuples, one per word found in the name.
"""
import re

B = r"(?<![a-z])"   # no letter before
E = r"(?![a-z])"    # no letter after

# word id: (label, pattern)
WORDS = {
    "roll": ("roll", r"rolls?"),
    "bap": ("bap", r"baps?"),
    "cob": ("cob", r"cobs?"),
    "batch": ("batch", r"batch(?:es)?"),
    "barm": ("barm", r"barms?"),
    "ovenbottom": ("oven bottom", r"oven ?bottoms?"),
    "stottie": ("stottie", r"stott(?:ie|ies|y)"),
    "breadcake": ("breadcake", r"bread ?cakes?"),
    "scuffler": ("scuffler", r"scufflers?"),
    "teacake": ("teacake", r"tea ?cakes?"),
    "bun": ("bun", r"buns?"),
    "buttery": ("buttery / rowie", r"butter(?:y|ies)|rowies?"),
    "blaa": ("blaa", r"blaas?"),
    "butty": ("butty", r"butt(?:y|ie|ies|ys)"),
    "sarnie": ("sarnie", r"sarn(?:ie|ies|y|ey|eys)"),
    "sandwich": ("sandwich", r"sandwich(?:es)?"),
    "piece": ("piece", r"pieces?"),
    "crusty": ("crusty", r"crusty"),
}
RX = {k: re.compile(B + p + E, re.I) for k, (_, p) in WORDS.items()}

# Groups used in the analysis
ROLL_WORDS = ["roll", "bap", "cob", "batch", "barm", "ovenbottom", "stottie", "breadcake", "scuffler"]
SANDWICH_WORDS = ["butty", "sarnie", "sandwich", "piece"]
OTHER_WORDS = ["bun", "teacake", "buttery", "blaa", "crusty"]

ASIAN = r"liangji|nara roll|seoul|fusion|kolkata|sushi|hand ?rolls?|spring ?rolls?|egg ?rolls?|summer ?rolls?|rice|noodle|maki|california|wok|pok[ei]e?|bao|tokyo|thai|chinese|oriental|vietnam|viet|japan|korea|kimbap|dim sum|lumpia|pho"
INDIAN = r"kati|kathi|desi|tikka|masala|bombay|indian|naan|paratha|frankie|dosa|spice|curry|shawarma|kebab|doner|gyros?|falafel|pyala"
PASTRY = r"sausage ?rolls?|swiss ?rolls?|cinnamon ?rolls?|jam ?roll|arctic ?roll|cinnabon|pastry|pasties"
ICE = r"ice ?cream|gelato|glaze|glacier|rolled|roll['’]d|frozen|bubble"
PUN_ROCK = r"(?:rock|wok|wrap|rattle|shake|rocket|loch|grind|glaze|pokie|poke|sushi|rice|rollin)['’]?\s*(?:n|and|&|'n'|’n’|'n|n'|’n|n’|\?n\?)\s*rolls?"

RULES = {
    "roll": [
        (PUN_ROCK, "rock and roll pun"),
        (r"rock ?(?:n|and|&|'n'|’n’)? ?rolls?|rattle|roll ?call", "rock and roll or other non-bread sense"),
        (r"rolls?[ -]?royce|rolls crescent|tiger roll|rolls of monmouth|dice|rack ?['’]?n['’]? ?roll|riff|ruck|rocky", "name, place, game or brand, not bread"),
        (r"ice rolls?|cone|choc|roll cake|sweet rolls|jelly roll|waffle|latte|acai|bowl ?(?:&|and|n) ?roll|roll ?(?:&|and|'n'|n) ?bowl|bowls & rolls", "ice cream, sweet roll or bowl food"),
        (ASIAN, "Asian roll dish or rice/noodle context"),
        (INDIAN, "wrap, kebab or South Asian roll"),
        (PASTRY, "pastry roll, not a bread roll"),
        (ICE, "ice cream or rolled dessert"),
        (r"roll[- ]?(?:on|up|out|over)\b|roller|rolling", "verb sense (roll on, roll up)"),
        (r"lobster|crab", "seafood roll in the American style"),
    ],
    "bap": [
        (r"baps (?:shri|shree)|swaminarayan|mandir", "BAPS Hindu organisation"),
        (r"kim[- ]?bap|(?<![a-z&])k\.\s?bap|kbap|korea|bibim|^on bap", "Korean bap (rice)"),
        (r"boom bap", "boom bap (a hip hop style)"),
    ],
    "cob": [
        (r"corn on the cob|on the cob", "corn on the cob"),
        (r"coloured cob|trek|horse|equestrian|riding", "cob as a horse"),
        (r"pen y cob|cob (?:and|&) pen|['’]r cob", "place or pub name (swan, Welsh embankment)"),
        (r"^cob,|(?<![a-z])y cob|animal feed", "abbreviation, Welsh place or animal feed"),
        (r"cob stays|cob cottage|cob barn|cob house|daycare|nursery|childcare", "building or childcare, not bread"),
    ],
    "barm": [],
    "batch": [],   # handled by a positive rule below
    "piece": [],   # handled by a positive rule below
    "stottie": [],
    "breadcake": [],
    "ovenbottom": [],
    "scuffler": [],
    "teacake": [],
    "bun": [
        (r"bun (?:bo|cha|thit|rieu|hue|bun)(?![a-z])|pho(?![a-z])|viet", "Vietnamese bun noodles"),
        (r"bun[- ]?sgoil", "Gaelic bun-sgoil (primary school)"),
        (r"bao|dim sum|chinese|hong kong|steamed", "Chinese steamed bun"),
    ],
    "buttery": [
        (r"college|school|university|hospital|volunteer|uppingham", "institutional buttery (provisions room)"),
        (r"rowie's pizza|zdrowie", "a name, not an Aberdeen rowie"),
    ],
    "blaa": [(r"bla blaa", "'bla bla' pun, not a Waterford blaa")],
    "butty": [],
    "sarnie": [],
    "sandwich": [
        (r"sandwich (?:bay|road|rd|golf|rugby|football|cricket|sailing|town|technology|tech|industrial|discovery|guildhall|bowls|bowling|masonic|market|convenience|grazing|haven|marina|lodge|leisure|sports|carnival|quay)|(?:kfc|spar|namaste|age concern) sandwich", "Sandwich, the town in Kent"),
        (r"subway(?![a-z])", "Subway chain (a brand name, not a local choice)"),
        (r"ice ?cream sandwich|cookie sandwich", "dessert sandwich"),
    ],
    "crusty": [],
}

# Positive rules: these words are only counted when the name uses them as food words.
BATCH_OK = re.compile(B + r"batch(?:es)? ?(?:bar|hatch|shop|van|stop|cabin|butty|butties|wagon|hut|box|cob|stall)" + E +
                      r"|" + B + r"(?:hot|filled|bacon|barm|cob|bap|roll)s? (?:and|&|n) batch(?:es)?" + E, re.I)
PIECE_OK = re.compile(B + r"(?:jeely|jammy|jelly) pieces?" + E + r"|" + B + r"pieces? ?(?:box|shop|bar|van|stop|cabin|hut|piece)" + E +
                      r"|" + B + r"braw pieces?" + E + r"|gie['’]?s (?:a |yer )?piece|^(?:the )?pieces?$", re.I)
PIECE_NO = re.compile(r"mssng|missing|pieces? o[f']?\b|piece ['‘’]?a['’]? |bits ?(?:n|and|&|'n'|’n’) ?pieces|pieces of eight|peace by piece|side piece|pizza pieces|mill piece|play pieces|foxes piece", re.I)


def classify(name):
    """Return [(word, kept, reason)] for every word id whose pattern appears in name."""
    out = []
    if not name:
        return out
    low = name.lower()
    for w, rx in RX.items():
        if not rx.search(low):
            continue
        # avoid double counting: "morning roll", "barm cake" etc. are fine; "bread cake" is not also "cake".
        if w == "teacake" and re.search(r"(?<![a-z])(?:a|piece of|cream|chocolate|mallow)\s+tea ?cakes?", low):
            pass
        if w == "batch":
            if BATCH_OK.search(low):
                out.append((w, True, ""))
            else:
                out.append((w, False, "batch not used as a bread word (small batch, batch cooking, brewing)"))
            continue
        if w == "piece":
            if PIECE_OK.search(low) and not PIECE_NO.search(low):
                out.append((w, True, ""))
            else:
                out.append((w, False, "piece not used as a sandwich word (piece of cake etc.)"))
            continue
        reason = ""
        for pat, why in RULES.get(w, []):
            if re.search(pat, low):
                reason = why
                break
        out.append((w, reason == "", reason))
    return out


if __name__ == "__main__":
    for t in ["Wok n Roll", "The Roll Shop", "Cobs & Robbers", "Corn on the Cob", "BAPS Shri Swaminarayan Mandir",
              "Deans Batch Hatch", "Small Batch Coffee", "A Piece of Cake", "Jeely Piece Pre 5 Unit", "Piece",
              "Sandwich Bay Golf Club", "Subway Sandwiches", "The Sandwich Bar", "Bun Bun Pho", "Pyala Kebab Roll"]:
        print(t, classify(t))
