from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import (
    Exercise,
    TemplateExercise,
    TemplateSet,
    User,
    WorkoutTemplate,
)


def seed_database(db: Session) -> None:
    existing_user = db.query(User).filter(User.email == "demo@myfitness.app").first()
    if existing_user:
        return

    demo_user = User(
        email="demo@myfitness.app",
        password_hash=get_password_hash("demo1234"),
        display_name="Demo User",
        units="kg",
        default_rest_seconds=90,
    )
    db.add(demo_user)
    db.flush()

    global_exercises = [
        Exercise(name="Barbell Bench Press", primary_muscle="Chest", equipment="Barbell"),
        Exercise(name="Barbell Row", primary_muscle="Back", equipment="Barbell"),
        Exercise(name="Back Squat", primary_muscle="Legs", equipment="Barbell"),
        Exercise(name="Deadlift", primary_muscle="Posterior Chain", equipment="Barbell"),
        Exercise(name="Overhead Press", primary_muscle="Shoulders", equipment="Barbell"),
        Exercise(name="Pull-up", primary_muscle="Back", equipment="Bodyweight"),
    ]
    db.add_all(global_exercises)
    db.flush()

    push_day = WorkoutTemplate(user_id=demo_user.id, name="Push Day", notes="Chest/Shoulders")
    bench = TemplateExercise(exercise_id=global_exercises[0].id, sort_order=0)
    bench.sets = [
        TemplateSet(set_order=1, target_reps=8, target_weight=60, set_type="normal"),
        TemplateSet(set_order=2, target_reps=8, target_weight=60, set_type="normal"),
        TemplateSet(set_order=3, target_reps=6, target_weight=65, set_type="normal"),
    ]
    ohp = TemplateExercise(exercise_id=global_exercises[4].id, sort_order=1)
    ohp.sets = [
        TemplateSet(set_order=1, target_reps=8, target_weight=35, set_type="normal"),
        TemplateSet(set_order=2, target_reps=8, target_weight=35, set_type="normal"),
        TemplateSet(set_order=3, target_reps=6, target_weight=37.5, set_type="normal"),
    ]
    push_day.exercises = [bench, ohp]
    db.add(push_day)

    db.commit()
