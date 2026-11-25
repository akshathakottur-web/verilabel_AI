# Team Guide: Git steps for everyone

Repo: https://github.com/akshathakottur-web/verilabel_AI

Branches: member1-platform, member2-ai, member3-frontend (and main).

## First time only

1. Open Command Prompt or the VS Code terminal in the folder where you keep projects.
2. Download the project:
   git clone https://github.com/akshathakottur-web/verilabel_AI.git
3. Go into the folder:
   cd verilabel_AI
4. Switch to YOUR branch (use your own branch name):
   git checkout member2-ai
5. Check you are on the right branch:
   git branch
   (the branch with a star is the one you are on)
6. Set your name once (skip if already done):
   git config --global user.name "Your Name"
   git config --global user.email "your-github-email@example.com"
7. Make a virtual environment and install packages:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   (Member 2 also runs: pip install -r requirements-ai.txt)
8. Copy .env.example to a new file called .env.

## Every working session

1. Get the latest shared work from main into your branch:
   git checkout your-branch-name
   git pull origin main
2. Do your work ONLY inside your own folders.
3. Save your work:
   git status
   git add .
   git commit -m "Short message about what you did"
   git push origin your-branch-name

Commit and push after every finished step, so nothing is lost.

## When a milestone is finished

1. Push your branch (step 3 above).
2. On GitHub, open your branch and click "Contribute" then "Open pull request"
   (or the yellow "Compare & pull request" button). Base branch: main.
3. Tell Member 1. Member 1 reviews and merges.
4. After the merge, everyone runs "git pull origin main" on their own branch.

Merge order: Member 2, then Member 3, then Member 1.

## Rules

- Never edit another member's folders.
- Never push .env, venv, photos, or datasets (the .gitignore already blocks them).
- Never change contracts/ yourself. Tell Member 1 and the group, then Member 1 updates it.
- If git shows "conflict", stop and ask Member 1 before doing anything.
- Windows note for Member 1: run the Celery worker with --pool=solo.
