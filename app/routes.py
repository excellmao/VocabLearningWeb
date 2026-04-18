import random
from datetime import datetime, timedelta, timezone
from flask import current_app as app
from flask import jsonify
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import RegistrationForm, LoginForm
from app.forms import TopicForm, WordForm
from app.models import db, User, Topic, Word, WordProgress
from sqlalchemy import func
from datetime import datetime, timezone
from functools import wraps
from flask import abort

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If they are already logged in, send them to the dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # 1. Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.')
            return redirect(url_for('register'))

        # 2. Check if username is already taken
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please choose another one.')
            return redirect(url_for('register'))

        # 3. Hash the password and create the user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # 4. Flash success message and redirect to login
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main app
@app.route('/')
@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('flashcards'))

    now = datetime.now(timezone.utc)

    # 1. Spaced Repetition Stats
    words_due = WordProgress.query.filter(
        WordProgress.user_id == current_user.id,
        WordProgress.next_review <= now
    ).count()

    total_learning = WordProgress.query.filter_by(user_id=current_user.id).count()

    mastered_count = WordProgress.query.filter_by(
        user_id=current_user.id,
        is_mastered=True
    ).count()

    # 2. Dynamic Streak Logic
    today_index = now.weekday()
    active_days = [False] * 7
    if current_user.last_active:
        days_since_active = (now.date() - current_user.last_active.date()).days
        if days_since_active <= 1:
            start_index = today_index if days_since_active == 0 else today_index - 1
            for i in range(current_user.current_streak):
                day_to_light = start_index - i
                if day_to_light >= 0:
                    active_days[day_to_light] = True

    day_labels = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
    streak_data = [(label, active_days[i]) for i, label in enumerate(day_labels)]

    # 3. Weekly Leaderboard (Monday to Sunday)
    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())

    leaderboard_data = db.session.query(
        User.username,
        func.count(WordProgress.id).label('mastered_count')
    ).join(WordProgress).filter(
        WordProgress.is_mastered == True,
        WordProgress.date_mastered >= start_of_week
    ).group_by(User.username).order_by(func.count(WordProgress.id).desc()).limit(5).all()

    # 4. Find Weakest Topic
    weak_progress = WordProgress.query.filter(
        WordProgress.user_id == current_user.id,
        WordProgress.times_tested > 0
    ).all()

    topic_scores = {}
    for p in weak_progress:
        # Check for topic_id instead of the relationship object
        if p.word and p.word.topic_id:
            # Fetch the actual Topic object manually
            topic = Topic.query.get(p.word.topic_id)

            if topic:
                acc = p.times_correct / p.times_tested
                t_id = topic.id
                if t_id not in topic_scores:
                    topic_scores[t_id] = {'name': topic.name, 'total_acc': 0, 'count': 0}
                topic_scores[t_id]['total_acc'] += acc
                topic_scores[t_id]['count'] += 1

    weakest_topic = None
    if topic_scores:
        lowest_acc = 1.1  # Impossible baseline
        for t_id, data in topic_scores.items():
            avg = data['total_acc'] / data['count']
            if avg < lowest_acc:
                lowest_acc = avg
                weakest_topic = {'id': t_id, 'name': data['name']}

    return render_template('dashboard.html',
                           words_due=words_due,
                           total_learning=total_learning,
                           mastered_count=mastered_count,
                           streak_data=streak_data,
                           leaderboard=leaderboard_data,
                           weakest_topic=weakest_topic)


@app.route('/study')
@login_required
def study():
    now = datetime.now(timezone.utc)

    # Query WordProgress, filter by user, ensure it's due, and LIMIT to 15
    due_progress = WordProgress.query.join(Word).filter(
        WordProgress.user_id == current_user.id,
        WordProgress.next_review <= now
    ).limit(15).all()  # <--- Added limit(15) here

    words_data = [{
        'progress_id': progress.id,
        'word_id': progress.word.id,
        'term': progress.word.term,
        'definition': progress.word.definition,
        'example': progress.word.example_sentence,
    } for progress in due_progress]

    return render_template('study.html', words=words_data)


@app.route('/api/update_srs', methods=['POST'])
@login_required
def update_srs():
    data = request.get_json()
    # Note: We are now looking for the PROGRESS ID, not just the Word ID
    progress_id = data.get('progress_id')
    rating = data.get('rating')

    progress = WordProgress.query.get_or_404(progress_id)

    if progress.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    now = datetime.now(timezone.utc)
    progress.last_reviewed = now
    progress.times_tested += 1

    # SRS logic remains the same, but updates the Progress record
    if rating == 'easy':
        progress.next_review = now + timedelta(days=4)
        progress.user_difficulty_rating = 'easy'
        progress.times_correct += 1
        current_user.xp += 15
    elif rating == 'medium':
        progress.next_review = now + timedelta(days=1)
        progress.user_difficulty_rating = 'medium'
        progress.times_correct += 1
        current_user.xp += 10
    elif rating == 'hard':
        progress.next_review = now + timedelta(minutes=10)
        progress.user_difficulty_rating = 'hard'
        current_user.xp += 5

    # Mastery check on the progress record
    if progress.times_tested >= 3 and (progress.times_correct / progress.times_tested) >= 0.8:
        if not progress.is_mastered:
            progress.is_mastered = True
            progress.date_mastered = now
            current_user.xp += 50

    db.session.commit()
    return jsonify({"status": "success", "new_xp": current_user.xp})


