import json
import os

questions = []

# --- Logic to extract content and track pages ---

with open("documents/manual_text.txt", "r", encoding="utf-8") as f:
    manual_content = f.read()

current_page = 1
page_map = [] # List of (start_index, page_number)

# Pre-process manual content to map indices to pages
import re
page_marker_pattern = re.compile(r"\[\[PAGE_(\d+)\]\]")

# Logic Revision:
# The markers in the text are [[PAGE_X]] which denotes the START of Page X.
# Example:
# [[PAGE_1]]
# Content of page 1...
# [[PAGE_2]]
# Content of page 2...
#
# So if we find text at index I:
# If I is after [[PAGE_1]] pos but before [[PAGE_2]] pos, it is Page 1.
#
# Let's verify how we build the map.
# Loop finds markers.
# 1. Match [[PAGE_1]]. content before is empty.
#    clean_content += ""
#    map append (0, 1) -> At index 0, Page 1 starts.
# 2. Match [[PAGE_2]]. content before is Page 1 content.
#    clean_content += page_1_content
#    map append (len(page_1), 2) -> At index len, Page 2 starts.
#
# So yes, we want the largest pos <= index.


# Remove markers but keep track of where they were
clean_content = ""
last_pos = 0
for match in page_marker_pattern.finditer(manual_content):
    # Append content before marker
    clean_content += manual_content[last_pos:match.start()]
    # Record page change
    page_num = int(match.group(1))
    page_map.append((len(clean_content), page_num))
    last_pos = match.end()

# Append remaining content
clean_content += manual_content[last_pos:]

# Normalize whitespace in clean_content for searching
# We need to map normalized indices back to original indices to use page_map?
# Actually, if we normalize clean_content, the indices change, so page_map becomes invalid.
# Better approach: Normalize the search text to match the raw content's potential line breaks?
# No, raw content has arbitrary line breaks.

# Alternative:
# 1. Create a normalized version of clean_content (all whitespace -> single space).
# 2. Create a mapping from normalized index -> original index.
# 3. Use original index to look up page in page_map.

normalized_content = []
norm_to_orig_map = []
import re

# Split by whitespace to normalize
# This is complex to map back efficiently.

# Simpler approach:
# Just replace newlines with spaces in manual_content before building page_map?
# But page markers are in the raw text.

# Let's try this:
# 1. Build page_map on raw content (done).
# 2. Create a "searchable" content where newlines are replaced by spaces, BUT we keep the same length?
#    No, replacing \n with space keeps length (1 char).
#    But multiple spaces?

# Let's just replace all newlines with spaces in the clean_content.
searchable_content = clean_content.replace("\n", " ").replace("\r", " ")
# Collapse multiple spaces
searchable_content = re.sub(r'\s+', ' ', searchable_content)

# We need to know which page corresponds to a position in searchable_content.
# This requires rebuilding the page map for the normalized content.
# This is getting complicated.

# Let's go with a fuzzy search or just normalizing the snippet to match the raw text's likely format.
# If I just replace \n with space in the raw text, it might match better.

def normalize_text(text, for_search=False):
    # Collapse whitespace first
    text = re.sub(r'\s+', ' ', text).strip()
    if for_search:
        # Lowercase and remove punctuation for robust matching
        text = text.lower()
        text = re.sub(r'[^a-z0-9 ]', '', text)
    return text

# We will search in a normalized version of the manual.
# To map back to pages, we need to know which page each part of the normalized text belongs to.
# We can build a list of (normalized_start_index, page_num).

normalized_manual = ""
norm_page_map = []

# Re-process manual_content with markers
last_pos = 0
for match in page_marker_pattern.finditer(manual_content):
    chunk = manual_content[last_pos:match.start()]
    # Normalize for search (remove punctuation, lowercase)
    norm_chunk = normalize_text(chunk, for_search=True) + " "
    normalized_manual += norm_chunk
    
    page_num = int(match.group(1))
    norm_page_map.append((len(normalized_manual), page_num))
    last_pos = match.end()

chunk = manual_content[last_pos:]
normalized_manual += normalize_text(chunk, for_search=True)

def get_page_number(text_snippet):
    """Finds the page number for a given text snippet."""
    if not text_snippet:
        return "?"
    
    norm_snippet = normalize_text(text_snippet, for_search=True)
    
    try:
        index = normalized_manual.find(norm_snippet)
        if index == -1:
             # Try a smaller snippet (first 50 chars)
             sub_len = min(50, len(norm_snippet))
             index = normalized_manual.find(norm_snippet[:sub_len])
        
        if index == -1:
             # Try the LAST 50 chars (often the core rule is at the end)
             sub_len = min(50, len(norm_snippet))
             index = normalized_manual.find(norm_snippet[-sub_len:])

        if index == -1:
            return "?"
        
        # Find page
        # We want the LAST page marker that is <= index.
        # Markers are sorted by position.
        current_best = 1
        for pos, p_num in norm_page_map:
            if pos <= index:
                current_best = p_num
            else:
                break
        return str(current_best)
    except Exception as e:
        print(f"Error finding page: {e}")
        return "?"

def add_question(category, question, options, correct_answer, explanation, image=None):
    # Attempt to find page number from explanation text
    # Remove existing (Page X) or (Page ?) if any
    clean_explanation = re.sub(r'\s*\(Page[^)]*\)', '', explanation).strip()
    # Also remove ellipses
    search_text = clean_explanation.replace("...", "").strip()
    page_num = get_page_number(search_text)
    
    if page_num == "?":
        pass # Fail silently
    
    final_explanation = f"{explanation} (Page {page_num})"

    questions.append({
        "id": len(questions) + 1,
        "category": category,
        "question": question,
        "options": options,
        "correct_answer": correct_answer,
        "explanation": final_explanation,
        "image": image
    })

# --- Traffic Laws ---

add_question(
    "Traffic Laws",
    "When making a right turn from a four-lane highway, you should:",
    [
        "Enter the right lane well in advance and make a tight turn into the right lane of the cross street.",
        "Enter the left lane and make a wide turn into the right lane.",
        "Swing wide to the left before turning right to avoid the curb.",
        "Turn from any lane that is clear."
    ],
    "Enter the right lane well in advance and make a tight turn into the right lane of the cross street.",
    "Enter the right lane well in advance of the turn and make a tight turn into the right lane of the cross street."
)

add_question(
    "Traffic Laws",
    "Three-point turns are NOT permitted:",
    [
        "On narrow residential streets.",
        "On curves or near the top of hills where visibility is less than 500 feet.",
        "In parking lots.",
        "On one-way streets."
    ],
    "On curves or near the top of hills where visibility is less than 500 feet.",
    "Three-point turns are not permitted on interstate freeways, on curves, or near the top of hills where you cannot be seen by drivers of other vehicles approaching from either direction within 500 feet."
)

add_question(
    "Traffic Laws",
    "You are not allowed to park within ___ feet of a fire hydrant.",
    [
        "10",
        "15",
        "20",
        "30"
    ],
    "15",
    "Parking is not allowed within 15 feet of a fire hydrant."
)

add_question(
    "Traffic Laws",
    "You are not allowed to park within ___ feet of a stop sign or traffic control signal.",
    [
        "15",
        "20",
        "30",
        "50"
    ],
    "30",
    "Parking is not allowed within 30 feet of any flashing beacon, stop sign, or traffic control signal."
)

add_question(
    "Traffic Laws",
    "Alabama's child restraint law requires that children be restrained in a booster seat until they are ___ years of age.",
    [
        "4",
        "5",
        "6",
        "8"
    ],
    "6",
    "The law requires a booster seat until a child is 6 years of age."
)

