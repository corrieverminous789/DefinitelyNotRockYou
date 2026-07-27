# DefinitelyNotRockYou

A CUPP-style (Common User Passwords Profiler) personalized wordlist generator
with a simple local web UI, plus a built-in zip-password tester.

**Use only on yourself or targets you have explicit written authorization to
test.** This is a red-team/OSINT-audit tool, not a tool for accessing accounts
or files that aren't yours.

## What it does

1. You fill out `osint_template.txt` with whatever personal info you've
   gathered on a target (names, birthdate, pet name, favorite things, family
   names, etc.) — leave anything you don't know blank.
2. Upload that file (or paste the same `field: value` lines) into the local
   web app.
3. It generates a wordlist by applying common mangling rules: case changes,
   leetspeak, date/number/symbol suffixes, name combinations, reversals,
   doubling, etc.
4. You can download the wordlist, or immediately test it against a
   password-protected `.zip` file right in the same page.

## Setup (one-time)

Requires Python 3.8+.

```bash
pip install -r requirements.txt
```

(`pyzipper` is optional but recommended — it lets the cracker also handle
AES-encrypted zips, not just the older ZipCrypto format.)

## Running it

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. Everything runs
locally — nothing is uploaded anywhere else.

## Step-by-step usage

The app gives you two ways to feed it a case file — pick whichever fits:

**Option A — Upload / Paste (recommended)**
1. Open `osint_template.txt` in any text editor.
2. Fill in whatever fields you know about the target, one per line, e.g.:
   ```
   first_name: Juan
   pet_name: Bantay
   birth_year: 1999
   ```
   Delete or leave blank anything you don't know — missing fields are fine,
   the generator just skips them.
3. Save the file, then in the web app upload it directly, or paste the same
   lines into the text box. This is the most thorough option and is easiest
   to build up over multiple sessions (it's just a text file you can keep
   editing).

**Option B — Quick Form**
1. Click the **Quick Form** tab on the page.
2. Expand whichever categories apply (Basics, Dates & Numbers, Family, etc.)
   and type values directly into the fields — no file needed.
3. Leave anything you don't know blank.

Either way, once you click **Generate the wordlist**:

4. You'll see a preview and a total count.
5. Click the download link to get the full `.txt` wordlist — usable with any
   other cracking tool too (John the Ripper, hashcat, fcrackzip, etc.), not
   just this one.
6. To test it against a zip: upload the `.zip` under "Put it to the test" and
   click **attempt crack**. It'll report the password if found, or how many
   attempts it tried if not.

## Using the wordlist elsewhere

The generated `dnry_wordlist.txt` is a plain newline-separated list, so it
drops straight into other tools, e.g.:

```bash
# John the Ripper style
zip2john target.zip > hash.txt
john --wordlist=dnry_wordlist.txt hash.txt

# fcrackzip
fcrackzip -D -p dnry_wordlist.txt -u target.zip
```

## Project structure

```
DefinitelyNotRockYou/
├── app.py               # Flask web app (the UI)
├── generator.py         # wordlist generation engine
├── cracker.py           # zip-cracking logic
├── osint_template.txt   # fillable OSINT data collection form
├── templates/
│   └── index.html       # web UI page
└── requirements.txt
```

## Notes / limitations

- You can now pick a **wordlist size** on the page (Quick ~50k / Standard ~150k
  / Thorough ~400k / Maximum ~800k). Bigger sizes take a bit longer to
  generate but cover far more date/number/symbol combinations — useful when
  you have a lot of confirmed fields and want maximum coverage.
- Date handling is now much richer: if you provide birth_day and birth_year
  but *not* birth_month, it still builds day+year combos (e.g. `25` + `1996`
  → `251996`), not just full DD+MM+YYYY combos. Filling in birth_day,
  birth_month, and birth_year as **separate fields** (rather than one
  combined date string) is what unlocks all of this.
- The generator can only mangle words you actually give it — it can't invent
  arbitrary misspellings on its own. If you know a target uses a specific
  nickname or misspelling (e.g. "Pickachu" instead of "Pikachu"), add it as
  an extra comma-separated value on the same field:
  `fav_character: Pikachu, Pickachu`
- Standard ZipCrypto zips are cracked with Python's built-in `zipfile`. AES
  zips need `pyzipper` installed.
- This is a profiling/wordlist tool, not a general-purpose password cracker —
  it won't help against strong, random passwords. It's meant to catch the
  common case of people using personal info as their password.
