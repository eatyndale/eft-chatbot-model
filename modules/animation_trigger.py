import os

# Map tapping points to absolute GIF filenames
TAPPING_POINTS = {
    "top of head": os.path.abspath("static/animations/top_of_head.gif"),
    "eyebrow": os.path.abspath("static/animations/eyebrow.gif"), 
    "side of eye": os.path.abspath("static/animations/side_of_eye.gif"),
    "under eye": os.path.abspath("static/animations/under_eye.gif"),
    "under nose": os.path.abspath("static/animations/under_nose.gif"),
    "chin": os.path.abspath("static/animations/chin.gif"),
    "collarbone": os.path.abspath("static/animations/collarbone.gif"),
    "under arm": os.path.abspath("static/animations/under_arm.gif"),
    "karate chop": os.path.abspath("static/animations/karate_chop.gif")  # New addition
}

# Add at the top of the file
print("Animation directory contents:")
animation_dir = os.path.abspath("static/animations")
if os.path.exists(animation_dir):
    print(f"Directory exists: {animation_dir}")
    print(os.listdir(animation_dir))
else:
    print(f"Directory NOT found: {animation_dir}")

# Then update the detect_animation function
def detect_animation(message_text):
    message_lower = message_text.lower()
    print(f"Looking for animation in: {message_text}")
    
    for point, path in TAPPING_POINTS.items():
        print(f"Checking if '{point}' is in message...")
        if point in message_lower:
            print(f"Match found for '{point}'!")
            if os.path.exists(path):
                print(f"Animation file exists: {path}")
                return path
            else:
                print(f"ERROR: Animation file NOT found at: {path}")
    
    print("No matching animation found")
    return None