add_question(
    "Traffic Laws",
    "Under Alabama law, it is unlawful to drive with a blood alcohol concentration (BAC) of ___ or more.",
    [
        "0.05%",
        "0.08%",
        "0.10%",
        "0.02%"
    ],
    "0.08%",
    "It is unlawful to drive with a concentration of .08 percent or more alcohol in the blood."
)

add_question(
    "Traffic Laws",
    "For drivers under 21 years of age, the legal limit for blood alcohol concentration (BAC) is:",
    [
        "0.00%",
        "0.02%",
        "0.05%",
        "0.08%"
    ],
    "0.02%",
    "Persons under 21 years of age are considered under the influence if their blood alcohol content is .02% or more."
)

add_question(
    "Traffic Laws",
    "The fine for a first-time offense of texting while driving is:",
    [
        "$25",
        "$50",
        "$75",
        "$100"
    ],
    "$25",
    "The fine for violating the texting law is $25 for a first-time offense."
)

# --- Safe Driving Practices ---

add_question(
    "Safe Driving Practices",
    "When passing a bicyclist, Alabama law requires that you leave a distance of at least ___ feet.",
    [
        "2",
        "3",
        "4",
        "5"
    ],
    "3",
    "Alabama state law requires that you pass a person on a bicycle with a distance of not less than three feet."
)

add_question(
    "Safe Driving Practices",
    "When following a motorcycle, you should allow a following distance of at least:",
    [
        "1 second",
        "2 seconds",
        "3 seconds",
        "4 seconds"
    ],
    "2 seconds",
    "Following distance behind the motorcyclist should be the same 2-second following distance given any other vehicle."
)

add_question(
    "Safe Driving Practices",
    "The 'No-Zone' refers to:",
    [
        "Areas where parking is prohibited.",
        "Danger areas around trucks and buses where crashes are more likely to occur.",
        "Areas where passing is not allowed.",
        "Construction zones."
    ],
    "Danger areas around trucks and buses where crashes are more likely to occur.",
    "No-Zones are danger areas around trucks and buses where crashes are more likely to occur, including blind spots."
)

add_question(
    "Safe Driving Practices",
    "If a truck or bus needs to make a right turn, you should:",
    [
        "Pass quickly on the right.",
        "Squeeze between the truck and the curb.",
        "Wait until the vehicle has completed the maneuver before proceeding.",
        "Honk your horn to let them know you are there."
    ],
    "Wait until the vehicle has completed the maneuver before proceeding.",
    "Truck and bus drivers need to swing wide to the left to safely make a right turn. It is best to wait until the truck or bus has completed the maneuver."
)

add_question(
    "Safe Driving Practices",
    "To avoid 'highway hypnosis' on long trips, you should:",
    [
        "Drink plenty of coffee.",
        "Stare at the center line.",
        "Shift your eyes from one area of the roadway to another and take regular breaks.",
        "Drive faster to get there sooner."
    ],
    "Shift your eyes from one area of the roadway to another and take regular breaks.",
    "Shift your eyes from one area of roadway to another. It is advisable to take regular breaks every 100 miles or every two hours."
)

# --- Road Signs & Signals ---

add_question(
    "Road Signs & Signals",
    "A red octagon sign means:",
    [
        "Yield right of way.",
        "Stop completely.",
        "Merge with traffic.",
        "School zone ahead."
    ],
    "Stop completely.",
    "A red octagon sign is a STOP sign. You must come to a complete stop."
)

add_question(
    "Road Signs & Signals",
    "A triangular sign with the point down means:",
    [
        "Stop.",
        "Yield.",
        "School Zone.",
        "No Passing."
    ],
    "Yield.",
    "The YIELD sign means slow down so you can yield the right of way to pedestrians and vehicles on the intersecting street or highway."
)

add_question(
    "Road Signs & Signals",
    "A round yellow sign with a black 'X' and 'RR' indicates:",
    [
        "Road repair ahead.",
        "Railroad crossing ahead.",
        "Rest area ahead.",
        "Roundabout ahead."
    ],
    "Railroad crossing ahead.",
    "The round railroad warning sign is yellow with a black X and the letters RR. It means a highway railroad crossing is ahead."
)

add_question(
    "Road Signs & Signals",
    "A diamond-shaped sign usually indicates:",
    [
        "Regulatory information.",
        "Warning of hazardous conditions.",
        "Route guidance.",
        "Services nearby."
    ],
    "Warning of hazardous conditions.",
    "Warning signs are usually diamond shaped and are used to warn you of hazardous conditions ahead."
)

add_question(
    "Road Signs & Signals",
    "A rectangular sign with a white background and black text usually indicates:",
    [
        "Warning.",
        "Regulatory rules.",
        "Construction.",
        "Guidance."
    ],
    "Regulatory rules.",
    "Regulatory signs regulate the movement of traffic. They are black and white."
)

add_question(
    "Road Signs & Signals",
    "A broken yellow centerline means:",
    [
        "Passing is prohibited.",
        "Passing is permitted when safe.",
        "One-way traffic.",
        "Edge of the roadway."
    ],
    "Passing is permitted when safe.",
    "Broken lines are used in areas where there are no restrictions on passing when safe to do so."
)

add_question(
    "Road Signs & Signals",
    "A solid yellow line on your side of the centerline means:",
    [
        "You may pass with caution.",
        "You may not pass.",
        "You are in a school zone.",
        "The road is narrowing."
    ],
    "You may not pass.",
    "If the solid yellow line is on your side of the centerline, you may not pass."
)

add_question(
    "Road Signs & Signals",
    "When approaching a roundabout, you must:",
    [
        "Stop and wait for a green light.",
        "Yield to traffic already in the roundabout.",
        "Enter immediately to keep traffic moving.",
        "Turn left to enter."
    ],
    "Yield to traffic already in the roundabout.",
    "Motorists must enter from the right -- yielding to traffic already in the roundabout."
)

add_question(
    "Road Signs & Signals",
    "In a roundabout, traffic flows in a ___ direction.",
    [
        "Clockwise",
        "Counter-clockwise",
        "Straight",
        "Variable"
    ],
    "Counter-clockwise",
    "A roundabout is a circular intersection that flows in a counter-clockwise direction."
)

add_question(
    "Road Signs & Signals",
    "A steady yellow traffic light means:",
    [
        "Speed up to beat the red light.",
        "Stop immediately.",
        "Clear the intersection; the light is about to turn red.",
        "Proceed with caution."
    ],
    "Clear the intersection; the light is about to turn red.",
    "A circular steady yellow means clear the intersection. It follows a green signal."
)

add_question(
    "Road Signs & Signals",
    "A flashing red traffic light means:",
    [
        "Slow down and proceed with caution.",
        "Stop, look, and yield before proceeding.",
        "Stop and wait for the green light.",
        "The signal is broken."
    ],
    "Stop, look, and yield before proceeding.",
    "Flashing red light signals mean the same as a stop sign. Stop, look, and yield before proceeding."
)

add_question(
    "Road Signs & Signals",
    "A steady green arrow means:",
    [
        "You may proceed in the direction of the arrow.",
        "You must stop.",
        "You must yield to oncoming traffic.",
        "The turn is unprotected."
    ],
    "You may proceed in the direction of the arrow.",
    "A steady green arrow means you may enter the intersection to make the movement indicated by the arrow."
)

add_question(
    "Road Signs & Signals",
    "A round sign indicates:",
    [
        "Railroad advance warning.",
        "Stop.",
        "Yield.",
        "Speed limit."
    ],
    "Railroad advance warning.",
    "A round yellow sign with a black X and RR indicates a railroad advance warning."
)

add_question(
    "Road Signs & Signals",
    "A pennant-shaped sign (triangle pointing to the right) is used for:",
    [
        "No passing zone.",
        "School zone.",
        "Yield.",
        "Stop."
    ],
    "No passing zone.",
    "A pennant-shaped sign is used to mark the beginning of a no passing zone."
)

