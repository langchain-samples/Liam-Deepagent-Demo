from managed_deepagents import channels

channel = channels.slack(
    name="Research Agent",
    description="Researches topics on the web and writes cited reports and social posts",
    icon="research-agent.png",  # 512x512 PNG, max 1 MB, path relative to channels/
    background_color="#1d4ed8",
)
