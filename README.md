To include the editor in a renpy project first make the project a git repository (if you haven't already)

if [ ! -d '.git' ]; then
  git init
  find game -type f -name "*.*py" -exec git add {} \+
  git commit -m 'Initial commit'
fi

# add the RVRE submodule
git submodule add https://github.com/picobyte/RVRE game/RVRE


