#!/usr/bin/env python3
import json
import os
import random
import sys
import getpass
import hashlib
import binascii
from pathlib import Path
from collections import defaultdict
from performance import record_result, user_stats, load_store, save_store

BASE = Path(__file__).parent
QUESTIONS_FILE = BASE / 'questions.json'
USERS_FILE = BASE / 'users.json'


def load_questions(path=QUESTIONS_FILE):
    if not path.exists():
        print('Question file missing:', path)
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        qs = data.get('questions') if isinstance(data, dict) else None
        if not isinstance(qs, list):
            print('Question file is misformatted (expected top-level "questions" array).')
            return []
        # Validate each question has required fields
        for q in qs:
            if not q.get('id'):
                print(f'Warning: Question missing "id" field: {q.get("question", "(no text)")[:30]}...')
            if not q.get('difficulty'):
                print(f'Warning: Question {q.get("id", "?")} missing "difficulty" field')
        return qs
    except json.JSONDecodeError:
        print('Question file contains invalid JSON.')
        return []


def prompt_int(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except Exception:
            print('Please enter an integer.')


def hash_password(password, salt=None):
    if salt is None:
        salt = hashlib.sha256(os.urandom(16)).hexdigest().encode('ascii')
    else:
        salt = salt.encode('ascii')
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.decode('ascii'), binascii.hexlify(dk).decode('ascii')


def load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        print('Users file unreadable/corrupted; starting with empty user database.')
        return {}


def save_users(u):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(u, f, indent=2)
    try:
        os.chmod(USERS_FILE, 0o600)
    except Exception:
        pass


def register_user():
    users = load_users()
    print('Register a new user')
    while True:
        username = input('Username: ').strip()
        if not username:
            print('Username cannot be blank')
            continue
        if username in users:
            print('That username exists; pick another or login instead.')
            continue
        pw = getpass.getpass('Password: ')
        pw2 = getpass.getpass('Repeat password: ')
        if pw != pw2:
            print('Passwords do not match; try again.')
            continue
        salt, hashed = hash_password(pw)
        users[username] = {'salt': salt, 'pw': hashed}
        save_users(users)
        print('Registered user', username)
        return username


def login_user():
    users = load_users()
    print('Login')
    username = input('Username: ').strip()
    if username not in users:
        print('Unknown user')
        return None
    pw = getpass.getpass('Password: ')
    salt = users[username]['salt']
    _, hashed = hash_password(pw, salt=salt)
    if hashed == users[username]['pw']:
        print('Login successful')
        return username
    else:
        print('Invalid password')
        return None


def present_question(q):
    QUIT_TOKENS = ('q', 'quit')
    print('\nQuestion:')
    print(q.get('question'))
    if q.get('type') == 'multiple_choice':
        opts = q.get('options', [])
        for i, o in enumerate(opts, start=1):
            print(f'  {i}. {o}')
        # accept index or option text; loop until parseable
        while True:
            ans = input("Your answer (number or exact option text) or 'q' to quit: ").strip()
            if not ans:
                print('Please enter an answer or q to quit.')
                continue
            if ans.lower() in QUIT_TOKENS:
                return '<<QUIT>>'
            if ans.isdigit():
                idx = int(ans)
                if 1 <= idx <= len(opts):
                    return opts[idx - 1]
                else:
                    print('Number out of range; try again.')
                    continue
            else:
                # match to option text
                matches = [o for o in opts if o.lower() == ans.lower()]
                if matches:
                    return matches[0]
                else:
                    print('Answer not understood; please enter the number, exact option text, or q to quit.')
                    continue
    else:
        # free text
        ans = input("Your answer (or 'q' to quit): ").strip()
        if ans.lower() in ('q', 'quit'):
            return '<<QUIT>>'
        return ans


def build_user_preferences(username):
    """Build user preference dict based on their feedback history."""
    data = load_store()
    history = [h for h in data.get('history', []) if h.get('user') == username]
    
    prefs = {}
    difficulty_feedback = defaultdict(lambda: {'likes': 0, 'dislikes': 0})
    
    for h in history:
        feedback = h.get('feedback')
        difficulty = h.get('difficulty', 'Unknown')
        
        if feedback == 'like':
            difficulty_feedback[difficulty]['likes'] += 1
        elif feedback == 'dislike':
            difficulty_feedback[difficulty]['dislikes'] += 1
    
    # Calculate preference score for each difficulty
    # positive = user prefers this difficulty, negative = user dislikes
    for difficulty, counts in difficulty_feedback.items():
        total = counts['likes'] + counts['dislikes']
        if total > 0:
            # Score: (likes - dislikes) / total, scaled for reasonable weighting
            prefs[difficulty] = (counts['likes'] - counts['dislikes']) / total * 0.5
        else:
            prefs[difficulty] = 0
    
    return prefs


def filter_by_difficulty(questions, difficulty):
    """Helper function to filter questions by difficulty level."""
    if not difficulty:
        return questions[:]
    df = str(difficulty).strip().lower()
    return [q for q in questions if str(q.get('difficulty', '')).strip().lower() == df]


def start_quiz():
    qs = load_questions()
    if not qs:
        print('No questions available. Please ensure questions.json exists and is valid.')
        return
    
    # Optional login for personalized selection based on feedback history
    user = None
    print('\nTo get questions tailored to your preferences based on past feedback, you can log in.')
    choice = input('Log in for personalized selection? (y/n): ').strip().lower()
    if choice == 'y':
        user = login_user()
    
    while True:
        try:
            raw = input("How many questions would you like? (enter 0 to cancel): ").strip()
            if raw.lower() in ('q', 'quit'):
                print('Cancelling quiz.')
                return
            num = int(raw)
            if num < 0:
                print('Enter a non-negative number.')
                continue
            break
        except ValueError:
            print('Please enter an integer or q to cancel.')

    if num == 0:
        print('Quiz cancelled.')
        return
    diff = input('Filter by difficulty? (Easy/Medium/Hard or leave blank): ').strip()
    if diff == '':
        diff = None
    # determine pool and validate requested count
    pool = filter_by_difficulty(qs, diff)
    if not pool:
        print('No questions match that filter.')
        return
    if num > len(pool):
        print(f'Requested {num} questions but only {len(pool)} available for that filter.')
        return
    
    # Build user preferences from their feedback history if logged in
    user_prefs = {}
    if user:
        user_prefs = build_user_preferences(user)
        if user_prefs:
            print('Personalizing question selection based on your feedback...')
    
    selected = select_questions(qs, num, difficulty_filter=diff, user_prefs=user_prefs)
    correct_count = 0
    answers = []
    for q in selected:
        ans = present_question(q)
        if ans == '<<QUIT>>':
            print('Exiting quiz early; returning to menu.')
            return
        correct = (ans.strip().lower() == q.get('answer', '').strip().lower())
        print('Correct!' if correct else f"Incorrect. Answer: {q.get('answer')}")
        fb = ask_feedback()
        feedback = None
        if fb == 'y':
            feedback = 'like'
        elif fb == 'n':
            feedback = 'dislike'
        answers.append((q, correct, feedback))
        if correct:
            correct_count += 1

    print(f'You answered {correct_count} out of {len(selected)} correctly.')

    # If not logged in yet, prompt to login/register to save results
    if not user:
        print('\nPlease login or register to save your performance and access features.')
        while True:
            choice = input('Enter L to login, R to register: ').strip().upper()
            if choice == 'L':
                user = login_user()
                if user:
                    break
                else:
                    continue
            elif choice == 'R':
                user = register_user()
                break
            else:
                print('Enter L or R')

    for q, correct, feedback in answers:
        record_result(user, q.get('id'), q.get('difficulty'), correct, feedback)

    stats = user_stats(user)
    print('\nYour performance:')
    print('  Total attempts:', stats.get('total'))
    print('  Correct answers:', stats.get('correct'))
    print('  Proficiency (weighted):', round(stats.get('proficiency', 0.0), 3))
    print('  By difficulty:')
    for d, v in stats.get('by_difficulty', {}).items():
        print(f"    {d}: {v['correct']}/{v['attempts']}")


def view_performance():
    print('View performance — please login')
    user = login_user()
    if not user:
        return
    stats = user_stats(user)
    print('\nPerformance for', user)
    print('  Total attempts:', stats.get('total'))
    print('  Correct answers:', stats.get('correct'))
    print('  Proficiency (weighted):', round(stats.get('proficiency', 0.0), 3))
    print('  By difficulty:')
    for d, v in stats.get('by_difficulty', {}).items():
        print(f"    {d}: {v['correct']}/{v['attempts']}")


def ask_feedback():
    while True:
        f = input('Did you like this question? (y/n/skip): ').strip().lower()
        if f in ('y', 'n', 'skip'):
            return f
        print('Enter y, n, or skip.')


def select_questions(qs, count, difficulty_filter=None, user_prefs=None):
    pool = filter_by_difficulty(qs, difficulty_filter)
    if not pool:
        return []
    # weight by user_prefs (preferences by difficulty)
    if user_prefs is None:
        user_prefs = {}
    weights = []
    for q in pool:
        base = 1.0
        pref = user_prefs.get(q.get('difficulty'), 0)
        base *= (1.0 + pref)
        weights.append(base)
    # If requesting more than available, return shuffled full pool
    if count >= len(pool):
        random.shuffle(pool)
        return pool[:count]
    # Use random.choices to allow weighting, then ensure uniqueness by sampling without replacement if needed
    try:
        chosen = random.choices(pool, weights=weights, k=count)
        # make unique while preserving order (crashes if 'id' missing, so use .get())
        seen = set()
        uniq = []
        for q in chosen:
            q_id = q.get('id')
            if q_id and q_id not in seen:
                uniq.append(q)
                seen.add(q_id)
        # if duplicates removed and we have fewer than requested, fill from remaining
        if len(uniq) < count:
            remaining = [q for q in pool if q.get('id') not in seen]
            while len(uniq) < count and remaining:
                extra = random.choice(remaining)
                uniq.append(extra)
                remaining = [q for q in remaining if q.get('id') != extra.get('id')]
        return uniq[:count]
    except Exception as e:
        # fallback to simple random.sample if weighting fails (e.g., weights sum to 0)
        # This degrades gracefully when preference weighting cannot be applied
        return random.sample(pool, min(count, len(pool)))


def edit_questions():
    """Allow users to edit questions in the question bank."""
    qs = load_questions()
    if not qs:
        print('No questions available.')
        return
    
    print('\nAvailable questions:')
    for q in qs:
        q_id = q.get('id', '?')
        q_text = q.get('question', '(no text)')[:50]
        print(f"  [{q_id}] {q_text}...")
    
    # Select question to edit
    while True:
        q_id_input = input('\nEnter question ID to edit (or q to cancel): ').strip()
        if q_id_input.lower() in ('q', 'quit'):
            return
        try:
            q_id = int(q_id_input)
            break
        except ValueError:
            print('Please enter a valid ID.')
    
    # Find question
    target = None
    idx = None
    for i, q in enumerate(qs):
        if q.get('id') == q_id:
            target = q
            idx = i
            break
    
    if target is None:
        print('Question not found.')
        return
    
    # Display current question
    print('\nCurrent question:')
    for key in ['id', 'question', 'type', 'options', 'answer', 'category', 'difficulty']:
        print(f"  {key}: {target.get(key)}")
    
    # Allow editing
    while True:
        field = input('\nEdit which field? (question/type/options/answer/category/difficulty/done): ').strip().lower()
        if field == 'done':
            break
        if field not in ['question', 'type', 'options', 'answer', 'category', 'difficulty']:
            print('Invalid field.')
            continue
        
        new_val = input(f'New value for {field}: ').strip()
        
        if field == 'options':
            # Parse options as comma-separated
            target[field] = [o.strip() for o in new_val.split(',')]
        else:
            target[field] = new_val
        print(f'{field} updated.')
    
    # Save
    qs[idx] = target
    try:
        with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'questions': qs}, f, indent=2)
        print('\nQuestion saved successfully.')
    except Exception as e:
        print(f'Error saving questions: {e}')


def main():
    print('Welcome to the Quiz App!')
    print('This app will quiz you on programming topics.')
    # simple menu loop
    while True:
        print('\nMenu:')
        print('  1) Start Quiz')
        print('  2) View Performance')
        print('  3) Edit Questions')
        print('  4) Quit')
        choice = input('Select an option (1/2/3/4 or start/view/edit/quit): ').strip().lower()
        if choice in ('1', 'start', 's'):
            start_quiz()
        elif choice in ('2', 'view', 'v'):
            view_performance()
        elif choice in ('3', 'edit', 'e'):
            edit_questions()
        elif choice in ('4', 'quit', 'q', 'exit'):
            print('Goodbye')
            return
        else:
            print('Enter 1, 2, 3, 4 or start/view/edit/quit')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted. Exiting.')
