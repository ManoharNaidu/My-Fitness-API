from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.utils import serialize_template
from app.db import get_db
from app.deps import get_current_user
from app.models import TemplateExercise, TemplateSet, User, WorkoutTemplate
from app.schemas import TemplateCreate, TemplatePublic, TemplateUpdate

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplatePublic])
def list_templates(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    templates = (
        db.query(WorkoutTemplate)
        .options(selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.sets))
        .filter(WorkoutTemplate.user_id == current_user.id)
        .order_by(WorkoutTemplate.created_at.desc())
        .all()
    )
    return [serialize_template(t) for t in templates]


@router.get("/{template_id}", response_model=TemplatePublic)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = (
        db.query(WorkoutTemplate)
        .options(selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.sets))
        .filter(WorkoutTemplate.id == template_id, WorkoutTemplate.user_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return serialize_template(template)


def _apply_template_exercises(template: WorkoutTemplate, exercises_in: list):
    template.exercises.clear()
    for ex in exercises_in:
        ex_db = TemplateExercise(exercise_id=ex.exercise_id, sort_order=ex.sort_order)
        ex_db.sets = [
            TemplateSet(
                set_order=s.set_order,
                target_reps=s.target_reps,
                target_weight=s.target_weight,
                set_type=s.set_type,
            )
            for s in ex.sets
        ]
        template.exercises.append(ex_db)


@router.post("", response_model=TemplatePublic, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = WorkoutTemplate(
        user_id=current_user.id,
        name=payload.name,
        notes=payload.notes,
    )
    _apply_template_exercises(template, payload.exercises)
    db.add(template)
    db.commit()
    db.refresh(template)
    template = (
        db.query(WorkoutTemplate)
        .options(selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.sets))
        .filter(WorkoutTemplate.id == template.id)
        .first()
    )
    return serialize_template(template)


@router.patch("/{template_id}", response_model=TemplatePublic)
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = (
        db.query(WorkoutTemplate)
        .options(selectinload(WorkoutTemplate.exercises).selectinload(TemplateExercise.sets))
        .filter(WorkoutTemplate.id == template_id, WorkoutTemplate.user_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if payload.name is not None:
        template.name = payload.name
    if payload.notes is not None:
        template.notes = payload.notes
    if payload.exercises is not None:
        _apply_template_exercises(template, payload.exercises)

    db.add(template)
    db.commit()
    db.refresh(template)
    return serialize_template(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = (
        db.query(WorkoutTemplate)
        .filter(WorkoutTemplate.id == template_id, WorkoutTemplate.user_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
