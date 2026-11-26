#!/bin/sh
# SPDX-License-Identifier: MIT
# MustardOS for R36S/R35S (unofficial port): choose your console model.
# Run it from the card's boot partition on a PC (Linux: sh select-model.sh;
# macOS: double-click select-model.command). It writes model.txt next to
# itself; the console applies it at its next start (it restarts once by
# itself). EXPERIMENTAL: only the R36S-V12 Panel 0 / R35S is tested.
cd "$(dirname "$0")" || exit 1
[ -f models.txt ] || { echo "models.txt not found: run this from the card's boot partition."; exit 1; }
echo "MustardOS for R36S/R35S: console model"
echo
if [ -f model.txt ]; then
    echo "Current choice: $(head -n 1 model.txt | tr -d '\r')"
else
    echo "Current choice: none (the console keeps its model)"
fi
for f in model.txt.failed model.txt.unknown; do
    [ -f "$f" ] && echo "Note: $f: the console did not accept '$(head -n 1 "$f" | tr -d '\r')'."
done
echo
i=0
while IFS="$(printf '\t')" read -r id name; do
    i=$((i + 1))
    printf '%3d  %s\n' "$i" "$name"
done < models.txt
echo
printf 'Number of your model (Enter = cancel): '
read -r n
case $n in ''|*[!0-9]*) echo "Nothing changed."; exit 0 ;; esac
id=$(sed -n "${n}p" models.txt | cut -f1)
name=$(sed -n "${n}p" models.txt | cut -f2)
[ -n "$id" ] || { echo "No model $n. Nothing changed."; exit 1; }
printf '%s\n' "$id" > model.txt.tmp && mv -f model.txt.tmp model.txt
rm -f model.txt.failed model.txt.unknown
sync
echo
echo "Chosen: $name"
echo "Eject the card, put it in slot 1 and power on. The console restarts"
echo "once by itself to apply it. If the screen stays black or wrong for"
echo "more than a minute, hold Power to turn it off and on again: it goes"
echo "back to the previous model by itself."
