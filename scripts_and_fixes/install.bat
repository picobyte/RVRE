@ECHO OFF

IF EXIST game\RVRE GOTO GOT_RVRE
IF NOT EXIST ..\..\game\RVRE GOTO EXIT_1
CD ..\..

:GOT_RVRE
IF EXIST .git\modules\game\RVRE GOTO GOT_GIT

:EXIT_1
ECHO "Install.bat should be run from your Ren'py game with a RVRE checkout in game\RVRE"
exit 1

:GOT_GIT

ECHO "Installing python modules used by the editor, old versions because of Ren'Py's python2.7 requirement"
CD game

python -m pip install --target python-packages "pyperclip"
python -m pip install --target python-packages "pygments==2.5.2"
python -m pip install --target python-packages "pyspellchecker==0.5.6"
python -m pip install --target python-packages "gitpython==2.1.11"

REM for Russian and other language updates copy the languages files from https://github.com/barrust/pyspellchecker.git
REM to python-packages\spellchecker\resources\

CD ..\..
MKDIR python-packages
CP game\RVRE\scripts_and_fixes\pygments_filters_init_py_replacement python-packages\pygments\filters\__init__.py
CP /E/H game\python-packages\spellchecker python-packages

ECHO
ECHO "Installing codeface fonts"
git submodule add https://github.com/chrissimpkins/codeface.git game\codeface

REM An optional cleanup step, you could edit the list to specify other codeface fonts to keep
CP game\RVRE\scripts_and_fixes\list_of_codeface_fonts_to_include.txt .git\modules\game\RVRE\modules\codeface\info\sparse-checkout
git -C game\codeface config core.sparseCheckout true
git -C game\codeface read-tree -m -u HEAD


