
import streamlit as st
import re

st.set_page_config(page_title="KnowYourHazards Tool", layout="centered")

st.title("KnowYourHazards Tool")
st.markdown("### Manual Hazard Entry and Classification")

# --- Regulatory Check ---
st.header("1. Regulatory Exemption")
reg1 = st.text_input("Is the substance listed in REACH Annex IV / V?", "")
reg2 = st.text_input("Is the substance listed in OSPAR PLONOR?", "")

# --- GHS Classification ---
st.header("2. GHS Hazard Statement")
ghs_statement = st.text_input("GHS Environmental Hazard Phrase", "")

# --- Toxicity Section ---
st.header("3. Toxicity (GESAMP Scores)")
st.subheader("Single or Mixture Assessment?")
is_mixture = st.radio("Select composition type:", ["Single Component", "Mixture"], key="mixtype") == "Mixture"

st.subheader("GESAMP Scores")
if is_mixture:
    orgAc = st.text_input("Mixture Acute Toxicity (e.g. Score 4 - Moderately Toxic)", key="orgAc_mix")
    orgCh = st.text_input("Mixture Chronic Toxicity", key="orgCh_mix")
else:
    orgAc = st.text_input("Single Acute Toxicity", key="orgAc_single")
    orgCh = st.text_input("Single Chronic Toxicity", key="orgCh_single")

metalAc = st.selectbox("Metal Category (Acute)", ["None", "Category 1", "Category 2"], key="metalAc")
metalCh = st.selectbox("Metal Category (Chronic)", ["None", "Category 1", "Category 2"], key="metalCh")

# --- Bioaccumulation Section ---
st.header("4. Bioaccumulation")
bio_L2 = st.text_input("Bioaccumulation Classification (e.g. High Concern)", "")
bio_M2 = st.text_input("Mixture Bioaccumulation Trigger (e.g. vPvB mixture)", "")

# --- Persistence Section ---
st.header("5. Persistence")
pbt_L3 = st.text_input("PBT Classification (e.g. vPvB, P)", "")
pbt_K3 = st.text_input("Biodegradability (e.g. Low, Moderate, High)", "")

# === Hazard Logic Functions ===
def extract_score(txt):
    match = re.search(r"Score\s+(\d+)", txt)
    return int(match.group(1)) if match else 0

def metal_score(txt):
    txt = txt.lower()
    if "category 1" in txt:
        return 6
    elif "category 2" in txt:
        return 5
    return 0

def bioaccum_score(txt):
    txt = txt.lower()
    if "high concern" in txt:
        return 3
    elif "moderate concern" in txt:
        return 2
    return 0

def bio_trigger_score(txt):
    txt = txt.lower()
    if "vpvb" in txt:
        return 3
    elif "pbt" in txt:
        return 2
    return 0

def pbt_score(txt):
    txt = txt.lower().strip()
    if "vpvb" in txt:
        return 3
    elif txt == "p":
        return 2
    return 0

def biodeg_score(txt):
    txt = txt.lower()
    if "low" in txt:
        return 2
    elif "moderate" in txt:
        return 1
    return 0

# --- Button to Run Logic ---
if st.button("Run Hazard Assessment", key="run_button"):

    if (reg1 == "" and reg2 == "") or        (reg1 != "" and "not listed" not in reg1.lower()) or        (reg2 != "" and "not listed" not in reg2.lower()):
        st.info("All components are pre-approved or exempt. Assessment skipped.")
    else:
        orgAcScore = extract_score(orgAc)
        orgChScore = extract_score(orgCh)
        metAcScore = min(metal_score(metalAc), 4)
        metChScore = min(metal_score(metalCh), 4)
        baseAc = max(orgAcScore, metAcScore)
        baseCh = max(orgChScore, metChScore)
        hazard_tox = min(max(baseAc, baseCh), 4)

        bio_score = max(bioaccum_score(bio_L2), bio_trigger_score(bio_M2))
        pbt_val = max(pbt_score(pbt_L3), biodeg_score(pbt_K3))

        final_score = max(hazard_tox, bio_score)
        elevated = False
        if pbt_val >= 2 and final_score < pbt_val:
            final_score = pbt_val
            elevated = True

        if final_score == 4:
            rating = "Final Rating: Severe hazard – strict controls required."
        elif final_score == 3:
            rating = "Final Rating: High concern – risk mitigation necessary."
        elif final_score == 2:
            rating = "Final Rating: Moderate concern – exercise caution."
        elif final_score == 1:
            rating = "Final Rating: Low concern."
        else:
            rating = "Final Rating: Negligible hazard."

        statement = (
            f"Final Hazard Assessment:\n"
            f"{ghs_statement}\n"
            f"Toxicity Rank: {hazard_tox}\n"
            f"Bioaccumulation: {'vB' if bio_score==3 else 'B' if bio_score==2 else 'Not significant'}\n"
            f"{'Persistence elevates overall hazard.\n' if elevated else ''}"
            f"{rating}"
        )
        st.success(statement)
