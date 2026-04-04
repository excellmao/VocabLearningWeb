from app import create_app, db
from app.models import User, Topic, Word

app = create_app()


def seed_database():
    with app.app_context():
        db.create_all()

        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', password_hash='pbkdf2:sha256:...')
            db.session.add(test_user)
            db.session.commit()

        topic_names = ["Computer", "School", "Football"]
        topics_dict = {}

        for name in topic_names:
            topic = Topic.query.filter_by(name=name, user_id=test_user.id).first()
            if not topic:
                topic = Topic(name=name, user_id=test_user.id)
                db.session.add(topic)
                db.session.commit()
            topics_dict[name.lower()] = topic

        seed_data = [
            # COMPUTER
            {"term": "Motherboard", "definition": "The main printed circuit board in a computer.",
             "topic_key": "computer"},
            {"term": "Virtualization",
             "definition": "Creating a virtual version of something, like an operating system or server.",
             "topic_key": "computer"},
            {"term": "Kernel", "definition": "The core program of an operating system that manages system resources.",
             "topic_key": "computer"},
            {"term": "Router", "definition": "A device that forwards data packets between computer networks.",
             "topic_key": "computer"},
            {"term": "Latency", "definition": "The delay before a transfer of data begins following an instruction.",
             "topic_key": "computer"},
            {"term": "Framework",
             "definition": "A platform for developing software applications (like Flask or Spring).",
             "topic_key": "computer"},
            {"term": "Deployment", "definition": "All the activities that make a software system available for use.",
             "topic_key": "computer"},
            {"term": "Repository",
             "definition": "A central location in which data is stored and managed, often used in version control.",
             "topic_key": "computer"},
            {"term": "Syntax",
             "definition": "The set of rules that defines the combinations of symbols that are considered to be correctly structured programs.",
             "topic_key": "computer"},
            {"term": "Compiler", "definition": "A program that translates source code into executable machine code.",
             "topic_key": "computer"},
            {"term": "Debugging",
             "definition": "The process of identifying and removing errors from computer hardware or software.",
             "topic_key": "computer"},
            {"term": "Tensor",
             "definition": "A mathematical object analogous to but more general than a vector, used heavily in AI/machine learning.",
             "topic_key": "computer"},
            {"term": "Neural Network",
             "definition": "A computing system inspired by the biological neural networks that constitute animal brains.",
             "topic_key": "computer"},
            {"term": "Algorithm",
             "definition": "A process or set of rules to be followed in calculations or other problem-solving operations.",
             "topic_key": "computer"},
            {"term": "Database",
             "definition": "A structured set of data held in a computer, especially one that is accessible in various ways.",
             "topic_key": "computer"},
            {"term": "Firewall",
             "definition": "A network security system that monitors and controls incoming and outgoing network traffic.",
             "topic_key": "computer"},
            {"term": "Cryptography", "definition": "The practice and study of techniques for secure communication.",
             "topic_key": "computer"},
            {"term": "Protocol",
             "definition": "A set of rules governing the exchange or transmission of data between devices.",
             "topic_key": "computer"},
            {"term": "Bandwidth", "definition": "The maximum rate of data transfer across a given path.",
             "topic_key": "computer"},
            {"term": "Interface",
             "definition": "A shared boundary across which two or more separate components of a computer system exchange information.",
             "topic_key": "computer"},

            # SCHOOL
            {"term": "Curriculum", "definition": "The subjects comprising a course of study in a school or college.",
             "topic_key": "school"},
            {"term": "Syllabus", "definition": "An outline of the subjects in a course of study or teaching.",
             "topic_key": "school"},
            {"term": "Prerequisite",
             "definition": "A thing that is required as a prior condition for something else to happen or exist.",
             "topic_key": "school"},
            {"term": "Undergraduate", "definition": "A university student who has not yet taken a first degree.",
             "topic_key": "school"},
            {"term": "Dissertation",
             "definition": "A long essay on a particular subject, especially one written as a requirement for a university degree.",
             "topic_key": "school"},
            {"term": "Faculty", "definition": "The teaching or research staff of a university or college.",
             "topic_key": "school"},
            {"term": "Transcript",
             "definition": "An official record of a student's work, showing courses taken and grades achieved.",
             "topic_key": "school"},
            {"term": "Tuition",
             "definition": "A sum of money charged for teaching or instruction by a school, college, or university.",
             "topic_key": "school"},
            {"term": "Scholarship",
             "definition": "A grant or payment made to support a student's education, awarded on the basis of academic or other achievement.",
             "topic_key": "school"},
            {"term": "Campus", "definition": "The grounds and buildings of a university or college.",
             "topic_key": "school"},
            {"term": "Lecture",
             "definition": "An educational talk to an audience, especially to students in a university or college.",
             "topic_key": "school"},
            {"term": "Seminar",
             "definition": "A class at a university in which a topic is discussed by a teacher and a small group of students.",
             "topic_key": "school"},
            {"term": "Plagiarism",
             "definition": "The practice of taking someone else's work or ideas and passing them off as one's own.",
             "topic_key": "school"},
            {"term": "Alumni",
             "definition": "Graduates or former students of a particular school, college, or university.",
             "topic_key": "school"},
            {"term": "Dormitory", "definition": "A large bedroom for a number of people in a school or institution.",
             "topic_key": "school"},
            {"term": "Enroll",
             "definition": "Officially register as a member of an institution or a student on a course.",
             "topic_key": "school"},
            {"term": "Major", "definition": "A student's principal subject or course of study.", "topic_key": "school"},
            {"term": "Assignment",
             "definition": "A task or piece of work allocated to someone as part of a course of study.",
             "topic_key": "school"},
            {"term": "Semester", "definition": "A half-year term in a school or university.", "topic_key": "school"},
            {"term": "GPA",
             "definition": "Grade Point Average; a number representing the average value of the accumulated final grades earned.",
             "topic_key": "school"},

            # FOOTBALL
            {"term": "Pitch", "definition": "The field on which football is played.", "topic_key": "football"},
            {"term": "Referee", "definition": "The official who controls the match and enforces the rules.",
             "topic_key": "football"},
            {"term": "Striker", "definition": "A forward player whose primary role is to score goals.",
             "topic_key": "football"},
            {"term": "Defender", "definition": "A player whose primary role is to stop the opposing team from scoring.",
             "topic_key": "football"},
            {"term": "Midfielder",
             "definition": "A player positioned between the defenders and strikers, involved in both attack and defense.",
             "topic_key": "football"},
            {"term": "Offside",
             "definition": "An infraction when an attacking player is nearer to the opponent's goal line than both the ball and the second-last opponent.",
             "topic_key": "football"},
            {"term": "Penalty",
             "definition": "A free kick taken from the penalty spot, awarded for a foul in the penalty area.",
             "topic_key": "football"},
            {"term": "Tackle", "definition": "The act of taking the ball away from an opposing player.",
             "topic_key": "football"},
            {"term": "Manager",
             "definition": "The person responsible for the training, strategy, and selection of the team.",
             "topic_key": "football"},
            {"term": "Derby", "definition": "A match between two rival teams from the same city or region.",
             "topic_key": "football"},
            {"term": "Clean Sheet",
             "definition": "When a team or goalkeeper does not concede any goals during a match.",
             "topic_key": "football"},
            {"term": "Equalizer", "definition": "A goal that makes the score level.", "topic_key": "football"},
            {"term": "Formation", "definition": "The way players are positioned on the pitch.",
             "topic_key": "football"},
            {"term": "Substitute", "definition": "A player who replaces another player on the pitch during the game.",
             "topic_key": "football"},
            {"term": "Fixture", "definition": "A scheduled match.", "topic_key": "football"},
            {"term": "Touchline", "definition": "The lines marking the side boundaries of the pitch.",
             "topic_key": "football"},
            {"term": "Header", "definition": "A shot or pass made by hitting the ball with the head.",
             "topic_key": "football"},
            {"term": "Booking", "definition": "When the referee shows a yellow card to a player for an offense.",
             "topic_key": "football"},
            {"term": "Captain", "definition": "The player chosen to lead the team on the pitch.",
             "topic_key": "football"},
            {"term": "Stadium", "definition": "The venue where the football match is played.", "topic_key": "football"}
        ]

        words_added = 0
        for item in seed_data:
            existing_word = Word.query.filter_by(term=item["term"], user_id=test_user.id).first()
            if not existing_word:
                target_topic = topics_dict[item["topic_key"]]
                new_word = Word(
                    user_id=test_user.id,
                    topic_id=target_topic.id,
                    term=item["term"],
                    definition=item["definition"]
                )
                db.session.add(new_word)
                words_added += 1

        db.session.commit()
        print(
            f"Successfully added {words_added} new words under {len(topic_names)} topics for user '{test_user.username}'!")


if __name__ == '__main__':
    seed_database()