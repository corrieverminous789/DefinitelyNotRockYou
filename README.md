<img width="1255" height="373" alt="not" src="https://github.com/user-attachments/assets/6e6516be-f56f-4565-898f-7197548e8153" />

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=55&duration=3000&pause=1000&color=FF0000&center=true&vCenter=true&width=900&lines=---DefinitelyNotRockYou---;---OSINT+Wordlist+Generator---" alt="DefinitelyNotRockYou" />
</p>

A CUPP-style (Common User Passwords Profiler) personalized wordlist generator
with a simple local web UI, plus a built-in zip-password tester.

## ⚠️ Responsible Use

**Use only on yourself, or on targets you have explicit written authorization
to test.** This is a red-team/OSINT-audit tool for password-hygiene research —
not a tool for accessing accounts, files, or systems that aren't yours.
Unauthorized use to crack or access data you don't own may be illegal in your
jurisdiction. You are solely responsible for how you use this software; see
[LICENSE](LICENSE) for the full disclaimer.

## What it does

1. You tell it what you know about the target (names, birthdate, pet name,
   favorite things, family names, etc.) — leave anything you don't know blank.
2. It generates a wordlist by applying common mangling rules: case changes,
   leetspeak, date/number/symbol suffixes, name combinations, reversals,
   doubling, etc.
3. You can download the wordlist, or immediately test it against a
   password-protected `.zip` file right in the same page.

## Installation

Requires Python 3.8+ and git.

```bash
git clone https://github.com/raivenLockdown/DefinitelyNotRockYou.git
cd DefinitelyNotRockYou
pip install -r requirements.txt
````

(`pyzipper` is optional but recommended — it lets the cracker also handle AES-encrypted zips, not just the older ZipCrypto format.)

## Running it

```bash
python app.py
```
<img width="1457" height="444" alt="image" src="https://github.com/user-attachments/assets/d2293258-a474-45b3-b3a3-0937a8f2d5d1" />

Then open **http://127.0.0.1:5000** in your browser. Everything runs locally — nothing is uploaded anywhere else.

<img width="1919" height="928" alt="image" src="https://github.com/user-attachments/assets/20ee0186-e1c6-42eb-929e-7229c7e70cea" />


## Step-by-step usage

The app gives you two ways to feed it a case file — pick whichever fits:

**Option A — Quick Form (recommended)**

1. Click the **Quick Form** tab on the page.
2. Expand whichever categories apply (Basics, Dates & Numbers, Family, etc.) and type values directly into the fields — no file needed.
3. Leave anything you don't know blank.

<img width="1152" height="648" alt="Untitled design" src="https://github.com/user-attachments/assets/acd6b593-7121-4dd2-82b0-9a7d92d87907" />

**Option B — Upload / Paste**

1. Open `osint_template.txt` in any text editor.
2. Fill in whatever fields you know about the target, one per line, e.g.:
    
    ```
    first_name: Juan pet_name: Pikachu birth_day: 5 birth_month: 2 birth_year: 1996
    ```
    
    Delete or leave blank anything you don't know — missing fields are fine, the generator just skips them.
3. Save the file, then in the web app upload it directly, or paste the same lines into the text box. Good for building up a profile over multiple sessions since it's just a text file you can keep editing.

<img width="1152" height="648" alt="Untitled design (1)" src="https://github.com/user-attachments/assets/abb6647f-53e9-434b-834d-e4f8cccc6a73" />

Either way, once you click **Generate the wordlist**:

4. You'll see a preview and a total count.
5. Click the download link to get the full `.txt` wordlist — usable with any other cracking tool too (John the Ripper, hashcat, fcrackzip, etc.), not just this one.
6. To test it against a zip: upload the `.zip` under "Put it to the test" and click **attempt crack**. It'll report the password if found, or how many attempts it tried if not.

## Using the wordlist elsewhere

The generated `dnry_wordlist.txt` is a plain newline-separated list, so it drops straight into other tools, e.g.:

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

- You can now pick a **wordlist size** on the page (Quick ~50k / Standard ~150k / Thorough ~400k / Maximum ~800k). Bigger sizes take a bit longer to generate but cover far more date/number/symbol combinations — useful when you have a lot of confirmed fields and want maximum coverage.
- Date handling is now much richer: if you provide birth_day and birth_year but _not_ birth_month, it still builds day+year combos (e.g. `25` + `1996` → `251996`), not just full DD+MM+YYYY combos. Filling in birth_day, birth_month, and birth_year as **separate fields** (rather than one combined date string) is what unlocks all of this.
- The generator can only mangle words you actually give it — it can't invent arbitrary misspellings on its own. If you know a target uses a specific nickname or misspelling (e.g. "Pickachu" instead of "Pikachu"), add it as an extra comma-separated value on the same field: `fav_character: Pikachu, Pickachu`
- Standard ZipCrypto zips are cracked with Python's built-in `zipfile`. AES zips need `pyzipper` installed.
- This is a profiling/wordlist tool, not a general-purpose password cracker — it won't help against strong, random passwords. It's meant to catch the common case of people using personal info as their password.

## License

MIT — see [LICENSE](https://claude.ai/chat/LICENSE). Free to use, modify, and distribute; provided "as is" with no warranty. Please read the **Responsible Use** note above before using this on anything other than your own accounts/files.
