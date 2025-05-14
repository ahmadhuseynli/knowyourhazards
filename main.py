
import streamlit as st
import re

st.set_page_config(page_title="KnowYourHazards Tool", layout="centered")
st.title("KnowYourHazards Tool")
st.markdown("### Manual Hazard Entry and Classification")

# Regulatory inputs
reg1 = st.text_input("C4 – REACH Annex IV/V listing", "")
reg2 = st.text_input("C5 – OSPAR PLONOR listing", "")

# GHS Statement
ghs = st.text_input("C3 – GHS Environmental Hazard Phrase", "")

# Toxicity Input
st.header("Toxicity Inputs")
is_mixture = st.radio("Is it a mixture?", ["Yes", "No"]) == "Yes"
if is_mixture:
    orgAc_txt = st.text_input("Mixture Acute Toxicity (H3)", "")
    orgCh_txt = st.text_input("Mixture Chronic Toxicity (H13)", "")
else:
    orgAc_txt = st.text_input("Single Acute Toxicity (F3)", "")
    orgCh_txt = st.text_input("Single Chronic Toxicity (F13)", "")

metalAc_txt = st.text_input("Metal Acute Category (C8)", "")
metalCh_txt = st.text_input("Metal Chronic Category (C9)", "")

# Component-level triggers
st.header("Component-level Triggers")
component_data = []
for i in range(3, 7):
    name = st.text_input(f"Component {i} name (A{i})", "")
    pct = st.text_input(f"Component {i} percentage (B{i})", "")
    ac_txt = st.text_input(f"Component {i} Acute (F{i})", "")
    ch_txt = st.text_input(f"Component {i} Chronic (F{i+10})", "")
    component_data.append((name, pct, ac_txt, ch_txt))

# Bioaccumulation
st.header("Bioaccumulation")
bio_L2 = st.text_input("L2 – Bioaccumulation concern text", "")
bio_M2 = st.text_input("M2 – Mixture Bioaccumulation trigger", "")

# Persistence
st.header("Persistence")
pbt_L3 = st.text_input("L3 – PBT label", "")
pbt_K3 = st.text_input("K3 – Biodegradability", "")


# --- Helper functions ---
def extract_score(text):
    match = re.search(r"Score\s+(\d+)", text)
    return int(match.group(1)) if match else 0

def metal_cat_score(txt):
    s = txt.lower()
    if "category 1" in s:
        return 6
    elif "category 2" in s:
        return 5
    return 0

def map_bio_accum(txt):
    s = txt.lower()
    if "high concern" in s:
        return 3
    elif "moderate concern" in s:
        return 2
    return 0

def map_bio_trigger(txt):
    s = txt.lower()
    if "vpvb" in s:
        return 3
    elif "pbt" in s:
        return 2
    return 0

def map_pbt(txt):
    s = txt.lower()
    if "vpvb" in s:
        return 3
    elif s.strip() == "p":
        return 2
    return 0

def map_biodeg(txt):
    s = txt.lower()
    if "low" in s:
        return 2
    elif "moderate" in s:
        return 1
    return 0

# --- Assessment Execution ---
if st.button("Generate Hazard Assessment"):
    # Regulatory Exemption Logic
    skip = False
    if reg1 == "" and reg2 == "":
        skip = True
    elif (reg1 != "" and "not listed" not in reg1.lower()) or (reg2 != "" and "not listed" not in reg2.lower()):
        skip = True
    else:
        skip = False

    if skip:
        st.info("Final Hazard Assessment: All components pre-approved or no inputs. Skipped.")
    else:
        # 1. Toxicity
        orgAc = extract_score(orgAc_txt)
        orgCh = extract_score(orgCh_txt)
        metAc = min(metal_cat_score(metalAc_txt), 4)
        metCh = min(metal_cat_score(metalCh_txt), 4)
        baseAc = max(orgAc, metAc)
        baseCh = max(orgCh, metCh)
        hazard_tox = min(max(baseAc, baseCh), 4)

        # 2. Component Triggers
        compTrig = False
        for name, pct_txt, ac_txt, ch_txt in component_data:
            if name.strip() != "":
                try:
                    pct = float(pct_txt)
                except:
                    pct = 0
                ac = extract_score(ac_txt)
                ch = extract_score(ch_txt)
                if (ac == 6 and pct >= 0.1) or (ac == 5 and pct >= 1) or (ac == 4 and pct >= 10) or                    (ch == 6 and pct >= 0.1) or (ch == 5 and pct >= 1) or (ch == 4 and pct >= 10):
                    compTrig = True
                    break
        if compTrig and hazard_tox < 3:
            hazard_tox += 1

        # 3. Bioaccumulation
        bioScore = max(map_bio_accum(bio_L2), map_bio_trigger(bio_M2))
        bioStatement = "Bioaccumulation: Very high (vB). " if bioScore == 3 else                        "Bioaccumulation: Moderate (B). " if bioScore == 2 else ""

        # 4. Persistence
        pbtScore = max(map_pbt(pbt_L3), map_biodeg(pbt_K3))

        # 5. Final ranking
        initialRank = max(hazard_tox, bioScore)
        finalRank = initialRank
        persistenceStatement = ""
        if pbtScore >= 2 and initialRank < pbtScore:
            finalRank = pbtScore
            persistenceStatement = "Persistence elevates overall hazard. "

        # 6. Rating text
        if finalRank == 4:
            ratingText = "Final Rating: Severe hazard – strict controls required."
        elif finalRank == 3:
            ratingText = "Final Rating: High concern – risk mitigation necessary."
        elif finalRank == 2:
            ratingText = "Final Rating: Moderate concern – exercise caution."
        elif finalRank == 1:
            ratingText = "Final Rating: Low concern."
        else:
            ratingText = "Final Rating: Negligible hazard."

        # 7. Output
        final = f"Final Hazard Assessment: {ghs} Toxicity rank {hazard_tox}. {bioStatement}{persistenceStatement}{ratingText}"
        st.success(final)
