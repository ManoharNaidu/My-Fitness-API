from app.schemas import (
    SessionExerciseOut,
    SessionPublic,
    SessionSetOut,
    TemplateExerciseOut,
    TemplatePublic,
    TemplateSetOut,
)


def serialize_template(template: dict) -> TemplatePublic:
    exercises = []
    for ex in sorted(template.get("exercises") or [], key=lambda x: x.get("sort_order", 0)):
        sets = [
            TemplateSetOut(
                id=s["id"],
                set_order=s["set_order"],
                target_reps=s["target_reps"],
                target_weight=s["target_weight"],
                set_type=s["set_type"],
            )
            for s in sorted(ex.get("sets") or [], key=lambda x: x.get("set_order", 0))
        ]
        exercises.append(
            TemplateExerciseOut(
                id=ex["id"],
                exercise_id=ex["exercise_id"],
                sort_order=ex["sort_order"],
                sets=sets,
            )
        )

    return TemplatePublic(
        id=template["id"],
        user_id=template["user_id"],
        name=template["name"],
        notes=template.get("notes"),
        created_at=template["created_at"],
        exercises=exercises,
    )


def serialize_session(session: dict) -> SessionPublic:
    exercises = []
    for ex in sorted(session.get("exercises") or [], key=lambda x: x.get("sort_order", 0)):
        sets = [
            SessionSetOut(
                id=s["id"],
                set_order=s["set_order"],
                reps=s["reps"],
                weight=s["weight"],
                completed=s["completed"],
                set_type=s["set_type"],
            )
            for s in sorted(ex.get("sets") or [], key=lambda x: x.get("set_order", 0))
        ]
        exercises.append(
            SessionExerciseOut(
                id=ex["id"],
                exercise_id=ex["exercise_id"],
                sort_order=ex["sort_order"],
                sets=sets,
            )
        )

    return SessionPublic(
        id=session["id"],
        user_id=session["user_id"],
        template_id=session.get("template_id"),
        template_name_snapshot=session["template_name_snapshot"],
        status=session["status"],
        started_at=session["started_at"],
        ended_at=session.get("ended_at"),
        duration_seconds=session.get("duration_seconds"),
        notes=session.get("notes"),
        exercises=exercises,
    )
