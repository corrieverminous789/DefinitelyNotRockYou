"""
DefinitelyNotRockYou - cracker.py
Try a generated wordlist against a password-protected ZIP file.

Supports standard ZipCrypto (via built-in zipfile). If pyzipper is installed,
AES-encrypted zips are also supported.

Only use this against files you own or are explicitly authorized to test.
"""

import zipfile

try:
    import pyzipper
    HAVE_PYZIPPER = True
except ImportError:
    HAVE_PYZIPPER = False


def crack_zip(zip_path, wordlist, progress_callback=None):
    """
    Attempt to crack a password-protected zip using the given wordlist.

    zip_path: path to the .zip file
    wordlist: list[str] or path to a wordlist file (one password per line)
    progress_callback: optional fn(index, total, current_word) called each attempt

    Returns: (found: bool, password: str|None, attempts: int)
    """
    if isinstance(wordlist, str):
        with open(wordlist, "r", encoding="utf-8", errors="ignore") as f:
            words = [line.rstrip("\n") for line in f if line.strip()]
    else:
        words = wordlist

    total = len(words)

    # Try built-in zipfile first (handles standard ZipCrypto)
    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile:
        return False, None, 0

    test_member = zf.namelist()[0] if zf.namelist() else None
    if test_member is None:
        return False, None, 0

    is_aes = False

    for i, word in enumerate(words):
        if progress_callback:
            progress_callback(i + 1, total, word)
        try:
            zf.extractall(pwd=word.encode("utf-8", errors="ignore"), members=[test_member])
            return True, word, i + 1
        except RuntimeError as e:
            if "Bad password" in str(e) or "password required" in str(e):
                continue
            elif "encryption method" in str(e).lower() or "not supported" in str(e).lower():
                is_aes = True
                break
        except (zipfile.BadZipFile, NotImplementedError):
            is_aes = True
            break
        except Exception:
            continue

    zf.close()

    # Fall back to pyzipper for AES-encrypted zips
    if is_aes:
        if not HAVE_PYZIPPER:
            raise RuntimeError(
                "This zip appears to use AES encryption. Install pyzipper "
                "(`pip install pyzipper`) to crack AES-encrypted zips."
            )
        with pyzipper.AESZipFile(zip_path) as azf:
            names = azf.namelist()
            if not names:
                return False, None, 0
            for i, word in enumerate(words):
                if progress_callback:
                    progress_callback(i + 1, total, word)
                try:
                    azf.extractall(pwd=word.encode("utf-8", errors="ignore"), members=[names[0]])
                    return True, word, i + 1
                except (RuntimeError, pyzipper.zipfile.BadZipFile):
                    continue
                except Exception:
                    continue

    return False, None, total
