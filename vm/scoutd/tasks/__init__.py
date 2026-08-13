"""Scheduled jobs. Each module exposes run(args) -> dict.

The returned dict is the job's report to the supervision envelope:

    ok        bool, default True. False sends an alert.
    message   one line a human should read. Ends up in the email subject line
              area and in the heartbeat summary, so write it for someone who is
              away from a laptop.
    event     dedupe key for the alert, default "<task>-failed". Keep it stable;
              it is what stops one fault becoming a hundred emails.
    severity  "error" (default) or "warn" for something degraded but working.

Anything else in the dict is carried through to the heartbeat detail and the
alert body, so put the numbers that make the message checkable in there.
"""
