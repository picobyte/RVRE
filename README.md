## Ren'Py Visual Runtime Editor

This repository is intended to be added as a submodule to a git project, a minimal installation of the Ren'Py visual runtime editor.

To include the editor in a renpy project make your project a git repository (if you haven't already):

```bash
git init

# add python and Ren'py files to your repository. You may want to add any other files that you might change for your project.
find game -type f -name "*.*py" -exec git add {} \+

git commit -m 'Initial commit for my visual novel'
```

In windows you can run these commands after installation of  https://gitforwindows.org/ which provides a commandline which should enable you to run this (at least the find command is Linux and Mac(?) command line only). 

```bash
# add the RVRE as a submodule 
git submodule add https://github.com/picobyte/RVRE game/RVRE

#install
game/RVRE/scripts_and_fixes/install.sh
```
For Windows there's `scripts_and_fixes\install.bat` which should do the same.

An example visual novel with RVRE included is https://github.com/picobyte/EditButton. The readme there discusses some of the features of the editor.
