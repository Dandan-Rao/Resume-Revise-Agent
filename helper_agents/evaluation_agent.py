from pydantic import BaseModel
from agents import Agent


class EvaluationResult(BaseModel):
    content_score: int
    expression_score: int


with open("./prompts/resume_evaluation_instruction.md", "r") as f:
    instructions = f.read()

# Use GPT-4o for this task
# Slightly better reasoning but more expensive
evaluation_agent = Agent(
    name="EvaluationAgent",
    instructions=instructions,
    model="gpt-4o",
    output_type=EvaluationResult,
)
