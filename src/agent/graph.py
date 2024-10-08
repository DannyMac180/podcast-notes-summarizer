from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import List, Dict
import datetime
import re

# Define the state
class PodcastNotesState(BaseModel):
    recent_note_titles: List[str] = Field(default_factory=list)
    collected_notes: List[str] = Field(default_factory=list)
    summary: str = ""

# Node 1: Get recent podcast notes
@tool
def get_recent_podcast_notes(state: PodcastNotesState, days: int = 7) -> Dict[str, List[str]]:
    """Get podcast note titles from Obsidian that were synced in the last 7 days."""
    obsidian_dir = "/Users/danielmcateer/Library/Mobile Documents/iCloud~md~obsidian/Documents/Ideaverse/Readwise/Sync.md"
    
    recent_titles = []
    current_time = datetime.datetime.now()
    
    with open(obsidian_dir, 'r') as file:
        content = file.read()
        notes = content.split('---')
        
        for note in notes:
            match = re.search(r'synced_date:\s*(\d{4}-\d{2}-\d{2})', note)
            if match:
                synced_date = datetime.datetime.strptime(match.group(1), '%Y-%m-%d')
                if (current_time - synced_date).days <= days:
                    title_match = re.search(r'title:\s*(.*)', note)
                    if title_match:
                        recent_titles.append(title_match.group(1))
    
    return {"recent_note_titles": recent_titles}

# Node 2: Collect notes
@tool
def collect_notes(state: PodcastNotesState, titles: List[str]) -> Dict[str, List[str]]:
    """Collect full notes for the given titles."""
    obsidian_dir = "/Users/danielmcateer/Library/Mobile Documents/iCloud~md~obsidian/Documents/Ideaverse/Readwise/Sync.md"
    
    collected_notes = []
    
    with open(obsidian_dir, 'r') as file:
        content = file.read()
        notes = content.split('---')
        
        for note in notes:
            for title in titles:
                if f"title: {title}" in note:
                    collected_notes.append(note.strip())
                    break
    
    return {"collected_notes": collected_notes}

# Node 3: Summarize notes
summarize_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert at summarizing podcast notes. Your task is to analyze the given notes, identify themes, insights, and connections between them. Focus on the most important and interesting points."),
    ("human", "Here are the podcast notes to summarize:\n\n{notes}\n\nPlease provide a summary that highlights themes, insights, and connections across these notes.")
])

summarize_chain = summarize_prompt | ChatOpenAI(model="gpt-4")

def summarize_notes(state: PodcastNotesState) -> Dict[str, str]:
    notes = "\n\n".join(state.collected_notes)
    summary = summarize_chain.run({"notes": notes})
    state.summary = summary
    return state

# Define the graph
workflow = StateGraph(PodcastNotesState)

# Add nodes
workflow.add_node("get_recent_notes", get_recent_podcast_notes)
workflow.add_node("collect_notes", collect_notes)
workflow.add_node("summarize_notes", summarize_notes)

# Define edges
workflow.add_edge("get_recent_notes", "collect_notes")
workflow.add_edge("collect_notes", "summarize_notes")
workflow.add_edge("summarize_notes", END)

# Set entry point
workflow.set_entry_point("get_recent_notes")

# Compile the graph
graph = workflow.compile()