@app.route('/quiz', methods=['GET'])
@login_required
def quiz_setup():
    user_progress = WordProgress.query.filter_by(user_id=current_user.id).all()
    enrolled_word_ids = [p.word_id for p in user_progress]

    enrolled_topics = db.session.query(Topic).join(Word).filter(Word.id.in_(enrolled_word_ids)).distinct().all()

    return render_template('quiz_setup.html', topics=enrolled_topics)


@app.route('/quiz/run', methods=['POST'])
@login_required
def quiz_run():
    # Use getlist() to grab an array of all checked boxes
    topic_ids = request.form.getlist('topic_ids')
    count = int(request.form.get('question_count', 10))

    progress_query = WordProgress.query.filter_by(user_id=current_user.id)

    # If "all" is not in the list, filter by the specific checked topics
    if 'all' not in topic_ids and topic_ids:
        # Convert string IDs from HTML into integers
        topic_ids_int = [int(t_id) for t_id in topic_ids]
        progress_query = progress_query.join(Word).filter(Word.topic_id.in_(topic_ids_int))

    available_progress = progress_query.all()

    if not available_progress:
        flash("You don't have enough words enrolled for the selected topics.")
        return redirect(url_for('quiz'))

    selected_progress = random.sample(available_progress, min(count, len(available_progress)))
    all_words = Word.query.all()

    quiz_data = []
    for p in selected_progress:
        target_word = p.word
        wrong_choices = random.sample([w for w in all_words if w.id != target_word.id], min(3, len(all_words) - 1))
        options = wrong_choices + [target_word]
        random.shuffle(options)

        quiz_data.append({
            'progress_id': p.id,
            'target_term': target_word.term,
            'options': [{'id': opt.id, 'def': opt.definition} for opt in options],
            'correct_id': target_word.id
        })

    return render_template('quiz_run.html', quiz_data=quiz_data)


@app.route('/api/submit_quiz_batch', methods=['POST'])
@login_required
def submit_quiz_batch():
    data = request.get_json()
    results = data.get('results', [])

    xp_earned = 0
    now = datetime.now(timezone.utc)

    # --- STREAK LOGIC FIX ---
    if not current_user.last_active or current_user.current_streak == 0:
        current_user.current_streak = 1  # First day using the app!
    else:
        delta = now.date() - current_user.last_active.date()
        if delta.days == 1:
            current_user.current_streak += 1  # Came back the next day
        elif delta.days > 1:
            current_user.current_streak = 1  # Streak broken, reset to 1
        # If delta.days == 0, they already got their streak today, do nothing.

    current_user.last_active = now

    for item in results:
        progress = WordProgress.query.get(item['progress_id'])
        if progress and progress.user_id == current_user.id:
            progress.times_tested += 1
            if item['is_correct']:
                progress.times_correct += 1
                xp_earned += 10

            if progress.times_tested >= 3 and (progress.times_correct / progress.times_tested) >= 0.8:
                if not progress.is_mastered:
                    progress.is_mastered = True
                    progress.date_mastered = now
                    xp_earned += 50

    current_user.xp += xp_earned
    db.session.commit()

    return jsonify({"status": "success", "xp_earned": xp_earned})

@app.route('/flashcards')
def flashcards():
    all_topics = Topic.query.all()

    return render_template('flashcards.html', topics=all_topics)


