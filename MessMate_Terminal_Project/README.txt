MESSMATE - PYTHON CONSOLE PROJECT
=================================

This version runs directly in the VS Code terminal. It does NOT start a website
and does NOT need Flask.

FEATURES
- Separate student and manager sign up/login
- View today's breakfast, lunch and dinner menu
- Student meal check-in code generation
- Manager check-in code verification
- Student voting for tomorrow's food
- Manager voting results and winner
- Student meal reviews and manager review summary
- CSV files used for persistent storage

HOW TO RUN (Windows / VS Code)
1. Extract this ZIP into a folder.
2. Open that folder in VS Code (File > Open Folder).
3. Open Terminal > New Terminal.
4. Run:
       python main.py
   If that does not work, try:
       py main.py

MANAGER SIGN-UP CODE
    MESSMATE2026

IMPORTANT
- Keep main.py and all CSV files in the same folder.
- Do not delete the CSV files if you want to retain saved users and records.
- The original project used Flask password hashes. Existing accounts are
  supported when Werkzeug is installed. Install it once with:
       pip install -r requirements.txt
- New accounts use Python's built-in password hashing.
- The old website's QR image upload and camera scanning are represented by
  a text check-in code in this terminal version. The manager pastes that code
  to verify the check-in.
