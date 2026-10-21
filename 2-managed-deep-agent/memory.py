from managed_deepagents import MemoryLayer, define_memory

memory = define_memory(
    agent=MemoryLayer(),  # /memories/agent/ - shared by every caller of the deployment
    user=MemoryLayer(),  # /memories/user/  - private to each signed-in person (Studio, Slack DMs)
)
