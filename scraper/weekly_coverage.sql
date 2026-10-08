-- Apply explicitly before enabling weekly_coverage.py; no automatic production DDL.
CREATE TABLE IF NOT EXISTS public.scrape_week_plans (
  week_start DATE PRIMARY KEY,
  plan_hash TEXT NOT NULL,
  manifest JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS public.scrape_week_tasks (
  task_id TEXT PRIMARY KEY,
  week_start DATE NOT NULL REFERENCES public.scrape_week_plans(week_start),
  due_date DATE NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('list','detail')),
  path TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','RUNNING','RETRY','DONE','EXHAUSTED')),
  attempts INTEGER NOT NULL DEFAULT 0,
  lease_token TEXT,
  lease_until TIMESTAMPTZ,
  next_attempt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  result JSONB,
  last_error TEXT,
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS scrape_week_tasks_due
  ON public.scrape_week_tasks(status,due_date,next_attempt);
ALTER TABLE public.scrape_week_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scrape_week_tasks ENABLE ROW LEVEL SECURITY;
-- No public policies. Use a restricted operational database role.
CREATE TABLE IF NOT EXISTS public.scrape_worker_health (
  component TEXT PRIMARY KEY,
  checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status TEXT NOT NULL,
  detail JSONB NOT NULL DEFAULT '{}'::JSONB
);
ALTER TABLE public.scrape_worker_health ENABLE ROW LEVEL SECURITY;
