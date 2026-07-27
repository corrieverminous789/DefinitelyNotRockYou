"""
DefinitelyNotRockYou - generator.py
Core wordlist generation engine.

Takes parsed OSINT fields (dict of field_name -> value/list of values) and
produces a de-duplicated password wordlist using common personal-info
mangling rules (case changes, leetspeak, appended dates/numbers, symbol
suffixes, name combos, reversals, etc.)

Use only on data you are authorized to test against.
"""

import itertools
import re

LEET_MAP = {
    "a": ["a", "4", "@"],
    "e": ["e", "3"],
    "i": ["i", "1", "!"],
    "o": ["o", "0"],
    "s": ["s", "5", "$"],
    "t": ["t", "7"],
}

COMMON_SUFFIX_NUMBERS = [
    "1", "12", "123", "1234", "12345", "01", "007", "143", "777", "69",
    "420", "00", "99", "88", "0", "10", "11", "22", "111", "222", "2024",
    "2025", "2026",
]
COMMON_SUFFIX_SYMBOLS = ["!", "@", "#", "$", "_", ".", "*", "?"]
COMMON_PREFIX_SYMBOLS = ["!", "@", "#", "_"]


# Field groups used to render the quick-fill form AND to parse it back into
# the same field format the txt template produces. (label, hint, [(key, placeholder), ...])
FIELD_GROUPS = [
    ("The Basics", "Who are we even talking about?", [
        ("first_name", "e.g. Juan"),
        ("second_first_name", "e.g. Carlos (if they have two given names)"),
        ("middle_name", "e.g. Dela"),
        ("last_name", "e.g. Cruz"),
        ("nickname", "e.g. Jhun-jhun"),
        ("maiden_name", "if applicable"),
        ("ign", "in-game name / gamertag"),
    ]),
    ("Dates & Numbers", "Birthdays are the #1 password ingredient.", [
        ("birth_day", "e.g. 14"),
        ("birth_month", "e.g. 7"),
        ("birth_year", "e.g. 1999"),
        ("anniversary_date", "e.g. 2020-06-12"),
        ("grad_year", "e.g. 2026"),
        ("fav_number", "e.g. 7"),
        ("lucky_number", "e.g. 3"),
        ("age", "if birthdate unknown"),
    ]),
    ("Likes & Favorites", "The stuff they'd never get tired of.", [
        ("fav_color", "e.g. blue"),
        ("fav_movie", ""),
        ("fav_game", ""),
        ("fav_food", ""),
        ("fav_character", ""),
        ("fav_song", ""),
        ("fav_team", ""),
        ("fav_show", ""),
    ]),
    ("Pets", "Never underestimate a pet's name.", [
        ("pet_name", "current pet"),
        ("past_pet_name", "childhood pet"),
    ]),
    ("Parents", "", [
        ("mother_first_name", ""),
        ("mother_middle_name", ""),
        ("mother_last_name", ""),
        ("father_first_name", ""),
        ("father_middle_name", ""),
        ("father_last_name", ""),
    ]),
    ("Siblings & Partner", "", [
        ("brother_name", ""),
        ("sister_name", ""),
        ("partner_name", "boyfriend/girlfriend"),
        ("spouse_name", "husband/wife"),
        ("ex_partner_name", ""),
    ]),
    ("Kids & Extended Family", "", [
        ("son_name", ""),
        ("daughter_name", ""),
        ("grandchild_name", ""),
        ("nephew_niece_name", ""),
    ]),
    ("Places", "", [
        ("hometown", ""),
        ("current_city", ""),
        ("street_name", ""),
        ("school_name", ""),
    ]),
    ("Work & Online Life", "", [
        ("company_name", ""),
        ("job_title", ""),
        ("gamertag", ""),
        ("clan_or_guild", ""),
        ("old_username", ""),
    ]),
    ("Loose Ends", "Anything else that could sneak into a password.", [
        ("phone_last_digits", "last 4 digits"),
        ("plate_number", ""),
        ("wifi_ssid", ""),
        ("security_question_answer", "e.g. first school, first car"),
    ]),
]


def all_field_keys():
    """Flat list of every field key defined in FIELD_GROUPS, in order."""
    keys = []
    for _, _, group_fields in FIELD_GROUPS:
        for key, _ in group_fields:
            keys.append(key)
    return keys


