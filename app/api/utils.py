from app.models import WorkoutSessionDB, WorkoutTemplate
from app.schemas import (
    SessionExerciseOut,
    SessionPublic,
    SessionSetOut,
    TemplateExerciseOut,
    TemplatePublic,
    TemplateSetOut,
)


def serialize_template(template: WorkoutTemplate) -> TemplatePublic:
    exercises = []
    for ex in sorted(template.exercises, key=lambda x: x.sort_order):
        sets = [
            TemplateSetOut(
                id=s.id,
                set_order=s.set_order,
                target_reps=s.target_reps,
                target_weight=s.target_weight,
                set_type=s.set_type,
            )
            for s in sorted(ex.sets, key=lambda x: x.set_order)
        ]
        exercises.append(
            TemplateExerciseOut(
                id=ex.id, exercise_id=ex.exercise_id, sort_order=ex.sort_order, sets=sets
            )
        )

    return TemplatePublic(
        id=template.id,
        user_id=template.user_id,
        name=template.name,
        notes=template.notes,
        created_at=template.created_at,
        exercises=exercises,
    )


def serialize_session(session: WorkoutSessionDB) -> SessionPublic:
    exercises = []
    for ex in sorted(session.exercises, key=lambda x: x.sort_order):
        sets = [
            SessionSetOut(
                id=s.id,
                set_order=s.set_order,
                reps=s.reps,
                weight=s.weight,
                completed=s.completed,
                set_type=s.set_type,
            )
            for s in sorted(ex.sets, key=lambda x: x.set_order)
        ]
        exercises.append(
            SessionExerciseOut(
                id=ex.id, exercise_id=ex.exercise_id, sort_order=ex.sort_order, sets=sets
            )
        )

    return SessionPublic(
        id=session.id,
        user_id=session.user_id,
        template_id=session.template_id,
        template_name_snapshot=session.template_name_snapshot,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        notes=session.notes,
        exercises=exercises,
    )
