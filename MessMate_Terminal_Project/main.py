import csv
import os
import hashlib
import hmac
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = {
    "students": ("students.csv", ["name", "student_id", "password"]),
    "managers": ("managers.csv", ["name", "manager_id", "password"]),
    "menu": ("daily_menu.csv", ["date", "meal", "food"]),
    "bookings": ("bookings.csv", ["student_id", "meal", "date"]),
    "reviews": ("reviews.csv", ["student_id", "meal", "date", "rating", "comment"]),
    "options": ("food_options.csv", ["date", "meal", "food"]),
    "votes": ("votes.csv", ["student_id", "date", "meal", "food"]),
}
MEALS = ["Breakfast", "Lunch", "Dinner"]
MANAGER_CODE = "MESSMATE2026"


def path(key):
    return os.path.join(BASE, FILES[key][0])


def read(key):
    filename, headers = FILES[key]
    if not os.path.exists(path(key)):
        write(key, [])
    with open(path(key), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(key, rows):
    filename, headers = FILES[key]
    with open(path(key), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def add(key, row):
    rows = read(key)
    rows.append(row)
    write(key, rows)


def initialize():
    for key in FILES:
        read(key)
    # Correct the old project's inconsistent vote CSV header without deleting its data.
    rows = read("votes")
    if rows and "meal" not in rows[0]:
        write("votes", [])
    print("MessMate data files are ready.")


def today():
    return date.today().isoformat()


def tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


def pause():
    input("\nPress Enter to continue...")


def ask(label):
    return input(label).strip()


def password_hash(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200000)
    return "pbkdf2$" + salt.hex() + "$" + digest.hex()


def password_ok(stored, entered):
    if stored.startswith("pbkdf2$"):
        try:
            _, salt, digest = stored.split("$")
            actual = hashlib.pbkdf2_hmac("sha256", entered.encode(), bytes.fromhex(salt), 200000).hex()
            return hmac.compare_digest(actual, digest)
        except Exception:
            return False
    # Support passwords previously created by the original Flask application.
    if stored.startswith("scrypt:") or stored.startswith("pbkdf2:"):
        try:
            from werkzeug.security import check_password_hash
            return check_password_hash(stored, entered)
        except ImportError:
            print("This account uses the old website password format.")
            print("Install the compatibility package with: pip install -r requirements.txt")
            return False
    return hmac.compare_digest(stored, entered)


def signup(role):
    key = "students" if role == "student" else "managers"
    id_label = "Student ID" if role == "student" else "Manager ID"
    print(f"\n--- {role.upper()} SIGN UP ---")
    name = ask("Name: ")
    user_id = ask(id_label + ": ")
    password = ask("Password (minimum 6 characters): ")
    if not name or not user_id or len(password) < 6:
        print("Please enter all details. Password must have at least 6 characters.")
        return
    if role == "manager" and ask("Manager registration code: ") != MANAGER_CODE:
        print("Invalid manager registration code.")
        return
    if any(r[id_label.lower().replace(" ", "_")].lower() == user_id.lower() for r in read(key)):
        print("This ID is already registered.")
        return
    add(key, {"name": name, id_label.lower().replace(" ", "_"): user_id,
              "password": password_hash(password)})
    print("Account created successfully. You can now log in.")


def login(role):
    key = "students" if role == "student" else "managers"
    id_key = "student_id" if role == "student" else "manager_id"
    print(f"\n--- {role.upper()} LOGIN ---")
    user_id = ask(id_key.replace("_", " ").title() + ": ")
    password = ask("Password: ")
    for user in read(key):
        if user[id_key].lower() == user_id.lower() and password_ok(user["password"], password):
            print(f"\nWelcome, {user['name']}!")
            return user
    print("Incorrect ID or password.")
    return None


def show_menu(menu_date):
    rows = [r for r in read("menu") if r["date"] == menu_date]
    print(f"\nMESS MENU — {menu_date}")
    for meal in MEALS:
        foods = [r["food"] for r in rows if r["meal"] == meal]
        print(f"\n{meal}:")
        if foods:
            for i, food in enumerate(foods, 1):
                print(f"  {i}. {food}")
        else:
            print("  No items added yet.")


def student_dashboard(student):
    while True:
        print("\n========== MESSMATE | STUDENT ==========")
        print(f"Hello, {student['name']} ({student['student_id']})")
        print("1. View today's menu")
        print("2. Generate meal check-in code")
        print("3. Vote for tomorrow's menu")
        print("4. Submit meal review")
        print("5. Logout")
        choice = ask("Choose an option: ")
        if choice == "1":
            show_menu(today())
            pause()
        elif choice == "2":
            meal = choose_meal()
            if not meal:
                continue
            if checked(student["student_id"], meal, today()):
                print("You have already checked in for this meal.")
            else:
                print("\nYOUR CHECK-IN CODE")
                print(f"MESSMATE|{student['student_id']}|{meal}|{today()}")
                print("Show this code to the mess manager for verification.")
            pause()
        elif choice == "3":
            student_vote(student)
            pause()
        elif choice == "4":
            student_review(student)
            pause()
        elif choice == "5":
            print("Logged out successfully.")
            return
        else:
            print("Invalid choice. Please select 1 to 5.")


def choose_meal():
    print("\n1. Breakfast\n2. Lunch\n3. Dinner")
    choice = ask("Select meal: ")
    return {"1": "Breakfast", "2": "Lunch", "3": "Dinner"}.get(choice)


def checked(student_id, meal, on_date):
    return any(r["student_id"] == student_id and r["meal"] == meal and r["date"] == on_date
               for r in read("bookings"))


def student_vote(student):
    vote_date = tomorrow()
    options = [r for r in read("options") if r["date"] == vote_date]
    if not options:
        print("The manager has not added food options for tomorrow yet.")
        return
    votes = read("votes")
    for meal in MEALS:
        meal_options = [r for r in options if r["meal"] == meal]
        if not meal_options:
            continue
        if any(v["student_id"] == student["student_id"] and v["date"] == vote_date and v["meal"] == meal for v in votes):
            print(f"\nYou have already voted for {meal}.")
            continue
        print(f"\n{meal} options for {vote_date}:")
        for i, row in enumerate(meal_options, 1):
            print(f"{i}. {row['food']}")
        choice = ask("Enter option number (or press Enter to skip): ")
        if choice.isdigit() and 1 <= int(choice) <= len(meal_options):
            add("votes", {"student_id": student["student_id"], "date": vote_date,
                          "meal": meal, "food": meal_options[int(choice)-1]["food"]})
            print("Your vote has been recorded.")
        elif choice:
            print("Invalid option. Skipped.")


def student_review(student):
    meal = choose_meal()
    if not meal:
        print("Invalid meal.")
        return
    if not checked(student["student_id"], meal, today()):
        print("You can review only a meal you checked in for today.")
        return
    reviews = read("reviews")
    if any(r["student_id"] == student["student_id"] and r["meal"] == meal and r["date"] == today() for r in reviews):
        print("You have already reviewed this meal.")
        return
    rating = ask("Rating (1 to 5): ")
    if rating not in ["1", "2", "3", "4", "5"]:
        print("Please enter a rating from 1 to 5.")
        return
    comment = ask("Your comment: ")
    add("reviews", {"student_id": student["student_id"], "meal": meal,
                    "date": today(), "rating": rating, "comment": comment})
    print("Thank you! Your review has been saved.")


def manager_dashboard(manager):
    while True:
        print("\n========== MESSMATE | MANAGER ==========")
        print(f"Welcome, {manager['name']}")
        print("1. View today's menu")
        print("2. Add food to daily menu")
        print("3. Verify student check-in code")
        print("4. Add food options for tomorrow's voting")
        print("5. View voting results")
        print("6. View student reviews")
        print("7. Logout")
        choice = ask("Choose an option: ")
        if choice == "1":
            show_menu(today())
            pause()
        elif choice == "2":
            add_menu_item()
            pause()
        elif choice == "3":
            verify_checkin()
            pause()
        elif choice == "4":
            add_food_option()
            pause()
        elif choice == "5":
            voting_results()
            pause()
        elif choice == "6":
            view_reviews()
            pause()
        elif choice == "7":
            print("Logged out successfully.")
            return
        else:
            print("Invalid choice. Please select 1 to 7.")


def add_menu_item():
    meal = choose_meal()
    if not meal:
        print("Invalid meal.")
        return
    food = ask("Food item: ")
    if not food:
        print("Food item cannot be empty.")
        return
    rows = read("menu")
    if any(r["date"] == today() and r["meal"] == meal and r["food"].lower() == food.lower() for r in rows):
        print("This item is already in today's menu.")
        return
    add("menu", {"date": today(), "meal": meal, "food": food})
    print("Food item added to today's menu.")


def verify_checkin():
    payload = ask("Enter/Paste student's check-in code: ")
    parts = payload.split("|")
    if len(parts) != 4 or parts[0] != "MESSMATE":
        print("Invalid MessMate code.")
        return
    _, student_id, meal, meal_date = parts
    if meal not in MEALS or not any(s["student_id"] == student_id for s in read("students")):
        print("Invalid meal or student ID.")
        return
    if checked(student_id, meal, meal_date):
        print("This student has already checked in.")
        return
    add("bookings", {"student_id": student_id, "meal": meal, "date": meal_date})
    print(f"Check-in successful: {student_id} — {meal} — {meal_date}")


def add_food_option():
    meal = choose_meal()
    if not meal:
        print("Invalid meal.")
        return
    food = ask("Food option: ")
    if not food:
        print("Food option cannot be empty.")
        return
    rows = read("options")
    if any(r["date"] == tomorrow() and r["meal"] == meal and r["food"].lower() == food.lower() for r in rows):
        print("This option already exists.")
        return
    add("options", {"date": tomorrow(), "meal": meal, "food": food})
    print(f"Added {food} to {meal} voting options for {tomorrow()}.")


def voting_results():
    vote_date = ask(f"Date [{tomorrow()}]: ") or tomorrow()
    votes = [r for r in read("votes") if r["date"] == vote_date]
    print(f"\nVOTING RESULTS — {vote_date}")
    if not votes:
        print("No votes yet.")
        return
    for meal in MEALS:
        counts = {}
        for row in votes:
            if row["meal"] == meal:
                counts[row["food"]] = counts.get(row["food"], 0) + 1
        if counts:
            print(f"\n{meal}:")
            for food, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
                print(f"  {food}: {count} vote(s)")
            top = max(counts.values())
            print("  Winner: " + ", ".join(food for food, count in counts.items() if count == top))


def view_reviews():
    reviews = sorted(read("reviews"), key=lambda r: r.get("date", ""), reverse=True)
    print("\nSTUDENT REVIEWS")
    if not reviews:
        print("No reviews submitted yet.")
        return
    for meal in MEALS:
        ratings = [int(r["rating"]) for r in reviews if r["meal"] == meal and r["rating"].isdigit()]
        if ratings:
            print(f"{meal}: {len(ratings)} review(s), average rating {sum(ratings)/len(ratings):.2f}/5")
    print("\nRecent comments:")
    for r in reviews[:20]:
        print(f"- {r['date']} | {r['student_id']} | {r['meal']} | {r['rating']}/5 | {r['comment']}")


def main():
    initialize()
    while True:
        print("\n" + "=" * 48)
        print("              MESSMATE")
        print("       SMART MESS MANAGEMENT SYSTEM")
        print("=" * 48)
        print("1. Student Sign Up")
        print("2. Student Login")
        print("3. Manager Sign Up")
        print("4. Manager Login")
        print("5. Exit")
        choice = ask("Choose an option: ")
        if choice == "1":
            signup("student")
            pause()
        elif choice == "2":
            user = login("student")
            if user:
                student_dashboard(user)
        elif choice == "3":
            signup("manager")
            pause()
        elif choice == "4":
            user = login("manager")
            if user:
                manager_dashboard(user)
        elif choice == "5":
            print("\nThank you for using MessMate. Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1 to 5.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nMessMate closed safely.")