def fields_from_form(form_dict):
    """Build the standard fields dict directly from a quick-form submission
    (e.g. Flask's request.form), skipping anything left blank."""
    fields = {}
    for key in all_field_keys():
        value = (form_dict.get(key) or "").strip()
        if value:
            values = [v.strip() for v in value.split(",") if v.strip()]
            if values:
                fields[key] = values
    return fields


def parse_osint_file(path_or_lines):
    """Parse the OSINT txt template into a dict of field -> list[str] values.
    Accepts either a filepath (str) or an iterable of lines."""
    if isinstance(path_or_lines, str):
        with open(path_or_lines, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = path_or_lines

    fields = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            continue
        values = [v.strip() for v in value.split(",") if v.strip()]
        if values:
            fields[key] = values
    return fields


def _leet_variants(word, max_variants=6):
    """Generate a handful of leetspeak variants for a word (capped to avoid
    combinatorial explosion)."""
    variants = {word}
    lowered = word.lower()
    chars = list(lowered)
    swap_positions = [i for i, c in enumerate(chars) if c in LEET_MAP]

    count = 0
    for i in swap_positions:
        if count >= max_variants:
            break
        for repl in LEET_MAP[chars[i]][1:]:
            new_chars = chars.copy()
            new_chars[i] = repl
            variants.add("".join(new_chars))
            count += 1
            if count >= max_variants:
                break
    return variants


def _case_variants(word):
    return {
        word.lower(),
        word.upper(),
        word.capitalize(),
        word[:-1] + word[-1].upper() if len(word) > 1 else word.upper(),
    }


def _base_words(fields):
    """Flatten all field values into a deduplicated list of base words."""
    words = set()
    for values in fields.values():
        for v in values:
            v = v.strip()
            if v and len(v) <= 30:
                words.add(v)
    return list(words)


def _date_tokens(fields):
    """Build likely date-based tokens from birth_day/month/year, and
    anniversary/grad_year etc. Generates every standalone combo (day+year,
    month+year, day+month, all three, in multiple orders) rather than only
    firing when all three fields are present."""
    tokens = set()

    day = fields.get("birth_day", [""])[0].strip()
    month = fields.get("birth_month", [""])[0].strip()
    year = fields.get("birth_year", [""])[0].strip()

    d = day.zfill(2) if day else ""
    m = month.zfill(2) if month else ""

    if day:
        tokens.add(day)
        tokens.add(d)
    if month:
        tokens.add(month)
        tokens.add(m)
    if year:
        tokens.add(year)
        if len(year) == 4:
            yy = year[2:]
            tokens.add(yy)

            # day + year (both orders, both raw and zero-padded day)
            if day:
                tokens.add(day + year)
                tokens.add(year + day)
                tokens.add(d + year)
                tokens.add(year + d)
                tokens.add(day + yy)
                tokens.add(yy + day)
                tokens.add(d + yy)
                tokens.add(yy + d)

            # month + year (both orders)
            if month:
                tokens.add(month + year)
                tokens.add(year + month)
                tokens.add(m + year)
                tokens.add(year + m)
                tokens.add(month + yy)
                tokens.add(yy + month)
                tokens.add(m + yy)
                tokens.add(yy + m)

    # day + month (both orders) regardless of year
    if day and month:
        tokens.add(d + m)
        tokens.add(m + d)
        tokens.add(day + month)
        tokens.add(month + day)
        if year:
            # zero-padded day/month + year
            tokens.add(d + m + year)
            tokens.add(m + d + year)
            tokens.add(year + m + d)
            tokens.add(year + d + m)
            # RAW (non-zero-padded) day/month + year - e.g. month=2, day=5,
            # year=1996 -> "251996" (this is the common "2/5/1996" style)
            tokens.add(day + month + year)
            tokens.add(month + day + year)
            tokens.add(year + month + day)
            tokens.add(year + day + month)
            if len(year) == 4:
                yy = year[2:]
                tokens.add(d + m + yy)
                tokens.add(m + d + yy)
                tokens.add(yy + m + d)
                tokens.add(yy + d + m)
                tokens.add(day + month + yy)
                tokens.add(month + day + yy)
                tokens.add(yy + month + day)
                tokens.add(yy + day + month)

    # other date-ish fields: pull all digits out and use as a token
    for other_key in ("anniversary_date", "grad_year", "age"):
        if other_key in fields:
            raw = fields[other_key][0]
            digits = re.sub(r"[^0-9]", "", raw)
            if digits:
                tokens.add(digits)
                tokens.add(raw.strip())

    # drop empties
    return {t for t in tokens if t}


def _extra_number_tokens(fields):
    """Pull additional standalone numeric tokens worth using as suffixes:
    favorite/lucky numbers, phone digits, plate numbers, etc."""
    tokens = set()
    for key in ("fav_number", "lucky_number", "phone_last_digits", "plate_number"):
        if key in fields:
            for v in fields[key]:
                digits = re.sub(r"[^0-9]", "", v)
                if digits:
                    tokens.add(digits)
    return tokens


def generate_wordlist(fields, max_size=150000, combine_pairs=True, use_leet=True):
    """
    Generate a wordlist (list[str]) from parsed OSINT fields.

    fields: dict from parse_osint_file()
    max_size: soft cap on output size (higher-priority combos are kept first
        if the raw generation exceeds this)
    combine_pairs: whether to combine two base words together (e.g. name+pet)
    use_leet: whether to include leetspeak substitutions

    Tips for better coverage:
    - Add known nicknames/misspellings as extra comma-separated values on the
      same field (e.g. "fav_character: Pikachu, Pickachu") - the generator
      can only mangle words you actually give it, it can't invent arbitrary
      misspellings on its own.
    - Fill in birth_day/birth_month/birth_year separately rather than
      lumping them into one field - that's what unlocks all the day+year,
      month+year, and full-date combinations.
    """
    base_words = _base_words(fields)
    date_tokens = _date_tokens(fields)
    number_tokens = _extra_number_tokens(fields)
    all_suffix_tokens = set(date_tokens) | set(number_tokens) | set(COMMON_SUFFIX_NUMBERS)

    # tiered sets so truncation (if needed) drops the least-likely stuff first
    tier1 = set()  # single words, plain case variants - always keep
    tier2 = set()  # single words + date/number/symbol suffixes, leet variants
    tier3 = set()  # two-word combinations, doubled words, reversed, extras

    # ---- Tier 1: plain case variants of every base word ----
    expanded_singles = set()
    for w in base_words:
        for cw in _case_variants(w):
            expanded_singles.add(cw)
            tier1.add(cw)

    # ---- Tier 2: leet variants + full suffix/prefix coverage ----
    if use_leet:
        for w in base_words:
            for lw in _leet_variants(w):
                expanded_singles.add(lw)
                tier2.add(lw)

    for w in expanded_singles:
        for suf in all_suffix_tokens:
            tier2.add(w + suf)
        for sym in COMMON_SUFFIX_SYMBOLS:
            tier2.add(w + sym)
            for suf in all_suffix_tokens:
                tier2.add(w + suf + sym)
        for sym in COMMON_PREFIX_SYMBOLS:
            tier2.add(sym + w)
            for suf in all_suffix_tokens:
                tier2.add(sym + w + suf)

    # ---- Tier 3: reversed, doubled, two-word combos ----
    for w in base_words:
        tier3.add(w[::-1])
        tier3.add(w + w)
        tier3.add(w + "." + w)
        tier3.add(w + "_" + w)
        for suf in all_suffix_tokens:
            tier3.add(w[::-1] + suf)

    if combine_pairs and len(base_words) > 1:
        for w1, w2 in itertools.permutations(base_words, 2):
            combo = w1 + w2
            tier3.add(combo)
            tier3.add(combo.lower())
            tier3.add(combo.capitalize())
            tier3.add(w1 + "." + w2)
            tier3.add(w1 + "_" + w2)
            for suf in all_suffix_tokens:
                tier3.add(combo + suf)
                tier3.add(combo.capitalize() + suf)
            for sym in COMMON_SUFFIX_SYMBOLS:
                tier3.add(combo + sym)

    # ---- Assemble, respecting priority order under the cap ----
    def _clean(bucket):
        return {w for w in bucket if w and 3 <= len(w) <= 40}

    tier1 = _clean(tier1)
    tier2 = _clean(tier2) - tier1
    tier3 = _clean(tier3) - tier1 - tier2

    ordered = sorted(tier1) + sorted(tier2) + sorted(tier3)

    if len(ordered) > max_size:
        ordered = ordered[:max_size]

    # final dedupe while preserving priority order, then sort for readability
    seen = set()
    final = []
    for w in ordered:
        if w not in seen:
            seen.add(w)
            final.append(w)

    return sorted(final)


def generate_and_save(fields, output_path, **kwargs):
    wordlist = generate_wordlist(fields, **kwargs)
    with open(output_path, "w", encoding="utf-8") as f:
        for w in wordlist:
            f.write(w + "\n")
    return len(wordlist)
