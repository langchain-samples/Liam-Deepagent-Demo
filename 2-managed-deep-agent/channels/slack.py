from managed_deepagents import channels

channel = channels.slack(
    name="Research Agent",
    description="Researches topics on the web and writes cited reports and social posts",
)