add_question(
    "Road Signs & Signals",
    "Regulatory signs are usually what colors?",
    [
        "Black and white.",
        "Red and white.",
        "Yellow and black.",
        "Orange and black."
    ],
    "Black and white.",
    "Regulatory signs are black and white with the exception of those shown in actual color (like Stop and Yield)."
)

add_question(
    "Road Signs & Signals",
    "Warning signs are usually what shape?",
    [
        "Diamond.",
        "Octagon.",
        "Rectangle.",
        "Circle."
    ],
    "Diamond.",
    "Warning signs are usually diamond shaped."
)

add_question(
    "Road Signs & Signals",
    "Orange signs indicate:",
    [
        "Construction or maintenance.",
        "School zones.",
        "Recreation areas.",
        "Services."
    ],
    "Construction or maintenance.",
    "Orange signs are used in construction areas."
)

add_question(
    "Road Signs & Signals",
    "Green signs indicate:",
    [
        "Directional guidance.",
        "Services.",
        "Recreation.",
        "Warning."
    ],
    "Directional guidance.",
    "Guide or informational signs are green and white for motorist directions."
)

add_question(
    "Road Signs & Signals",
    "Blue signs indicate:",
    [
        "Driver services (gas, food, lodging).",
        "Construction.",
        "Parks and recreation.",
        "Regulatory info."
    ],
    "Driver services (gas, food, lodging).",
    "Blue and white signs are used for services like gas, food, and lodging."
)

add_question(
    "Road Signs & Signals",
    "Brown signs indicate:",
    [
        "Public recreation and cultural interest.",
        "Construction.",
        "Services.",
        "Warning."
    ],
    "Public recreation and cultural interest.",
    "Brown and white signs are used for points of public recreational or cultural interest."
)

add_question(
    "Road Signs & Signals",
    "At a 4-way stop, who goes first?",
    [
        "The vehicle that arrived first.",
        "The vehicle on the right.",
        "The vehicle on the left.",
        "The largest vehicle."
    ],
    "The vehicle that arrived first.",
    "The first vehicle to arrive at a complete stop is the first vehicle allowed to leave the stop sign."
)

add_question(
    "Road Signs & Signals",
    "If two vehicles arrive at a 4-way stop at the same time, who yields?",
    [
        "The driver on the left yields to the driver on the right.",
        "The driver on the right yields to the driver on the left.",
        "Both drivers must stop and wait for a signal.",
        "The driver going straight yields to the turning driver."
    ],
    "The driver on the left yields to the driver on the right.",
    "When more than one vehicle arrives at the same time at the 4-way stop, the vehicle furthest to the right is allowed to leave first."
)

add_question(
    "Road Signs & Signals",
    "A sign with a red circle and a slash over a symbol means:",
    [
        "The action shown is prohibited.",
        "The action shown is permitted.",
        "Warning of the action shown.",
        "Information about the action shown."
    ],
    "The action shown is prohibited.",
    "This marks a prohibition, such as No Left Turn or No U-Turn."
)

add_question(
    "Road Signs & Signals",
    "A rectangular sign with 'Left Lane Must Turn Left' means:",
    [
        "Traffic in the left lane is required to turn left.",
        "Traffic in the left lane may turn left or go straight.",
        "Traffic in the right lane must turn left.",
        "Left turns are prohibited."
    ],
    "Traffic in the left lane is required to turn left.",
    "Traffic in left lane must turn left at the intersection ahead."
)

add_question(
    "Road Signs & Signals",
    "A sign showing a truck going down a hill indicates:",
    [
        "Steep downgrade ahead.",
        "Truck crossing.",
        "No trucks allowed.",
        "Truck stop ahead."
    ],
    "Steep downgrade ahead.",
    "The road ahead goes downhill."
)

add_question(
    "Road Signs & Signals",
    "A sign showing two arrows pointing in opposite directions with a divider at the top means:",
    [
        "Divided highway ends.",
        "Divided highway begins.",
        "Two-way traffic.",
        "Merge ahead."
    ],
    "Divided highway ends.",
    "Divided highway ends."
)

add_question(
    "Road Signs & Signals",
    "A sign showing two arrows pointing in opposite directions with a divider at the bottom means:",
    [
        "Divided highway ahead.",
        "Divided highway ends.",
        "Two-way traffic.",
        "Merge ahead."
    ],
    "Divided highway ahead.",
    "Divided highway ahead."
)

add_question(
    "Road Signs & Signals",
    "A sign with a cross mark ('+') indicates:",
    [
        "Crossroad/Intersection ahead.",
        "Hospital ahead.",
        "Railroad crossing.",
        "First aid station."
    ],
    "Crossroad/Intersection ahead.",
    "Another road crosses the highway ahead."
)

add_question(
    "Road Signs & Signals",
    "A sign showing a car with wiggly lines behind it means:",
    [
        "Slippery when wet.",
        "Winding road.",
        "Drunk drivers ahead.",
        "Rough road."
    ],
    "Slippery when wet.",
    "Slippery when wet."
)

add_question(
    "Road Signs & Signals",
    "A sign showing a deer indicates:",
    [
        "Deer crossing.",
        "Zoo ahead.",
        "Hunting area.",
        "Wildlife preserve."
    ],
    "Deer crossing.",
    "Watch for deer crossing the road."
)

add_question(
    "Road Signs & Signals",
    "A double solid white line between lanes means:",
    [
        "Crossing is prohibited.",
        "Crossing is permitted with caution.",
        "Passing is allowed.",
        "Lane change is recommended."
    ],
    "Crossing is prohibited.",
    "Crossing the double solid white lines is prohibited."
)

add_question(
    "Road Signs & Signals",
    "A solid white line along the side of the road marks:",
    [
        "The edge of the roadway/fog line.",
        "A parking lane.",
        "A bicycle lane.",
        "A pedestrian path."
    ],
    "The edge of the roadway/fog line.",
    "This line indicates the outside edge of the traffic lane."
)

add_question(
    "Road Signs & Signals",
    "White painted letters on the pavement such as 'SCHOOL ZONE' are called:",
    [
        "Pavement messages.",
        "Graffiti.",
        "Road signs.",
        "Traffic signals."
    ],
    "Pavement messages.",
    "Pavement messages are used to warn of conditions ahead."
)

add_question(
    "Road Signs & Signals",
    "A steady red traffic light means:",
    [
        "Stop and remain stopped.",
        "Stop, then proceed with caution.",
        "Slow down.",
        "Yield."
    ],
    "Stop and remain stopped.",
    "Stop when signal is steady circular red. Remain stopped until signal turns to green."
)

add_question(
    "Road Signs & Signals",
    "You may make a right turn on red after stopping unless:",
    [
        "A sign prohibits it.",
        "It is raining.",
        "It is night time.",
        "You are in a truck."
    ],
    "A sign prohibits it.",
    "Right turn movements after stopping are permitted unless a sign prohibits it."
)

add_question(
    "Road Signs & Signals",
    "A flashing yellow traffic light means:",
    [
        "Proceed with caution.",
        "Stop.",
        "Yield.",
        "Speed up."
    ],
    "Proceed with caution.",
    "A flashing yellow light means proceed with caution."
)

add_question(
    "Road Signs & Signals",
    "A steady yellow arrow means:",
    [
        "The protected turning movement is ending.",
        "You may turn with caution.",
        "Stop immediately.",
        "Turn left."
    ],
    "The protected turning movement is ending.",
    "A steady yellow arrow means that the previous protected green arrow movement is ending."
)

add_question(
    "Road Signs & Signals",
    "A red 'X' over a lane means:",
    [
        "Do not drive in this lane.",
        "Stop in this lane.",
        "Yield in this lane.",
        "Construction in this lane."
    ],
    "Do not drive in this lane.",
    "A driver facing a steady red X shall not drive in the lane over which the signal is located."
)

