#!/usr/bin/env python3
"""Extract useful info from WhatsApp chat exports."""
import os, re

d = "/data/data/com.termux/files/home/Documents/Codex/2026-05-18/hola-3/team/chats/"

# Read group chat
text = ""
for f in os.listdir(d):
    if "Administraci" in f and f.endswith(".txt"):
        path = os.path.join(d, f)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        break

lines = text.split("\n")
print(f"=== GROUP CHAT: {len(lines)} lines ===")

# Find phone numbers
phones = set()
for line in lines:
    found = re.findall(r'(\+?\d[\d\s\-\(\)]{7,15})', line)
    for p in found:
        p = p.strip()
        if len(p) >= 10:
            phones.add(p)

print("\n=== PHONE NUMBERS ===")
for p in sorted(phones):
    print(f"  {p}")

# Find prices
print("\n=== PRICES ===")
for line in lines:
    if re.search(r'[\$]\s*\d+', line):
        print(f"  {line[:200]}")

# Find emails
print("\n=== EMAILS ===")
for line in lines:
    found = re.findall(r'[\w.]+@[\w.]+\.\w+', line)
    for e in found:
        print(f"  {e}")

# Find key info
print("\n=== KEY INFO ===")
keywords = ["precio", "habita", "cabañ", "camping", "servicio", "wifi", "direccion", "whatsapp"]
for kw in keywords:
    for line in lines:
        if kw.lower() in line.lower():
            print(f"  [{kw}] {line[:250]}")
            break

# Now read Leo's chat
text2 = ""
for f in os.listdir(d):
    if "Leo Tello" in f and f.endswith(".txt"):
        path = os.path.join(d, f)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text2 = fh.read()
        break

lines2 = text2.split("\n")
print(f"\n\n=== LEO'S CHAT: {len(lines2)} lines ===")

# Find prices in Leo's chat
print("\n=== PRICES (Leo) ===")
for line in lines2:
    if re.search(r'[\$]\s*\d+', line):
        print(f"  {line[:200]}")

# Find keywords in Leo's chat
print("\n=== KEY INFO (Leo) ===")
for kw in ["precio", "habita", "cabañ", "servicio", "whatsapp", "tel", "direccion", "ig", "instagram"]:
    for line in lines2:
        if kw.lower() in line.lower():
            print(f"  [{kw}] {line[:250]}")
            break
