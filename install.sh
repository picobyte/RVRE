#!/bin/bash

if [ ! -d game/RVRE -o ! -d .git/modules/game/RVRE/ ]; then
  echo "$0 should be run from the root of your Ren'py game with a RVRE checkout in game/RVRE"
  exit 1
fi

cd game/RVRE
python -m pip install --target python-packages pyperclip
python -m pip install --target python-packages pygments==2.5.2
python -m pip install --target python-packages pyspellchecker==0.5.6
python -m pip install --target python-packages gitpython==2.1.11
cd -

git submodule update --init --recursive
egrep -v '^(#|$)' list_of_codeface_fonts_to_include.txt > .git/modules/game/RVRE/modules/codeface/info/sparsgit -C game/RVRE/codeface config core.sparseCheckout true
git -C game/RVRE/codeface read-tree -m -u HEAD


