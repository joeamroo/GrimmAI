# NOTE: After writng the initial prompts, all prompts were imporved with GPT-4.1.
# WARNING: The test API key below is for quick demo ONLY! Remove/comment out before final use/submission!
import os
import openai
import datetime
import json
from typing import Dict, Any

# ----------- Agent role definition prompts -------------
STORYTELLER_PROMPT = """
You are a master storyteller for children aged 5-10. Use age-appropriate language, a clear story arc, and embed a fun or meaningful lesson. Respond ONLY with the story, no extra commentary.
"""
JUDGE_PROMPT = """
You are the Grimm Brothers, world-famous story critics. Rate the following story for:
1. Structure (beginning, middle, end)
2. Engagement (is it fun/scary etc for kids 5-10?)
3. Moral/Lesson (is it clear/age-appropriate?)
4. Appropriateness (well-suited for a child age 5-10?)
List points that need improvement. Give a final verdict: Accept, Minor Revisions, or Major Revisions.

STORY:
{{story}}
"""
CLASSIFIER_PROMPT = """
Classify the following story (choose ALL that apply): fun, scary, fantasy, realistic, educational, adventure.
Then, in 1 short sentence, state the main lesson or moral. Respond as JSON with keys 'genres' (list), 'lesson' (string).

STORY:
{{story}}
"""
// OpenAI API key
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "###")
client = openai.OpenAI(api_key=OPENAI_KEY)

def call_model(prompt: str, max_tokens=1000, temperature=0.7) -> str:
    # Call OpenAI chat API 
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content

def get_story(user_request: str, fantasy_world: Dict[str, Any] = None) -> str:
    # Compose the story prompt, optionally including fantasy world info
    if fantasy_world:
        preamble = f"Story set in the fantasy world: {fantasy_world['name']}. "\
                   f"The main characters are: {', '.join(fantasy_world['characters'])}. "\
                   f"Special rules: {fantasy_world['rules']}. "
        prompt = f"{STORYTELLER_PROMPT}\n{preamble}\nUser Request: {user_request}"
    else:
        prompt = f"{STORYTELLER_PROMPT}\nUser Request: {user_request}"
    return call_model(prompt)

def judge_story(story: str) -> str:
    # Judge the story using the Grimm Brothers agent
    filled = JUDGE_PROMPT.replace("{{story}}", story)
    return call_model(filled, max_tokens=700)

def classify_story(story: str) -> Dict[str, Any]:
    # Classify the story and extract its lesson
    import ast
    filled = CLASSIFIER_PROMPT.replace("{{story}}", story)
    resp = call_model(filled, max_tokens=400, temperature=0.3)
    try:
        return json.loads(resp)
    except Exception:
        try:
            return ast.literal_eval(resp)
        except Exception:
            return {"genres": [], "lesson": "Could not parse."}

def save_story(data: Dict[str, Any], filename=None):
    # Save accepted story as a JSON file
    if not filename:
        fn = data.get('story_title', 'story').replace(' ', '_')
        filename = f"stories/{fn}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    os.makedirs("stories", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def input_fantasy_world() -> Dict[str, Any]:
    # Gather info for co-creation mode
    print("\nLet's create your fantasy world!")
    name = input("World name: ")
    chars = input("List main characters (comma separated): ").split(",")
    rules = input("Briefly describe special rules or magic in your world: ")
    return {"name": name, "characters": [c.strip() for c in chars], "rules": rules}

def main():
    print("\n--- Bedtime Story Generator ---")
    mode = input("Choose mode: 1=Normal story, 2=Fantasy World co-creation: ")
    fantasy = None
    if mode.strip() == "2":
        fantasy = input_fantasy_world()
        print(f"\nWorld '{fantasy['name']}' is ready!")
        # Fantasy mode: back-and-forth
        conversation = [
            {"role": "system", "content": f"You are a storyteller inside the fantasy world '{fantasy['name']}' with rules: {fantasy['rules']}. Main characters: {', '.join(fantasy['characters'])}. Always keep the world logic and rules!"}
        ]
        print("Type anything to interact with the world. Type 'exit' to end co-creation and save story.")
        while True:
            user_turn = input("You: ")
            if user_turn.strip().lower() == 'exit':
                break
            conversation.append({"role": "user", "content": user_turn})
            ai_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation,
                max_tokens=400,
                temperature=0.85,
            )
            ai_text = ai_response.choices[0].message.content
            print(f"AI: {ai_text}\n")
            conversation.append({"role": "assistant", "content": ai_text})
        # Save the back-and-forth as a story
        transcript = '\n'.join([
            f"{m['role'].capitalize()}: {m['content']}" for m in conversation if m['role'] in ('user','assistant')
        ])
        meta = {"fantasy_world": fantasy, "transcript": transcript, "datetime": datetime.datetime.now().isoformat()}
        save_story(meta)
        print('Fantasy session saved.')
        return

    user_request = input("What kind of story do you want to hear? ")
    story = get_story(user_request, fantasy)
    print(f"\n--- Your Story ---\n{story}\n")

    while True:
        judge_feedback = judge_story(story)
        print(f"\n--- Grimm Brothers Judge ---\n{judge_feedback}\n")
        if "Accept" in judge_feedback:
            print("The Grimm Brothers have accepted your story!")
            break
        elif "Major Revisions" in judge_feedback:
            change = input("Major revisions suggested. New story? (y/n): ")
            if change.lower().startswith('y'):
                story = get_story(user_request, fantasy)
                continue
            break
        else:
            minor = input("Minor revisions suggested. Re-generate? (y/n): ")
            if minor.lower().startswith("y"):
                story = get_story(user_request, fantasy)
                continue
            break

    meta = classify_story(story)
    print(f"\n--- Story Classification ---\nGenres: {', '.join(meta['genres'])}\nLesson: {meta['lesson']}\n")

    data = {"author": "Youssef Ateya", "contact": "yousefamrzagazig@gmail.com", "story": story, "judge_feedback": judge_feedback, "user_request": user_request, "classification": meta, "datetime": datetime.datetime.now().isoformat()}
    save_story(data)
    print("Story saved.")

if __name__ == "__main__":
    main()