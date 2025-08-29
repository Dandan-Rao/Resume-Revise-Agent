from pydantic import BaseModel
from agents import Agent
import os
import warnings

warnings.filterwarnings("ignore")
import os
import openai

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from typing import List

openai.api_key = os.getenv("OPENAI_API_KEY")


def web_scraper_tool(url: str) -> str:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)  # Wait for JS to load

    try:
        job_desc_element = driver.find_element(By.TAG_NAME, "body")
        job_desc_text = job_desc_element.text
    except Exception as e:
        job_desc_text = f"Error: {e}"
    driver.quit()
    return job_desc_text


class JDItem(BaseModel):
    company_description: str
    "The company description extracted from the job description, including location, remote work options, company name, and main business focus."

    soft_skills: List[str]
    "The soft skills included in the job description, such as communication, teamwork, and problem-solving abilities."

    hard_skills: List[str]
    "The hard skills included in the job description, such as programming languages, tools, and technologies."

    job_responsibilities: str
    "All the job responsibilities included in the job description"

    keywords: List[str]
    "All the keywords included in the job description, "

    citizenship_requirements: bool
    "Whether U.S. citizenship is required for the job, return True if required, otherwise return False."


with open("./prompts/jd_parser_instruction.md", "r") as f:
    instructions = f.read()

# Use GPT-4o-mini for this task
# More cost-effective for high-volume processing
# Still good at structured extraction
jd_parser_agent = Agent(
    name="JD Parser Agent",
    model="gpt-4o-mini",
    instructions=instructions,
    output_type=JDItem,
)
