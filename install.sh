#!/bin/bash

if [ ! -d game/RVRE -o ! -d .git/modules/game/RVRE/ ]; then
  echo "$0 should be run from the root of your Ren'py game with a RVRE checkout in game/RVRE" 1>&2
  exit 1
fi

echo "Installing python modules used by the editor, old versions because of Ren'Py's python2.7 requirement" 1>&2
cd game/RVRE
python -m pip install --target python-packages pyperclip
python -m pip install --target python-packages pygments==2.5.2
python -m pip install --target python-packages pyspellchecker==0.5.6
python -m pip install --target python-packages gitpython==2.1.11
cp pygments_filters_init_py_replacement python-packages/pygments/filters/__init__.py
cd -

echo
echo "Installing codeface fonts" 1>&2
git submodule update --init --recursive
egrep -v '^(#|$)' game/RVRE/list_of_codeface_fonts_to_include.txt > .git/modules/game/RVRE/modules/codeface/info/sparse-checkout
git -C game/RVRE/codeface config core.sparseCheckout true
git -C game/RVRE/codeface read-tree -m -u HEAD