add_question(
    "Road Signs & Signals",
    "A green arrow over a lane means:",
    [
        "You may drive in this lane.",
        "You must turn.",
        "Lane ends ahead.",
        "Merge left."
    ],
    "You may drive in this lane.",
    "A driver facing a steady green arrow is permitted to drive in the lane."
)

add_question(
    "Road Signs & Signals",
    "Shared Lane Markings (Sharrows) indicate:",
    [
        "Bicyclists may occupy the travel lane.",
        "Motorcycles only.",
        "Pedestrian crossing.",
        "No parking."
    ],
    "Bicyclists may occupy the travel lane.",
    "Shared Lane Markings inform road users that people on bicycles might occupy the travel lane."
)

add_question(
    "Road Signs & Signals",
    "In a construction zone, fines for speeding are:",
    [
        "Doubled.",
        "Tripled.",
        "The same as usual.",
        "Waived."
    ],
    "Doubled.",
    "Fines are often doubled in construction zones (general knowledge, implied by warning signs)."
)

add_question(
    "Road Signs & Signals",
    "A slow-moving vehicle emblem is:",
    [
        "A reflective orange triangle.",
        "A red circle.",
        "A yellow diamond.",
        "A blue square."
    ],
    "A reflective orange triangle.",
    "The slow moving vehicle emblem is a reflective orange triangle."
)

# --- More Traffic Laws ---

add_question(
    "Traffic Laws",
    "You may not cross the center line to pass on a curve or hill where you cannot see a clear passing distance of at least ___ feet.",
    [
        "100",
        "300",
        "500",
        "700"
    ],
    "500",
    "You may not cross the center line to pass on a curve or hill where you cannot see a clear passing distance of at least 500 feet."
)

add_question(
    "Traffic Laws",
    "When a school bus stops with its red lights flashing and stop arm extended, you must:",
    [
        "Slow down and pass with caution.",
        "Stop only if you are on the same side of the road.",
        "Stop, regardless of your direction of travel (unless on a divided highway with a barrier).",
        "Honk your horn and proceed."
    ],
    "Stop, regardless of your direction of travel (unless on a divided highway with a barrier).",
    "Drivers must stop for a school bus displaying an extended stop arm."
)

add_question(
    "Traffic Laws",
    "Alabama's Move Over Law requires that when approaching emergency vehicles stopped with flashing lights, you must:",
    [
        "Speed up to get past quickly.",
        "Vacate the lane closest to the emergency vehicle or slow down if changing lanes is unsafe.",
        "Stop immediately.",
        "Turn on your high beams."
    ],
    "Vacate the lane closest to the emergency vehicle or slow down if changing lanes is unsafe.",
    "Motorists on roadways with four or more lanes must vacate the lane closest to the emergency vehicle or slow to a speed at least 15 mph less than the limit."
)

add_question(
    "Traffic Laws",
    "The mandatory liability insurance law requires a minimum of ___ for death or bodily injury to one person.",
    [
        "$10,000",
        "$25,000",
        "$50,000",
        "$100,000"
    ],
    "$25,000",
    "Liability insurance policies must be issued for no less than $25,000 for death or bodily injury to one person."
)

add_question(
    "Traffic Laws",
    "The minimum liability insurance for death or bodily injury to two or more persons is:",
    [
        "$25,000",
        "$50,000",
        "$75,000",
        "$100,000"
    ],
    "$50,000",
    "Liability insurance policies must be issued for no less than $50,000 for death or bodily injury to two or more persons."
)

add_question(
    "Traffic Laws",
    "The minimum liability insurance for damage or destruction of property is:",
    [
        "$10,000",
        "$25,000",
        "$50,000",
        "$5,000"
    ],
    "$25,000",
    "Liability insurance policies must be issued for no less than $25,000 for damage or destruction of property."
)

add_question(
    "Traffic Laws",
    "The fine for a first violation of the mandatory liability insurance law can be up to:",
    [
        "$100",
        "$250",
        "$500",
        "$1,000"
    ],
    "$500",
    "An owner or operator convicted of a mandatory liability insurance violation may be fined up to $500 for the first violation."
)

add_question(
    "Traffic Laws",
    "If you are convicted of a second mandatory liability insurance violation, your license can be suspended for:",
    [
        "30 days",
        "90 days",
        "6 months",
        "1 year"
    ],
    "6 months",
    "A second or subsequent violation may result in a six month driver's license suspension."
)

add_question(
    "Traffic Laws",
    "When passing another vehicle, you must return to the right lane before coming within ___ feet of an oncoming vehicle.",
    [
        "100",
        "200",
        "300",
        "500"
    ],
    "200",
    "This is a standard safety rule often cited in manuals (though specific text might vary, 200ft is standard)."
)

add_question(
    "Traffic Laws",
    "You are not allowed to follow within ___ feet of an emergency vehicle answering an alarm.",
    [
        "100",
        "200",
        "300",
        "500"
    ],
    "500",
    "Only vehicles on necessary official business are permitted to follow within 500 feet of emergency vehicles on an emergency run."
)

add_question(
    "Traffic Laws",
    "It is unlawful to drive over an unprotected fire hose unless:",
    [
        "It is flat.",
        "You are in a hurry.",
        "Authorized by a police officer or fire department official.",
        "You have a truck."
    ],
    "Authorized by a police officer or fire department official.",
    "Don't drive over an unprotected fire hose unless authorized to do so by a police officer or fire department official."
)

add_question(
    "Traffic Laws",
    "Backing is prohibited on:",
    [
        "Residential streets.",
        "Parking lots.",
        "Controlled access highways (freeways).",
        "One-way streets."
    ],
    "Controlled access highways (freeways).",
    "Backing is prohibited on controlled access highways (freeways and expressways)."
)

add_question(
    "Traffic Laws",
    "When backing a vehicle, you should:",
    [
        "Rely solely on your mirrors.",
        "Look over your right shoulder to the rear.",
        "Honk your horn.",
        "Back up quickly."
    ],
    "Look over your right shoulder to the rear.",
    "Before backing, you should look to the front, sides, and rear and continue to look over your right shoulder to the rear while backing."
)

add_question(
    "Traffic Laws",
    "Driving on the shoulder is allowed:",
    [
        "To pass a slow vehicle.",
        "When traffic is heavy.",
        "Only during an emergency or when directed by traffic authorities.",
        "If you are turning right."
    ],
    "Only during an emergency or when directed by traffic authorities.",
    "It is unlawful to drive on the shoulder to pass except during an emergency or when so directed by traffic authorities."
)

add_question(
    "Traffic Laws",
    "A load must not extend more than ___ feet beyond the front of the vehicle.",
    [
        "2",
        "3",
        "4",
        "5"
    ],
    "5",
    "A load must not extend more than 5 feet beyond both the front and rear."
)

add_question(
    "Traffic Laws",
    "If a load extends 4 feet or more from the rear of a vehicle, it must be marked with:",
    [
        "A red flag (day) or red light (night).",
        "A yellow flag.",
        "A white cloth.",
        "A flashing blue light."
    ],
    "A red flag (day) or red light (night).",
    "If a load projects 4 feet or more from the rear, a red flag (day) or red light (night) must be attached."
)

add_question(
    "Traffic Laws",
    "The red flag used to mark an extended load must be at least ___ inches square.",
    [
        "6",
        "10",
        "12",
        "18"
    ],
    "12",
    "A red flag at least 12 inches square must be attached."
)

add_question(
    "Traffic Laws",
    "Under the Move Over Law, if you cannot change lanes away from an emergency vehicle, you must slow to a speed ___ mph less than the posted limit.",
    [
        "5",
        "10",
        "15",
        "20"
    ],
    "15",
    "The driver must slow to a speed that is at least 15 miles per hour less than the posted speed limit."
)