@app.route('/flashcards/<int:topic_id>')
def view_flashcards(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    words = Word.query.filter_by(topic_id=topic.id).all()

    # Check if the user is enrolled in this deck
    is_enrolled = False
    if current_user.is_authenticated:
        word_ids = [w.id for w in words]
        if word_ids:
            # If the user has ANY progress trackers for the words in this deck, they are enrolled
            progress_exists = WordProgress.query.filter(
                WordProgress.user_id == current_user.id,
                WordProgress.word_id.in_(word_ids)
            ).first()
            if progress_exists:
                is_enrolled = True

    return render_template('view_flashcards.html', topic=topic, words=words, is_enrolled=is_enrolled)


@app.route('/unenroll/<int:topic_id>', methods=['POST'])
@login_required
def unenroll_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    words = Word.query.filter_by(topic_id=topic.id).all()
    word_ids = [w.id for w in words]

    if word_ids:
        # Delete all progress trackers for these specific words for the current user
        WordProgress.query.filter(
            WordProgress.user_id == current_user.id,
            WordProgress.word_id.in_(word_ids)
        ).delete(synchronize_session=False)
        db.session.commit()

    flash(f'Removed "{topic.name}" from your learning queue.')
    return redirect(url_for('view_flashcards', topic_id=topic.id))



@app.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    form = TopicForm()
    if form.validate_on_submit():
        new_topic = Topic(name=form.name.data, user_id=current_user.id)
        db.session.add(new_topic)
        db.session.commit()

        flash('Deck created! Now add some words.')
        # Immediately redirect them to add words to this new deck
        return redirect(url_for('add_word', topic_id=new_topic.id))

    return render_template('create_topic.html', form=form)


@app.route('/add_word/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def add_word(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    form = WordForm()

    if form.validate_on_submit():
        # 1. Create the public word
        new_word = Word(
            term=form.term.data,
            definition=form.definition.data,
            example_sentence=form.example_sentence.data,
            topic_id=topic.id,
            user_id=current_user.id
        )
        db.session.add(new_word)
        db.session.commit()

        # 2. Automatically give the creator a progress tracker for it
        progress = WordProgress(user_id=current_user.id, word_id=new_word.id)
        db.session.add(progress)
        db.session.commit()

        flash(f'Added "{new_word.term}" to {topic.name}!')
        return redirect(url_for('add_word', topic_id=topic.id))

    # Fetch existing words to show the user what they've added so far
    words = Word.query.filter_by(topic_id=topic.id).all()
    return render_template('add_word.html', form=form, topic=topic, words=words)


@app.route('/progress')
@login_required
def progress():
    # 1. Weak Words Logic (Now querying WordProgress)
    weak_progress = WordProgress.query.filter(
        WordProgress.user_id == current_user.id,
        WordProgress.times_tested > 0
    ).all()
    actual_weak_words = [p for p in weak_progress if (p.times_correct / p.times_tested) < 0.5]

    # 2. Mastery Breakdown Logic
    mastered_count = WordProgress.query.filter_by(user_id=current_user.id, is_mastered=True).count()

    learning_count = WordProgress.query.filter(
        WordProgress.user_id == current_user.id,
        WordProgress.times_tested > 0,
        WordProgress.is_mastered == False
    ).count()

    new_count = WordProgress.query.filter_by(user_id=current_user.id, times_tested=0).count()

    # 3. Chart Data
    today = datetime.now(timezone.utc).date()
    last_7_dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    chart_labels = [day.strftime('%b %d') for day in last_7_dates]
    chart_data = [0] * 7

    mastered_progress_list = WordProgress.query.filter(
        WordProgress.user_id == current_user.id,
        WordProgress.is_mastered == True,
        WordProgress.date_mastered.isnot(None)
    ).all()

    for progress in mastered_progress_list:
        word_date = progress.date_mastered.date()
        if word_date in last_7_dates:
            index = last_7_dates.index(word_date)
            chart_data[index] += 1

    return render_template('progress.html',
                           weak_words=actual_weak_words,
                           mastered_count=mastered_count,
                           learning_count=learning_count,
                           new_count=new_count,
                           chart_labels=chart_labels,
                           chart_data=chart_data)


@app.route('/enroll/<int:topic_id>', methods=['POST'])
@login_required
def enroll_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    words = Word.query.filter_by(topic_id=topic.id).all()

    for word in words:
        existing_progress = WordProgress.query.filter_by(user_id=current_user.id, word_id=word.id).first()
        if not existing_progress:
            progress = WordProgress(user_id=current_user.id, word_id=word.id)
            db.session.add(progress)

    db.session.commit()
    flash(f'Added {topic.name} to your learning queue!')
    return redirect(url_for('view_flashcards', topic_id=topic.id))


@app.route('/delete_word/<int:word_id>', methods=['POST'])
@login_required
def delete_word(word_id):
    word = Word.query.get_or_404(word_id)

    # ADDED the admin bypass here:
    if word.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized.")
        return redirect(url_for('flashcards'))

    topic_id = word.topic_id

    WordProgress.query.filter_by(word_id=word.id).delete()

    db.session.delete(word)
    db.session.commit()

    return redirect(url_for('add_word', topic_id=topic_id))

@app.route('/delete_topic/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)

    # ADDED the admin bypass here:
    if topic.user_id != current_user.id and not current_user.is_admin:
        flash("Unauthorized.")
        return redirect(url_for('flashcards'))

    words = Word.query.filter_by(topic_id=topic.id).all()
    for word in words:
        WordProgress.query.filter_by(word_id=word.id).delete()
        db.session.delete(word)

    db.session.delete(topic)
    db.session.commit()

    flash(f'Deck "{topic.name}" has been deleted.')
    return redirect(url_for('flashcards'))


# --- ADMIN SECURITY DECORATOR ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to view that page.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


# --- ADMIN ROUTES ---
@app.route('/admin')
@admin_required
def admin_panel():
    users = User.query.all()
    # We can fetch all topics to display stats in the admin panel
    topics = Topic.query.all()
    return render_template('admin.html', users=users, topics=topics)


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own admin account!', 'danger')
        return redirect(url_for('admin_panel'))

    # Delete their study progress first to prevent database errors
    WordProgress.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin_panel'))

