from fastapi import APIRouter, Depends, HTTPException, status

from app.api.utils import serialize_template
from app.db import Client, get_supabase
from app.deps import get_current_user
from app.schemas import TemplateCreate, TemplatePublic, TemplateUpdate

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplatePublic])
def list_templates(
    supabase: Client = Depends(get_supabase), current_user: dict = Depends(get_current_user)
):
    response = (
        supabase.table("templates")
        .select(
            "id,user_id,name,notes,created_at,template_exercises(id,exercise_id,sort_order,template_sets(id,set_order,target_reps,target_weight,set_type))"
        )
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    templates = [
        {
            **t,
            "exercises": [
                {**ex, "sets": ex.get("template_sets") or []}
                for ex in (t.get("template_exercises") or [])
            ],
        }
        for t in (response.data or [])
    ]
    return [serialize_template(t) for t in templates]


@router.get("/{template_id}", response_model=TemplatePublic)
def get_template(
    template_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    response = (
        supabase.table("templates")
        .select(
            "id,user_id,name,notes,created_at,template_exercises(id,exercise_id,sort_order,template_sets(id,set_order,target_reps,target_weight,set_type))"
        )
        .eq("id", template_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    template = response.data[0] if response.data else None
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template["exercises"] = [
        {**ex, "sets": ex.get("template_sets") or []}
        for ex in (template.get("template_exercises") or [])
    ]
    return serialize_template(template)


def _insert_template_exercises(supabase: Client, template_id: int, exercises_in: list):
    for ex in exercises_in:
        ex_row = (
            supabase.table("template_exercises")
            .insert(
                {
                    "template_id": template_id,
                    "exercise_id": ex.exercise_id,
                    "sort_order": ex.sort_order,
                }
            )
            .execute()
        )
        if not ex_row.data:
            continue
        template_exercise_id = ex_row.data[0]["id"]
        if ex.sets:
            supabase.table("template_sets").insert(
                [
                    {
                        "template_exercise_id": template_exercise_id,
                        "set_order": s.set_order,
                        "target_reps": s.target_reps,
                        "target_weight": s.target_weight,
                        "set_type": s.set_type,
                    }
                    for s in ex.sets
                ]
            ).execute()


@router.post("", response_model=TemplatePublic, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    created = (
        supabase.table("templates")
        .insert(
            {
                "user_id": current_user["id"],
                "name": payload.name,
                "notes": payload.notes,
            }
        )
        .execute()
    )
    if not created.data:
        raise HTTPException(status_code=500, detail="Failed to create template")
    template_id = created.data[0]["id"]
    _insert_template_exercises(supabase, template_id, payload.exercises)
    return get_template(template_id, supabase, current_user)


@router.patch("/{template_id}", response_model=TemplatePublic)
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    existing = (
        supabase.table("templates")
        .select("id")
        .eq("id", template_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Template not found")

    updates: dict = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.notes is not None:
        updates["notes"] = payload.notes

    if updates:
        supabase.table("templates").update(updates).eq("id", template_id).eq(
            "user_id", current_user["id"]
        ).execute()

    if payload.exercises is not None:
        existing_ex = (
            supabase.table("template_exercises")
            .select("id")
            .eq("template_id", template_id)
            .execute()
        )
        for ex in (existing_ex.data or []):
            supabase.table("template_sets").delete().eq(
                "template_exercise_id", ex["id"]
            ).execute()
        supabase.table("template_exercises").delete().eq("template_id", template_id).execute()
        _insert_template_exercises(supabase, template_id, payload.exercises)

    return get_template(template_id, supabase, current_user)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    existing = (
        supabase.table("templates")
        .select("id")
        .eq("id", template_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Template not found")
    supabase.table("templates").delete().eq("id", template_id).eq(
        "user_id", current_user["id"]
    ).execute()