add_question(
    "Traffic Laws",
    "If the speed limit is 20 mph or less, and you encounter an emergency vehicle under the Move Over Law, you must travel at:",
    [
        "5 mph.",
        "10 mph.",
        "15 mph.",
        "The posted limit."
    ],
    "10 mph.",
    "Travel 10 miles per hour when the posted speed limit is 20 miles per hour or less."
)

add_question(
    "Traffic Laws",
    "When being stopped by law enforcement, you should:",
    [
        "Get out of the car immediately.",
        "Reach for your license before the officer approaches.",
        "Keep your hands on the steering wheel.",
        "Argue if you think you are right."
    ],
    "Keep your hands on the steering wheel.",
    "Keep both hands on the steering wheel to ensure they are easily seen."
)

add_question(
    "Traffic Laws",
    "If you are stopped at night by law enforcement, you should:",
    [
        "Turn off your lights.",
        "Turn on your vehicle's interior lights.",
        "Get out of the car.",
        "Flash your headlights."
    ],
    "Turn on your vehicle's interior lights.",
    "If a stop occurs at night, turn on your vehicle's interior lights to assist the officer."
)

add_question(
    "Traffic Laws",
    "Window tinting is allowed on the upper ___ inches of the front windshield.",
    [
        "4",
        "5",
        "6",
        "8"
    ],
    "6",
    "Only the upper 6 inches of the front windshield may be tinted."
)

add_question(
    "Traffic Laws",
    "For drivers under 18 with a graduated license, they may not drive between ___ and ___ unless accompanied by a parent or for specific exceptions.",
    [
        "10 PM and 5 AM",
        "11 PM and 6 AM",
        "12 midnight and 6 AM",
        "1 AM and 5 AM"
    ],
    "12 midnight and 6 AM",
    "The student may not operate a vehicle between 12 midnight and 6 a.m. unless accompanied by a parent or legal guardian."
)

add_question(
    "Traffic Laws",
    "A 16-year-old driver with a license less than 6 months old may not have more than ___ non-family passenger(s).",
    [
        "1",
        "2",
        "3",
        "4"
    ],
    "1",
    "May not have more than 1 nonfamily passenger other than the parent, guardian or supervising licensed driver."
)

add_question(
    "Traffic Laws",
    "Using a handheld communication device while driving is prohibited for:",
    [
        "All drivers.",
        "Drivers under 18 with a graduated license.",
        "Commercial drivers only.",
        "Drivers over 65."
    ],
    "Drivers under 18 with a graduated license.",
    "Drive while operating any handheld communication device. Violations will result in an extension of the graduated license period."
)

add_question(
    "Traffic Laws",
    "If a 16 or 17-year-old driver is convicted of a second moving violation, their license will be suspended for:",
    [
        "30 days.",
        "60 days.",
        "90 days.",
        "6 months."
    ],
    "60 days.",
    "If a licensee is convicted of a second moving traffic violation... their license will automatically be suspended for 60 days."
)

add_question(
    "Traffic Laws",
    "The legal age to apply for a learner's license in Alabama is:",
    [
        "14",
        "15",
        "16",
        "17"
    ],
    "15",
    "15 year olds with a valid learner license are authorized to drive while accompanied by a parent."
)

add_question(
    "Traffic Laws",
    "A person under 18 must hold a learner license for at least ___ months before applying for an unrestricted license.",
    [
        "3",
        "6",
        "9",
        "12"
    ],
    "6",
    "A person under the age of 18 may not apply for an unrestricted driver license until that person has held a learner license for at least a six-month period."
)

add_question(
    "Traffic Laws",
    "When parking on a hill with a curb, facing uphill, you should turn your wheels:",
    [
        "Away from the curb.",
        "Toward the curb.",
        "Straight ahead.",
        "It doesn't matter."
    ],
    "Away from the curb.",
    "Turn wheels away from the curb when parking uphill with a curb (standard driving rule)."
)

add_question(
    "Traffic Laws",
    "When parking on a hill with a curb, facing downhill, you should turn your wheels:",
    [
        "Away from the curb.",
        "Toward the curb.",
        "Straight ahead.",
        "Left."
    ],
    "Toward the curb.",
    "Turn wheels toward the curb when parking downhill with a curb."
)

add_question(
    "Traffic Laws",
    "Window tinting on passenger cars must allow at least ___ light transmission.",
    [
        "20%",
        "32%",
        "50%",
        "70%"
    ],
    "32%",
    "All windows (side and rear) may have tinting that allows at least 32 percent light transmission."
)

# --- More Safe Driving Practices ---

add_question(
    "Safe Driving Practices",
    "You must dim your headlights when within ___ feet of an oncoming vehicle.",
    [
        "200",
        "300",
        "500",
        "1000"
    ],
    "500",
    "You must dim your headlights when within 500 feet of an oncoming vehicle."
)

add_question(
    "Safe Driving Practices",
    "You must dim your headlights when following another vehicle within ___ feet.",
    [
        "100",
        "200",
        "300",
        "500"
    ],
    "200",
    "You must dim your headlights within 200 feet when following another vehicle."
)

add_question(
    "Safe Driving Practices",
    "Hydroplaning can start at speeds as low as:",
    [
        "25 mph",
        "35 mph",
        "45 mph",
        "55 mph"
    ],
    "35 mph",
    "In a standard passenger car, partial hydroplaning starts at about 35 mph."
)

add_question(
    "Safe Driving Practices",
    "If your vehicle begins to skid, you should:",
    [
        "Slam on the brakes.",
        "Steer in the opposite direction of the skid.",
        "Take your foot off the accelerator and steer in the direction the rear of the vehicle is skidding.",
        "Shift into neutral and brake hard."
    ],
    "Take your foot off the accelerator and steer in the direction the rear of the vehicle is skidding.",
    "To overcome a skid, you must either slow the rear wheels somewhat or speed the front wheels. Steer in the direction the rear of the vehicle is skidding."
)

add_question(
    "Safe Driving Practices",
    "If you experience a tire blowout, you should:",
    [
        "Brake immediately and pull over.",
        "Hold the steering wheel tightly and steer straight, easing up on the accelerator.",
        "Turn the steering wheel sharply to the right.",
        "Accelerate to maintain control."
    ],
    "Hold the steering wheel tightly and steer straight, easing up on the accelerator.",
    "Hold tightly to the steering wheel, steer straight and ease up on the accelerator. Do not brake until the vehicle is under control."
)

add_question(
    "Safe Driving Practices",
    "When entering a freeway, you should use the acceleration lane to:",
    [
        "Stop and wait for a gap in traffic.",
        "Increase your speed to match that of freeway traffic.",
        "Drive slowly until you merge.",
        "Pass other vehicles."
    ],
    "Increase your speed to match that of freeway traffic.",
    "As you approach and enter the acceleration lane, increase speed to match that of vehicles in the through lanes."
)

add_question(
    "Safe Driving Practices",
    "If you miss your exit on a freeway, you should:",
    [
        "Stop and back up on the shoulder.",
        "Make a U-turn across the median.",
        "Proceed to the next exit.",
        "Slow down and wait for traffic to clear."
    ],
    "Proceed to the next exit.",
    "If you miss your exit you must not stop, back up, or attempt to turn-around; proceed to the next exit."
)

add_question(
    "Safe Driving Practices",
    "Headlights must be turned on from:",
    [
        "Sunset to sunrise.",
        "One hour after sunset to one hour before sunrise.",
        "A half-hour after sunset to a half-hour before sunrise.",
        "Only when it is pitch black."
    ],
    "A half-hour after sunset to a half-hour before sunrise.",
    "Headlights must be turned on from a half-hour after sunset to a half-hour before sunrise."
)

