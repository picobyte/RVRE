@echo off

IF EXIST game\RVRE GOTO GOT_RVRE
GOTO EXIT1

:GOT_RVRE
IF EXIST .git\modules\game\RVRE GOTO GOT_RIT

:EXIT1
ECHO "should be run from the root of your Ren'py game with a RVRE checkout in game\RVRE"
exit 1

:GOT_GIT

ECHO "Installing python modules used by the editor, old versions because of Ren'Py's python2.7 requirement"
CD game\RVRE

python -m pip install --target python-packages "pyperclip"
python -m pip install --target python-packages "pygments==2.5.2"
python -m pip install --target python-packages "pyspellchecker==0.5.6"
python -m pip install --target python-packages "gitpython==2.1.11"
CP pygments_filters_init_py_replacement python-packages\pygments\filters\__init__.py
CD ..\..

ECHO
ECHO "Installing codeface fonts"

git submodule update --init --recursive
CP game\RVRE\list_of_codeface_fonts_to_include.txt .git\modules\game\RVRE\modules\codeface\info\sparse-checkout
git -C game\RVRE\codeface config core.sparseCheckout true
git -C game\RVRE\codeface read-tree -m -u HEAD


