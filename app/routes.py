from datetime import datetime, timedelta, timezone
from flask import jsonify
from flask import current_app as app
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User, Topic, Word
from app.forms import RegistrationForm, LoginForm
import random
from app.forms import WordForm
from flask import jsonify


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()  # Commit so the user gets an ID

        default_topic = Topic(name="General", user_id=new_user.id)
        db.session.add(default_topic)
        db.session.commit()

        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


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
@login_required
def dashboard():
    total_words = Word.query.filter_by(user_id = current_user.id).count()
    mastered_words = Word.query.filter_by(user_id = current_user.id, is_mastered = True).count()

    return render_template('dashboard.html', total_words=total_words, mastered_words=mastered_words)

@app.route('/flashcards')
@login_required
def flashcard():
    user_topics = Topic.query.filter_by(user_id = current_user.id).all()
    all_words = Word.query.filter_by(user_id = current_user.id).all()

    return render_template('flashcards.html', topics = user_topics, words = all_words)


@app.route('/study')
@login_required
def study():
    """
    Fetches words that are due for review based on the SRS algorithm.
    """
    now = datetime.now(timezone.utc)

    # Fetch words where the next_review date has passed
    due_words = Word.query.filter(
        Word.user_id == current_user.id,
        Word.next_review <= now
    ).all()

    # Convert the database objects to a list of dictionaries for JavaScript
    words_data = [{
        'id': word.id,
        'term': word.term,
        'definition': word.definition,
        'example': word.example_sentence,
        'synonyms': word.synonyms
    } for word in due_words]

    return render_template('study.html', words=words_data)


@app.route('/api/update_srs', methods=['POST'])
@login_required
def update_srs():
    data = request.get_json()
    word_id = data.get('word_id')
    rating = data.get('rating')

    word = Word.query.get_or_404(word_id)

    if word.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    now = datetime.now(timezone.utc)
    word.last_reviewed = now
    word.times_tested += 1

    if rating == 'easy':
        word.next_review = now + timedelta(days=4)
        word.user_difficulty = 'easy'
        word.times_correct += 1
        current_user.xp += 15
    elif rating == 'medium':
        word.next_review = now + timedelta(days=1)
        word.user_difficulty = 'medium'
        word.times_correct += 1
        current_user.xp += 10
    elif rating == 'hard':
        # Review it again very soon (e.g., 5 minutes from now)
        word.next_review = now + timedelta(minutes=5)
        word.user_difficulty = 'hard'
        current_user.xp += 5

    accuracy = word.times_correct / word.times_tested
    if word.times_tested >= 3 and accuracy >= 0.8 and not word.is_mastered:
        word.is_mastered = True
        word.date_mastered = now
        current_user.xp += 50

    new_level = (current_user.xp // 100) + 1
    if new_level > current_user.level:
        current_user.level = new_level

    db.session.commit()

    return jsonify({"status": "success", "new_xp": current_user.xp})


@app.route('/quiz', methods=['GET'])
@login_required
def quiz():
    # Fetch all user words
    words = Word.query.filter_by(user_id=current_user.id).all()

    # Need at least 4 words to run a proper multiple choice quiz
    if len(words) < 4:
        flash('You need at least 4 words in your library to start a quiz!')
        return redirect(url_for('dashboard'))

    # 1. Pick the target word to test
    target_word = random.choice(words)

    # 2. Pick 3 random wrong definitions
    other_words = [w for w in words if w.id != target_word.id]
    wrong_choices = random.sample(other_words, 3)

    # 3. Combine and shuffle the options so the correct answer isn't always first
    options = [target_word] + wrong_choices
    random.shuffle(options)

    quiz_data = {
        'target': target_word,
        'options': options
    }

    return render_template('quiz.html', quiz_data=quiz_data)


@app.route('/api/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    data = request.get_json()
    word_id = data.get('word_id')
    is_correct = data.get('is_correct')

    word = Word.query.get_or_404(word_id)

    if word.user_id == current_user.id:
        word.times_tested += 1

        if is_correct:
            word.times_correct += 1
            current_user.xp += 5  # Gamification reward

            # Check for Mastery via Quiz
            accuracy = word.times_correct / word.times_tested
            if word.times_tested >= 3 and accuracy >= 0.8 and not word.is_mastered:
                word.is_mastered = True
                word.date_mastered = datetime.now(timezone.utc)
                current_user.xp += 50

        db.session.commit()

    return jsonify({"status": "success", "new_xp": current_user.xp})


@app.route('/add_word', methods=['GET', 'POST'])
@login_required
def add_word():
    form = WordForm()

    # Populate the topic dropdown with the user's specific topics
    user_topics = Topic.query.filter_by(user_id=current_user.id).all()
    form.topic_id.choices = [(t.id, t.name) for t in user_topics]

    if form.validate_on_submit():
        new_word = Word(
            user_id=current_user.id,
            topic_id=form.topic_id.data,
            term=form.term.data,
            definition=form.definition.data,
            example_sentence=form.example_sentence.data,
            synonyms=form.synonyms.data
        )
        db.session.add(new_word)
        db.session.commit()

        flash('New vocabulary word added successfully!')
        return redirect(url_for('flashcards'))

    return render_template('word_form.html', form=form)


@app.route('/delete_word/<int:word_id>', methods=['POST'])
@login_required
def delete_word(word_id):
    word = Word.query.get_or_404(word_id)

    # Security check: ensure the user actually owns this word
    if word.user_id == current_user.id:
        db.session.delete(word)
        db.session.commit()
        flash(f'"{word.term}" has been deleted.')

    return redirect(url_for('flashcards'))

@app.route('/progress')
@login_required
def progress():
    weak_words = Word.query.filter(
        Word.user_id == current_user.id,
        Word.times_tested > 0
    ).all()
    actual_weak_words = [w for w in weak_words if (w.times_correct / w.times_tested) < 0.5]

    mastered_count = Word.query.filter_by(user_id=current_user.id, is_mastered=True).count()

    learning_count = Word.query.filter(
        Word.user_id == current_user.id,
        Word.times_tested > 0,
        Word.is_mastered == False
    ).count()

    new_count = Word.query.filter_by(user_id=current_user.id, times_tested=0).count()

    today = datetime.now(datetime.timezone.utc).date()
    last_7_dates = [(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
    chart_labels = [day.strftime('%b %d') for day in last_7_dates]
    chart_data = [0] * 7

    # ONLY fetch words that are actually mastered and have a mastery date
    mastered_words_list = Word.query.filter(
        Word.user_id == current_user.id,
        Word.is_mastered == True,
        Word.date_mastered.isnot(None)
    ).all()

    for word in mastered_words_list:
        word_date = word.date_mastered.date()
        if word_date in last_7_dates:
            # Sort the mastered word into the correct day bucket
            index = last_7_dates.index(word_date)
            chart_data[index] += 1

    return render_template('progress.html',
                           weak_words=actual_weak_words,
                           mastered_count=mastered_count,
                           learning_count=learning_count,
                           new_count=new_count,
                           chart_labels=chart_labels,
                           chart_data=chart_data)