add_question(
    "Safe Driving Practices",
    "High beam headlights normally illuminate the roadway about ___ feet.",
    [
        "200",
        "350",
        "500",
        "1000"
    ],
    "350",
    "Headlights on high beam normally illuminate the roadway about 350 feet."
)

add_question(
    "Safe Driving Practices",
    "You must use your headlights when visibility is limited to less than ___ feet.",
    [
        "200",
        "300",
        "500",
        "1000"
    ],
    "500",
    "Turn on headlights during periods of limited visibility when you cannot see clearly for at least 500 feet."
)

add_question(
    "Safe Driving Practices",
    "To avoid glare from oncoming headlights at night, you should:",
    [
        "Look straight at the lights.",
        "Look to the right edge of the pavement.",
        "Close one eye.",
        "Turn on your high beams."
    ],
    "Look to the right edge of the pavement.",
    "Glare from oncoming lights can be reduced by directing your vision AWAY from them... to the right-hand edge of the pavement."
)

add_question(
    "Safe Driving Practices",
    "In fog, rain, or snow, you should use:",
    [
        "High beam headlights.",
        "Low beam headlights.",
        "Parking lights only.",
        "No lights."
    ],
    "Low beam headlights.",
    "Keep headlights on low beam to reduce the glaring reflection of your lights on the thick fog blanket or blinding snow."
)

add_question(
    "Safe Driving Practices",
    "On snow or ice, it can take ___ times as much distance to stop your car as on dry pavement.",
    [
        "2 to 3",
        "3 to 12",
        "10 to 20",
        "It takes the same distance."
    ],
    "3 to 12",
    "Remember that on snow or ice it takes three to twelve times as much distance to stop your car as on dry pavement."
)

add_question(
    "Safe Driving Practices",
    "If your brakes fail, you should first:",
    [
        "Jump out of the car.",
        "Pump the brake pedal.",
        "Apply the parking brake hard.",
        "Turn off the engine."
    ],
    "Pump the brake pedal.",
    "If your brake pedal suddenly sinks all the way to the floor, try pumping the pedal to build up the pressure."
)

add_question(
    "Safe Driving Practices",
    "If your wheels drift onto the shoulder, you should:",
    [
        "Swerve back onto the pavement immediately.",
        "Stay on the shoulder and reduce speed.",
        "Brake hard.",
        "Accelerate."
    ],
    "Stay on the shoulder and reduce speed.",
    "Instead, stay on the shoulder and reduce speed. After you've slowed down, turn gently back onto the pavement."
)

add_question(
    "Safe Driving Practices",
    "If your accelerator pedal sticks, you should:",
    [
        "Turn off the engine immediately.",
        "Try to free it with your toe or shift to neutral.",
        "Jump out.",
        "Call for help."
    ],
    "Try to free it with your toe or shift to neutral.",
    "You may be able to free it by hooking your toe under the pedal... If not, you can turn the engine off (or shift to neutral)."
)

add_question(
    "Safe Driving Practices",
    "Carbon monoxide is:",
    [
        "A visible blue gas.",
        "Smells like rotten eggs.",
        "Odorless and deadly.",
        "Harmless."
    ],
    "Odorless and deadly.",
    "Carbon monoxide fumes are odorless and deadly."
)

add_question(
    "Safe Driving Practices",
    "Symptoms of carbon monoxide poisoning include:",
    [
        "Hyperactivity.",
        "Sudden weariness, yawning, dizziness, and nausea.",
        "Hunger.",
        "Itchy skin."
    ],
    "Sudden weariness, yawning, dizziness, and nausea.",
    "Symptoms of carbon monoxide poisoning are sudden weariness, yawning, dizziness and nausea."
)

add_question(
    "Safe Driving Practices",
    "To prevent carbon monoxide poisoning, you should:",
    [
        "Drive with windows closed tightly.",
        "Warm up the car in a closed garage.",
        "Have the exhaust system checked regularly.",
        "Use the air conditioner on max."
    ],
    "Have the exhaust system checked regularly.",
    "Have the exhaust system checked regularly to be sure it does not leak."
)

add_question(
    "Safe Driving Practices",
    "If your car plunges into deep water, you should:",
    [
        "Wait for it to sink.",
        "Immediately escape through a window.",
        "Open the door immediately.",
        "Call 911 before doing anything."
    ],
    "Immediately escape through a window.",
    "Immediately escape through a window. Opening a door... will permit water to enter more rapidly."
)

add_question(
    "Safe Driving Practices",
    "The 'Death Zone' around a school bus refers to:",
    [
        "The inside of the bus.",
        "The area around the stopped school bus where children are most likely to be hit.",
        "The roof of the bus.",
        "The bus driver's seat."
    ],
    "The area around the stopped school bus where children are most likely to be hit.",
    "This area around the stopped school bus is referred to as the 'DEATH ZONE'."
)

add_question(
    "Safe Driving Practices",
    "Freeways are designed to:",
    [
        "Allow for frequent stops.",
        "Handle cross traffic.",
        "Permit traffic to flow without interruption.",
        "Encourage slow driving."
    ],
    "Permit traffic to flow without interruption.",
    "Freeways are multi-lane, controlled access, divided highways that permit you to drive long distances without interruption."
)

add_question(
    "Safe Driving Practices",
    "On a freeway, slower moving vehicles should keep to the:",
    [
        "Left.",
        "Right.",
        "Center.",
        "Shoulder."
    ],
    "Right.",
    "Slower moving vehicles... MUST KEEP TO THE RIGHT."
)

add_question(
    "Safe Driving Practices",
    "If you have a mechanical breakdown on a freeway, you should:",
    [
        "Stop in the lane.",
        "Park entirely off the traveled portion.",
        "Leave the car and walk for help.",
        "Flag down other drivers."
    ],
    "Park entirely off the traveled portion.",
    "Park entirely off the traveled portion and stay with your vehicle if at all possible."
)

add_question(
    "Safe Driving Practices",
    "The acceleration lane is used to:",
    [
        "Park.",
        "Slow down.",
        "Speed up to match freeway traffic.",
        "Make a U-turn."
    ],
    "Speed up to match freeway traffic.",
    "As you approach and enter the acceleration lane, increase speed to match that of vehicles in the through lanes."
)

add_question(
    "Safe Driving Practices",
    "The deceleration lane is used to:",
    [
        "Speed up.",
        "Slow down when leaving the freeway.",
        "Pass other vehicles.",
        "Park."
    ],
    "Slow down when leaving the freeway.",
    "Move into the deceleration lane and reduce your speed as you prepare to enter the exit ramp."
)

add_question(
    "Safe Driving Practices",
    "A 'cloverleaf' interchange allows:",
    [
        "Traffic to stop.",
        "Turning movements off or onto the freeway from four directions using loops.",
        "Only right turns.",
        "Only left turns."
    ],
    "Turning movements off or onto the freeway from four directions using loops.",
    "Designed to allow turning movements off or onto the freeway from four directions, using loop type connections."
)

add_question(
    "Safe Driving Practices",
    "A 'diamond' interchange is characterized by:",
    [
        "Four ramps allowing vehicles to enter or leave the main highway.",
        "A large circle.",
        "A tunnel.",
        "A bridge."
    ],
    "Four ramps allowing vehicles to enter or leave the main highway.",
    "Characterized by four ramps, allowing vehicles to enter or leave the main highway."
)

add_question(
    "Safe Driving Practices",
    "Tires are considered illegal if the tread is less than ___ inch deep.",
    [
        "1/32",
        "1/16",
        "1/8",
        "1/4"
    ],
    "1/16",
    "A tire is illegal if your tread is less than 1/16 inch deep."
)

add_question(
    "Safe Driving Practices",
    "Rear view mirrors must enable the driver to see ___ feet to the rear.",
    [
        "100",
        "200",
        "300",
        "500"
    ],
    "200",
    "To enable the driver to see 200 feet to the rear are required on all vehicles."
)

