# -----------------------------
# Caesar+ Tool (with ROT13 & brute force)
# -----------------------------
# This program provides:
#  - A pure Caesar function that shifts only A–Z (preserves case, keeps punctuation)
#  - ROT13 (fixed Caesar shift of 13)
#  - Brute-force decoder (prints all 25 possible shifts)
#  - A simple text menu to use the tool from the terminal
#
# Key ideas:
#  - We treat the alphabet as circular (wrap-around) using modulo 26.
#  - We keep a single "pure" function (caesar) so it’s easy to test and reuse.
#  - The menu calls the function; logic stays separate from I/O.

# Build an alphabet list: ["A","B",...,"Z"]
alphabet_list = [chr(c) for c in range(ord('A'), ord('Z') + 1)]


def caesar(text: str, shift: int) -> str:
    """
    Core Caesar cipher function.
    - Shifts letters by `shift` positions through A–Z.
    - Preserves original case.
    - Leaves non-letters unchanged (spaces, punctuation, numbers).
    - Works for any integer shift (negative or > 26).

    Example:
      caesar("Abc xyz!", 2) -> "Cde zab!"
    """
    shift %= 26  # normalize (so 27 -> 1, -1 -> 25, etc.)
    out = []     # build result efficiently (list + join faster than string concat)

    for ch in text:
        up = ch.upper()  # compare using uppercase so we match A–Z
        if up in alphabet_list:
            # Find the current index 0..25 for A..Z
            i = alphabet_list.index(up)
            # Shift with wrap-around using modulo
            new_up = alphabet_list[(i + shift) % 26]
            # Restore original case (upper stays upper, lower stays lower)
            out.append(new_up if ch.isupper() else new_up.lower())
        else:
            # Not an A–Z letter: keep as-is
            out.append(ch)

    return "".join(out)


def rot13(text: str) -> str:
    """
    ROT13 is just Caesar with a fixed shift of 13.
    It is self-inverse: rot13(rot13(x)) == x
    """
    return caesar(text, 13)


def brute_force_decode(text: str) -> str:
    """
    Try all 25 possible reverse shifts and print candidates.
    Useful when you don't know the original shift.
    """
    lines = ["-- Brute-force candidates (shift means how much ORIGINAL text was shifted) --"]
    for s in range(1, 26):
        # To *decode* a Caesar with shift s, apply -s
        candidate = caesar(text, -s)
        lines.append(f"{s:2}: {candidate}")
    return "\n".join(lines)


def menu():
    """
    Simple command-line menu loop.
    Keeps input/output separate from the core logic (caesar, rot13).
    """
    while True:
        print("\nCaesar+ Tool")
        print("[e] encode  [d] decode  [r] rot13  [b] brute-force  [q] quit")
        choice = input("Choose: ").strip().lower()

        if choice == 'q':
            print("Bye!")
            break

        if choice not in {'e', 'd', 'r', 'b'}:
            print("Invalid choice. Use e/d/r/b/q.")
            continue

        # Ask for the message once (all options need it)
        text = input("Enter your message: ")

        if choice == 'r':
            # ROT13 path (no numeric shift needed)
            print("ROT13:", rot13(text))
            continue

        if choice == 'b':
            # Brute force path (shows all 25 possible decodings)
            print(brute_force_decode(text))
            continue

        # Encode/Decode path (needs a shift number)
        while True:
            try:
                # We accept any integer:
                #  - 0 does nothing
                #  - negatives and big numbers are fine (internally mod 26)
                shift = int(input("Enter shift value (integer, can be negative or >25): "))
                break
            except ValueError:
                print("Please enter a valid integer.")

        if choice == 'e':
            # Encoding = shift forward
            print("Encrypted:", caesar(text, shift))
        else:
            # Decoding = shift backward (reverse the sign)
            print("Decrypted:", caesar(text, -shift))


if __name__ == "__main__":
    # -----------------------------
    # Self-checks (quick tests):
    # These run ONLY when the file is executed directly.
    # They do NOT run if someone imports your functions.
    # -----------------------------
    assert caesar("Abc xyz!", 0) == "Abc xyz!"          # shift 0 should change nothing
    assert caesar("Abc xyz!", 2) == "Cde zab!"          # forward shift
    assert caesar("Cde zab!", -2) == "Abc xyz!"         # negative shift (decode)
    assert caesar("Hello, World!", 26) == "Hello, World!"  # big shift wraps
    assert rot13("Hello") == "Uryyb" and rot13("Uryyb") == "Hello"  # rot13 is self-inverse
    print("Self-tests passed.")

    # Start the menu loop
    menu()
