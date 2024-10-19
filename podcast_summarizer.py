from langchain_community.document_loaders import ObsidianLoader
from datetime import datetime, timedelta
import ell
from dotenv import load_dotenv

load_dotenv()

ell.init(store='./logdir', autocommit=True, verbose=True)

# Initialize the ObsidianLoader with the specified directory
obsidian_loader = ObsidianLoader(
    "/Users/danielmcateer/Library/Mobile Documents/iCloud~md~obsidian/Documents/Ideaverse/Readwise/Podcasts"
)

# Load the documents from the Obsidian vault
documents = obsidian_loader.load()

# Get the current date
current_date = datetime.now().date()

# Calculate the date 7 days ago
seven_days_ago = current_date - timedelta(days=7)

# Filter documents updated within the last 7 days
recent_documents = []
for doc in documents:
    if 'last_modified' in doc.metadata:
        try:
            updated_date = datetime.fromtimestamp(doc.metadata['last_modified']).date()
            if updated_date > seven_days_ago:
                recent_documents.append(doc)
        except (ValueError, TypeError):
            print(f"Invalid date format for document: {doc.metadata}")
    else:
        print(f"'last_modified' field missing for document: {doc.metadata}")

print(f"Number of documents updated in the last 7 days: {len(recent_documents)}")

@ell.simple(model="gpt-4o")
def extract_summary(notes: str) -> str:
    """
    Summarize the podcast notes.
    The notes are in the format of a podcast transcript with metadata at the top.
    The summaries should especially focus on the highlights and key ideas and insights.
    Return the summary as a markdown formatted string.
    """
    # Your logic to summarize goes here
    return f"Summarize the podcast notes here: {notes}"

summaries = []

for doc in recent_documents:
    notes = doc.page_content
    metadata = {}
    for line in notes.split('\n'):
        if line.startswith('Title:'):
            metadata['title'] = line.split(':', 1)[1].strip()
        elif line.startswith('Source URL:'):
            metadata['source_url'] = line.split(':', 1)[1].strip()
        elif line.startswith('Authors:'):
            metadata['authors'] = line.split(':', 1)[1].strip()
    
    summary = extract_summary(notes)
    summaries.append(
        f"## {metadata['title'].strip('[]')}\n\n"
        f"[Source]({metadata['source_url']})\n\n"
        f"### Summary\n\n{summary}\n\n"
        f"**Authors:** {metadata['authors'].strip('[]')}\n\n"
        f"---\n\n"
    )

with open('summarized_podcasts.md', 'w') as f:
    f.write("# Summarized Podcasts\n\n")
    f.writelines(summaries)
    
    print("Summarized Podcasts:")
    with open('summarized_podcasts.md', 'r') as f:
        print(f.read())