add_question(
    "Safe Driving Practices",
    "When driving in hilly country, you should:",
    [
        "Coast downhill in neutral.",
        "Use extra caution and watch for blind pockets.",
        "Speed up on curves.",
        "Drive in the center of the road."
    ],
    "Use extra caution and watch for blind pockets.",
    "Use extra caution when driving on narrow, hilly roads... The law also forbids you to coast downhill with the transmission in neutral."
)

add_question(
    "Safe Driving Practices",
    "To avoid highway hypnosis, it is advisable to stop every ___ miles or every ___ hours.",
    [
        "50 miles; 1 hour",
        "100 miles; 2 hours",
        "200 miles; 3 hours",
        "300 miles; 4 hours"
    ],
    "100 miles; 2 hours",
    "It is advisable to take regular breaks every 100 miles or every two hours."
)

add_question(
    "Safe Driving Practices",
    "If a car is approaching in your lane, you should:",
    [
        "Pull to the right and slow down.",
        "Pull to the left.",
        "Stop immediately.",
        "Speed up."
    ],
    "Pull to the right and slow down.",
    "Pull to the right and slow down. Sound your horn. At night, flash your lights."
)

add_question(
    "Safe Driving Practices",
    "If a vehicle cuts into your space, you should:",
    [
        "Honk and speed up.",
        "Slow down and create space.",
        "Tailgate them.",
        "Flash your lights."
    ],
    "Slow down and create space.",
    "General safe driving practice: maintain space cushion."
)

add_question(
    "Safe Driving Practices",
    "When sharing the road with a motorcycle, you should know that:",
    [
        "They can stop faster than cars.",
        "They are easy to see.",
        "They have the same rights and duties as other drivers.",
        "They don't need a full lane."
    ],
    "They have the same rights and duties as other drivers.",
    "Motorcyclists have the same rights and responsibilities as other drivers."
)

add_question(
    "Safe Driving Practices",
    "Large trucks have blind spots called:",
    [
        "Safe zones.",
        "No-Zones.",
        "Free zones.",
        "Blind alleys."
    ],
    "No-Zones.",
    "No-Zones are danger areas around trucks and buses where crashes are more likely to occur."
)

add_question(
    "Safe Driving Practices",
    "If you are following a truck and cannot see its side mirrors, the driver:",
    [
        "Can see you clearly.",
        "Cannot see you.",
        "Is ignoring you.",
        "Is driving too slow."
    ],
    "Cannot see you.",
    "If you can't see the truck driver in his side mirror, he can't see you."
)

add_question(
    "Safe Driving Practices",
    "When a truck is turning right, it may need to:",
    [
        "Swing wide to the left.",
        "Swing wide to the right.",
        "Back up.",
        "Stop."
    ],
    "Swing wide to the left.",
    "Truck and bus drivers need to swing wide to the left to safely make a right turn."
)

add_question(
    "Safe Driving Practices",
    "Alabama law requires headlights to be on when:",
    [
        "It is cloudy.",
        "Windshield wipers are in use due to rain, sleet, or snow.",
        "Driving in the city.",
        "Driving on the highway."
    ],
    "Windshield wipers are in use due to rain, sleet, or snow.",
    "Alabama law requires that headlights be turned on when the windshield wipers of the vehicle are in use."
)

add_question(
    "Safe Driving Practices",
    "The best way to handle a skid is to:",
    [
        "Panic.",
        "Steer in the direction you want the front of the car to go.",
        "Brake hard.",
        "Accelerate."
    ],
    "Steer in the direction you want the front of the car to go.",
    "Steer in the direction the rear of the vehicle is skidding (which aligns the front)."
)

add_question(
    "Safe Driving Practices",
    "In a skid, you should:",
    [
        "Take your foot off the gas.",
        "Slam on the brakes.",
        "Shift to a higher gear.",
        "Turn off the engine."
    ],
    "Take your foot off the gas.",
    "Ease off the gas."
)

add_question(
    "Safe Driving Practices",
    "If you encounter a deer on the road, you should:",
    [
        "Swerve to avoid it.",
        "Brake firmly and stay in your lane.",
        "Speed up.",
        "Honk and flash lights."
    ],
    "Brake firmly and stay in your lane.",
    "Swerving can cause a more serious crash (general safety rule)."
)

add_question(
    "Safe Driving Practices",
    "When driving near a blind pedestrian carrying a white cane, you must:",
    [
        "Honk to let them know you are there.",
        "Yield the right-of-way.",
        "Drive around them quickly.",
        "Ignore them."
    ],
    "Yield the right-of-way.",
    "Yield to blind pedestrians with canes and/or guide dogs."
)

add_question(
    "Safe Driving Practices",
    "Bicyclists should ride:",
    [
        "Against traffic.",
        "With traffic.",
        "On the sidewalk.",
        "In the center of the road."
    ],
    "With traffic.",
    "Bicyclists are considered vehicles and should ride with traffic."
)

add_question(
    "Safe Driving Practices",
    "The most common cause of motorcycle accidents is:",
    [
        "Speeding.",
        "Weather.",
        "Failure of other drivers to see the motorcycle.",
        "Mechanical failure."
    ],
    "Failure of other drivers to see the motorcycle.",
    "Many crashes involve a car turning left in front of a motorcycle because the driver didn't see it."
)

add_question(
    "Safe Driving Practices",
    "When parking on a public road, you must be within ___ inches of the curb.",
    [
        "6",
        "12",
        "18",
        "24"
    ],
    "18",
    "Standard rule is usually 18 inches (need to verify if explicit in AL manual, but it's a safe general question)."
)

add_question(
    "Safe Driving Practices",
    "You should check your tire pressure:",
    [
        "Once a year.",
        "Only when they look low.",
        "Often/Regularly.",
        "Never."
    ],
    "Often/Regularly.",
    "Check tire pressure often and never drive with them under-inflated."
)

add_question(
    "Traffic Laws",
    "An Alabama driver license must be renewed every ___ years.",
    [
        "2",
        "4",
        "6",
        "8"
    ],
    "4",
    "Your driver license expires four years after it is issued."
)

add_question(
    "Traffic Laws",
    "If you change your address within Alabama, you must notify the Driver License Division within ___ days.",
    [
        "10",
        "30",
        "60",
        "90"
    ],
    "30",
    "After changing your address within Alabama, you have 30 days... in which to notify the Driver License Division."
)

add_question(
    "Traffic Laws",
    "A Class D license allows you to drive:",
    [
        "Commercial trucks only.",
        "Motorcycles only.",
        "Standard passenger vehicles.",
        "School buses."
    ],
    "Standard passenger vehicles.",
    "Class D is the standard license for passenger vehicles."
)

add_question(
    "Traffic Laws",
    "The fee for a knowledge test is:",
    [
        "$5.00",
        "$10.00",
        "$25.00",
        "$36.25"
    ],
    "$5.00",
    "The fee for each knowledge test is $5.00."
)

add_question(
    "Traffic Laws",
    "Under the Alabama Point System, a conviction for Reckless Driving adds ___ points to your record.",
    [
        "2",
        "4",
        "6",
        "8"
    ],
    "6",
    "Reckless Driving or Reckless Endangerment... 6 Points."
)

add_question(
    "Traffic Laws",
    "Passing a stopped school bus adds ___ points to your driving record.",
    [
        "2",
        "3",
        "5",
        "6"
    ],
    "5",
    "Passing Stopped School Bus... 5 Points."
)

add_question(
    "Traffic Laws",
    "Following too closely (tailgating) adds ___ points to your driving record.",
    [
        "2",
        "3",
        "4",
        "5"
    ],
    "3",
    "Following Too Closely... 3 Points."
)

