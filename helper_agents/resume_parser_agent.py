from pydantic import BaseModel
from agents import Agent
import os
import docx
from typing import List

#! brew install graphicsmagick
#! pip install py-zerox
#! brew install poppler
from pyzerox import zerox


async def file_to_markdown(file_path, output_path):
    """Convert files to markdown. Local filepath and file URL supported"""
    # Ensure parent directory exists

    # If output file already exists, you may choose to overwrite or skip
    if os.path.isfile(output_path):
        return "The output file already exists, no conversion"
    if file_path.endswith(".md"):
        with open(file_path, "r") as f, open(output_path, "w") as out_f:
            out_f.write(f.read())
            return "Conversion done"
    if file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        txt = "\n".join([p.text for p in doc.paragraphs])
        # save the txt to a md file
        with open(output_path, "w") as f:
            f.write(txt)
        return "Conversion done"

    model = "gpt-4o-mini"
    custom_system_prompt = """
            You are a resume parser. Extract the text from the PDF, 
            preserving headings, bullet points, and tables. 
            Return the output in Markdown format.
        """
    kwargs = {}
    # select_pages = None
    await zerox(
        file_path=file_path,
        model=model,
        output_dir=output_path,
        custom_system_prompt=custom_system_prompt,
        **kwargs
    )
    return "Conversion done"


class Project(BaseModel):
    title: str
    "The title of the project, should be titles like Data Scientist, Software Engineer, AI Engineer"
    company: str
    "The company where the project was developed"
    project_name: str
    "The name of the project"
    description: List[str]
    "some bullet points describe the project"
    location: str
    "The location of the job"


class ResumeItem(BaseModel):
    summary: str
    "The summary section of the resume"

    hard_skills: List[str]
    "The hard skills included in the resume"

    projects: List[Project]
    "All the projects included in the resume"


with open("./prompts/resume_parser_instruction.md", "r") as f:
    instructions = f.read()

# Use GPT-4o-mini for this task
# More cost-effective for high-volume processing
# Still good at structured extraction
resume_parser_agent = Agent(
    name="ResumeParser",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=ResumeItem,
)
