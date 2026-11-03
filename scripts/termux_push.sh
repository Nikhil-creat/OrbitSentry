#!/data/data/com.termux/files/usr/bin/bash
# One-shot GitHub push from Termux. Run from inside the unzipped project folder.
set -e
REPO="${1:-orbitsentry}"
pkg update -y && pkg install -y git gh
git config --global user.name "Nikhil Chary Sriramoju"
git config --global user.email "sriramojunikhil66@gmail.com"
gh auth status >/dev/null 2>&1 || gh auth login
[ -d .git ] || git init -b main
git add .
git commit -m "OrbitSentry master" || true
git branch -M main
if gh repo create "$REPO" --public --source=. --remote=origin --push; then
  echo "Pushed via gh."
else
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/Nikhil-creat/$REPO.git"
  git push -u origin main
fi
echo "Next: vercel.com -> Add New -> Project -> import $REPO -> Deploy"