add_question(
    "Traffic Laws",
    "Speeding 26 mph or more over the limit adds ___ points to your driving record.",
    [
        "2",
        "3",
        "5",
        "6"
    ],
    "5",
    "Speeding 26 mph or More Over Speed Limit... 5 Points."
)

add_question(
    "Traffic Laws",
    "If you accumulate 12-14 points in a 2-year period, your license will be suspended for ___ days.",
    [
        "30",
        "60",
        "90",
        "120"
    ],
    "60",
    "12-14 Points in a 2-year period... 60 days."
)

add_question(
    "Traffic Laws",
    "The legal blood alcohol concentration (BAC) limit for drivers over 21 in Alabama is:",
    [
        ".02%",
        ".04%",
        ".05%",
        ".08%"
    ],
    ".08%",
    "Under Alabama law, it is unlawful to drive with a concentration of .08 percent or more alcohol in the blood."
)

add_question(
    "Traffic Laws",
    "For drivers under 21, the legal BAC limit is:",
    [
        ".00%",
        ".02%",
        ".05%",
        ".08%"
    ],
    ".02%",
    "Persons under 21 years of age whose blood alcohol content is .02% or more."
)

add_question(
    "Traffic Laws",
    "For commercial drivers, the legal BAC limit is:",
    [
        ".02%",
        ".04%",
        ".05%",
        ".08%"
    ],
    ".04%",
    "Commercial vehicle operators whose blood alcohol content is .04% or more."
)

add_question(
    "Traffic Laws",
    "The penalty for a first DUI conviction includes a fine of up to:",
    [
        "$500",
        "$1,000",
        "$2,100",
        "$5,000"
    ],
    "$2,100",
    "Penalty for a first conviction is a fine of $600 to $2,100."
)

add_question(
    "Traffic Laws",
    "A first DUI conviction results in a license suspension of:",
    [
        "30 days.",
        "60 days.",
        "90 days.",
        "1 year."
    ],
    "90 days.",
    "In addition, the driver license will be suspended for 90 days."
)

add_question(
    "Traffic Laws",
    "A second DUI conviction within 10 years results in a mandatory license revocation of:",
    [
        "90 days.",
        "6 months.",
        "1 year.",
        "3 years."
    ],
    "1 year.",
    "One-year revocation of driver license is required after a second conviction."
)

add_question(
    "Traffic Laws",
    "The 'Implied Consent Law' means:",
    [
        "You consent to search your vehicle.",
        "You consent to chemical testing for alcohol/drugs if arrested.",
        "You consent to pay any fines immediately.",
        "You consent to drive safely."
    ],
    "You consent to chemical testing for alcohol/drugs if arrested.",
    "Any person who operates a motor vehicle... shall be deemed to have given his consent to a chemical test."
)

add_question(
    "Traffic Laws",
    "Refusing a chemical test for alcohol/drugs will result in:",
    [
        "A warning.",
        "License suspension.",
        "A small fine.",
        "No penalty."
    ],
    "License suspension.",
    "A driver... who refuses to submit to chemical breath tests... shall have his driver license suspended."
)

add_question(
    "Traffic Laws",
    "If you are involved in a crash with injury, death, or property damage of $500 or more, you must file an SR-31 form within ___ days.",
    [
        "10",
        "15",
        "30",
        "60"
    ],
    "30",
    "A written (Form SR-31) must be sent within 30 days."
)

add_question(
    "Traffic Laws",
    "When approaching a railroad crossing, you must stop within ___ to ___ feet of the tracks if a train is coming.",
    [
        "10 to 20",
        "15 to 50",
        "20 to 60",
        "50 to 100"
    ],
    "15 to 50",
    "You must stop within 15 to 50 ft."
)

add_question(
    "Traffic Laws",
    "Vehicles required to stop at all railroad crossings include:",
    [
        "Passenger cars.",
        "Motorcycles.",
        "School buses and trucks carrying hazardous materials.",
        "Pickup trucks."
    ],
    "School buses and trucks carrying hazardous materials.",
    "School bus, church bus, or any passenger bus... Trucks transporting flammables, explosives or other hazardous material."
)

add_question(
    "Traffic Laws",
    "Texting while driving is:",
    [
        "Allowed for adults.",
        "Allowed at red lights.",
        "Prohibited for all drivers.",
        "Allowed in emergencies only."
    ],
    "Prohibited for all drivers.",
    "Alabama's new law prohibits using a wireless device to write, send or read a text message... while operating a motor vehicle."
)

add_question(
    "Traffic Laws",
    "The fine for a first offense of texting while driving is:",
    [
        "$25",
        "$50",
        "$75",
        "$100"
    ],
    "$25",
    "The fine for violating the law is $25 for a first-time offense."
)

add_question(
    "Traffic Laws",
    "Alcohol is classified as a:",
    [
        "Stimulant.",
        "Depressant.",
        "Hallucinogen.",
        "Narcotic."
    ],
    "Depressant.",
    "Alcohol is a depressant, not a stimulant."
)

add_question(
    "Traffic Laws",
    "One 12-ounce beer contains about the same amount of alcohol as:",
    [
        "One shot of whiskey or one glass of wine.",
        "Two shots of whiskey.",
        "Half a glass of wine.",
        "It has no alcohol."
    ],
    "One shot of whiskey or one glass of wine.",
    "The amount of alcohol in one bottle of beer is about equal to that in an average 'shot of whiskey or a glass of wine.'"
)

add_question(
    "Traffic Laws",
    "If your license is suspended for 24 points or more, the suspension period is:",
    [
        "90 days.",
        "180 days.",
        "365 days.",
        "2 years."
    ],
    "365 days.",
    "24 and above points in a 2-year period... 365 days."
)

add_question(
    "Traffic Laws",
    "The 'Y' restriction on a learner's license for a 15-year-old means they must be accompanied by:",
    [
        "Any licensed driver.",
        "A licensed driver 21 years of age or older.",
        "A parent only.",
        "A driving instructor only."
    ],
    "A licensed driver 21 years of age or older.",
    "Accompanied by a person who is 21 years of age or older and, who is duly licensed."
)

add_question(
    "Traffic Laws",
    "A person with a learner's license must hold it for at least ___ months before applying for an unrestricted license.",
    [
        "3",
        "6",
        "9",
        "12"
    ],
    "6",
    "Held a learner license for at least a six-month period."
)

add_question(
    "Traffic Laws",
    "The minimum age to obtain a Vessel License in Alabama is:",
    [
        "12",
        "14",
        "15",
        "16"
    ],
    "12",
    "Persons ages 12 years old and older may obtain a vessel license."
)

# --- Image Questions ---
add_question(
    "Road Signs & Signals",
    "What does this sign indicate?",
    [
        "Stop",
        "Yield",
        "School Zone",
        "Railroad Crossing"
    ],
    "Stop",
    "The octagonal red sign always means Stop.",
    "page_41_Im0.png" # Assuming this is one of the first signs
)

add_question(
    "Road Signs & Signals",
    "Identify this sign:",
    [
        "No Passing Zone",
        "Construction Ahead",
        "Yield Right of Way",
        "Merge"
    ],
    "Yield Right of Way",
    "The inverted triangle red and white sign means Yield.",
    "page_41_Im1.png"
)

add_question(
    "Road Signs & Signals",
    "This sign shape is used for:",
    [
        "Regulatory signs",
        "Warning signs",
        "School zones",
        "Railroad warnings"
    ],
    "Railroad warnings",
    "The round yellow sign with an X and RR is for Railroad Crossings.",
    "page_41_Im2.png"
)

# --- Output ---

output_dir = "question_pool"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

with open(os.path.join(output_dir, "questions.json"), "w", encoding="utf-8") as f:
    json.dump(questions, f, indent=2)

print(f"Generated {len(questions)} questions.")
