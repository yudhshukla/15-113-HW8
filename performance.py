import os
import pickle
import time
from collections import defaultdict

STORE_PATH = os.path.join(os.path.dirname(__file__), 'performance.store')


def load_store(path=STORE_PATH):
    if not os.path.exists(path):
        return {"users": {}, "history": []}
    try:
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception:
        # If store corrupted, don't crash; return empty structure
        return {"users": {}, "history": []}


def save_store(data, path=STORE_PATH):
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        pickle.dump(data, f)
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def record_result(username, question_id, difficulty, correct, feedback=None, path=STORE_PATH):
    data = load_store(path)
    if 'history' not in data:
        data['history'] = []
    entry = {
        'user': username,
        'q_id': question_id,
        'difficulty': difficulty,
        'correct': bool(correct),
        'feedback': feedback,
        'ts': time.time()
    }
    data['history'].append(entry)
    # ensure users key exists
    if 'users' not in data:
        data['users'] = {}
    if username not in data['users']:
        data['users'][username] = {'prefs': defaultdict(int)}
    save_store(data, path)


def user_stats(username, path=STORE_PATH):
    data = load_store(path)
    history = [h for h in data.get('history', []) if h.get('user') == username]
    stats = {
        'total': len(history),
        'correct': sum(1 for h in history if h.get('correct')),
        'by_difficulty': {}
    }
    by_diff = defaultdict(lambda: {'attempts': 0, 'correct': 0})
    for h in history:
        d = h.get('difficulty') or 'Unknown'
        by_diff[d]['attempts'] += 1
        if h.get('correct'):
            by_diff[d]['correct'] += 1
    stats['by_difficulty'] = dict(by_diff)
    # compute simple proficiency score weighted by difficulty
    weights = {'Easy': 1, 'Medium': 2, 'Hard': 3}
    weighted_correct = 0
    weighted_total = 0
    for d, vals in by_diff.items():
        w = weights.get(d, 1)
        weighted_correct += vals['correct'] * w
        weighted_total += vals['attempts'] * w
    stats['proficiency'] = (weighted_correct / weighted_total) if weighted_total else 0.0
    return stats
