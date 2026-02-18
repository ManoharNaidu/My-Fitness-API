-- My Fitness API - Supabase/Postgres schema
-- Run this in Supabase SQL Editor.

begin;

-- =========
-- Core users
-- =========
create table if not exists public.users (
  id bigserial primary key,
  email varchar(255) not null unique,
  password_hash varchar(255) not null,
  display_name varchar(120) not null,
  units varchar(8) not null default 'kg' check (units in ('kg','lb')),
  default_rest_seconds integer not null default 90,
  created_at timestamptz not null default now()
);

create index if not exists idx_users_email on public.users(email);

-- ===========
-- Exercises
-- ===========
create table if not exists public.exercises (
  id bigserial primary key,
  owner_user_id bigint references public.users(id) on delete set null,
  name varchar(150) not null,
  primary_muscle varchar(80) not null,
  equipment varchar(80) not null,
  is_custom boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists idx_exercises_owner_user_id on public.exercises(owner_user_id);
create index if not exists idx_exercises_name on public.exercises(name);

-- ===========
-- Templates
-- ===========
create table if not exists public.templates (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  name varchar(120) not null,
  notes text,
  created_at timestamptz not null default now()
);

create index if not exists idx_templates_user_id on public.templates(user_id);
create index if not exists idx_templates_created_at on public.templates(created_at desc);

create table if not exists public.template_exercises (
  id bigserial primary key,
  template_id bigint not null references public.templates(id) on delete cascade,
  exercise_id bigint not null references public.exercises(id),
  sort_order integer not null default 0
);

create index if not exists idx_template_exercises_template_id on public.template_exercises(template_id);
create index if not exists idx_template_exercises_exercise_id on public.template_exercises(exercise_id);

create table if not exists public.template_sets (
  id bigserial primary key,
  template_exercise_id bigint not null references public.template_exercises(id) on delete cascade,
  set_order integer not null,
  target_reps integer not null,
  target_weight double precision not null,
  set_type varchar(16) not null default 'normal'
    check (set_type in ('normal','warmup','failure','drop'))
);

create index if not exists idx_template_sets_template_exercise_id on public.template_sets(template_exercise_id);

-- ==========
-- Sessions
-- ==========
create table if not exists public.sessions (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  template_id bigint references public.templates(id) on delete set null,
  template_name_snapshot varchar(120) not null default 'Quick Workout',
  status varchar(16) not null default 'active'
    check (status in ('active','completed','cancelled')),
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  duration_seconds integer,
  notes text
);

create index if not exists idx_sessions_user_id_started_at on public.sessions(user_id, started_at desc);
create index if not exists idx_sessions_status on public.sessions(status);

create table if not exists public.session_exercises (
  id bigserial primary key,
  session_id bigint not null references public.sessions(id) on delete cascade,
  exercise_id bigint not null references public.exercises(id),
  sort_order integer not null default 0
);

create index if not exists idx_session_exercises_session_id on public.session_exercises(session_id);
create index if not exists idx_session_exercises_exercise_id on public.session_exercises(exercise_id);

create table if not exists public.session_sets (
  id bigserial primary key,
  session_exercise_id bigint not null references public.session_exercises(id) on delete cascade,
  set_order integer not null,
  reps integer not null,
  weight double precision not null,
  completed boolean not null default false,
  set_type varchar(16) not null default 'normal'
    check (set_type in ('normal','warmup','failure','drop'))
);

create index if not exists idx_session_sets_session_exercise_id on public.session_sets(session_exercise_id);

-- ===========
-- Nutrition
-- ===========
create table if not exists public.meal_logs (
  id bigserial primary key,
  user_id bigint not null references public.users(id) on delete cascade,
  meal_name varchar(150) not null,
  calories integer not null,
  protein_g double precision not null default 0,
  carbs_g double precision not null default 0,
  fats_g double precision not null default 0,
  eaten_at timestamptz not null default now()
);

create index if not exists idx_meal_logs_user_id on public.meal_logs(user_id);
create index if not exists idx_meal_logs_eaten_at on public.meal_logs(eaten_at desc);

commit;
