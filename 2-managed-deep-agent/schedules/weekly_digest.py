from managed_deepagents import define_schedule

schedule = define_schedule(
    cron="0 9 * * 1",
    timezone="America/Los_Angeles",
    prompt=(
        "Read /memories/agent/research_notes.md. Write a short weekly digest of the most "
        "useful research takeaways so far, then list three topics worth researching next."
    ),
)
