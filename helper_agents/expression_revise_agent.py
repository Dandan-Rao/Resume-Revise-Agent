from agents import Agent
from helper_agents.resume_parser_agent import ResumeItem

with open("./prompts/resume_expression_revise_instruction.md", "r") as f:
    instructions = f.read()

# Use GPT-4o for this task
# Slightly better reasoning but more expensive
expression_revise_agent = Agent(
    name="expression_revise_agent",
    instructions=instructions,
    model="gpt-4o",
    output_type=ResumeItem,
)
