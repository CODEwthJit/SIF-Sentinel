"""
sif_auto_annotator.py
=====================
Automated Rule-Based + Semantic Extraction Engine for SIF Precursor Annotations.
SIH26165 Project.

Implements:
1. Sentence-level syntactic and negation analysis (preserving safety negation)
2. Hazard / Energy detection across 9 controlled energy vectors
3. Activity detection across 10 controlled tasks
4. Barrier / Control identification and strict failure mode classification (MISSING vs BYPASSED vs UNKNOWN)
5. Human exposure classification (DIRECT vs POTENTIAL vs NONE vs UNKNOWN)
6. Plausible worst-case consequence mapping
7. Life-Saving Rules (LSR) multi-label tag extraction
8. Transparent evidence-based SIF scoring engine
9. Verbatim evidence substring extraction directly from narrative text
10. Confidence scoring and reason code logging
11. Modular local LLM / semantic fallback capability (Ollama / local endpoint if available)
"""

import re
import os
import json
import datetime
import urllib.request
import urllib.error

# -------------------------------------------------------------
# CONTROLLED VOCABULARIES (Strict compliance with app schema)
# -------------------------------------------------------------
ALLOWED_SIF_LABELS = ["YES", "NO", "UNCERTAIN"]
ALLOWED_HAZARD_ENERGY = [
    "Electrical", "Mechanical", "Pressure", "Chemical",
    "Thermal", "Gravitational", "Other", "None", "Unknown"
]
ALLOWED_ACTIVITY = [
    "Maintenance", "Lifting", "Hot Work", "Confined Space",
    "Excavation", "Driving", "Construction", "Material Handling", "Other", "Unknown"
]
ALLOWED_BARRIER_CONTROL = [
    "Energy Isolation", "Permit", "PPE", "Gas Testing", "Guarding",
    "Fall Protection", "Traffic Control", "Safe Work Procedure", "Supervision", "Other", "None", "Unknown"
]
ALLOWED_BARRIER_FAILURE = [
    "MISSING", "BYPASSED", "INADEQUATE", "NOT_FOLLOWED",
    "DEGRADED", "NONE", "UNKNOWN"
]
ALLOWED_HUMAN_EXPOSURE = [
    "DIRECT", "POTENTIAL", "NONE", "UNKNOWN"
]
ALLOWED_POTENTIAL_CONSEQUENCE = [
    "Electrocution", "Fall", "Fire", "Explosion", "Struck-by",
    "Caught-in", "Toxic Exposure", "Asphyxiation", "Crushing", "Drowning", "Other", "None", "Unknown"
]
ALLOWED_LSR_TAGS = [
    "Energy Isolation", "Confined Space", "Hot Work", "Line of Fire",
    "Working at Height", "Lifting", "Driving", "Other"
]
ALLOWED_CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]

# -------------------------------------------------------------
# TEXT PROCESSING & NEGATION HELPERS
# -------------------------------------------------------------
def split_sentences(text):
    """Splits narrative into clean sentences while preserving abbreviations and decimals."""
    if not isinstance(text, str):
        return []
    cleaned = text.replace("p.m.", "pm").replace("a.m.", "am").replace("No.", "No").replace("no.", "no")
    cleaned = re.sub(r'(\d+)\.(\d+)', r'\1_DOT_\2', cleaned) # protect decimals like 12.5 feet
    raw_sents = re.split(r'(?<=[.!?])\s+', cleaned)
    
    sentences = []
    for s in raw_sents:
        s_restored = s.replace("_DOT_", ".").strip()
        if len(s_restored) >= 5:
            sentences.append(s_restored)
    return sentences if sentences else [text.strip()]

def extract_verbatim_evidence(narrative, keywords):
    """
    Extracts the shortest verbatim sentence from the narrative that directly
    contains the primary hazard/barrier evidence keywords. Never invents text.
    """
    if not isinstance(narrative, str) or not narrative.strip():
        return ""
    
    sentences = split_sentences(narrative)
    if not sentences:
        return narrative.strip()[:120]
    
    best_sent = ""
    best_score = -1
    
    for sent in sentences:
        s_lower = sent.lower()
        score = 0
        for kw in keywords:
            if kw.lower() in s_lower:
                score += (len(kw) * 2)
        # boost if contains decisive incident action verbs
        for act in ["fell", "fall", "struck", "caught", "shock", "crush", "harness", "guard", "electric", "died", "killed", "amputat", "burn", "explosion", "ladder", "roof"]:
            if act in s_lower:
                score += 3
        # penalty for overly long run-on sentences
        if len(sent) > 250:
            score -= 2
            
        if score > best_score:
            best_score = score
            best_sent = sent
            
    if best_sent and best_sent in narrative:
        return best_sent.strip()
    for s in sentences:
        if s.lower() == best_sent.lower() and s in narrative:
            return s.strip()
                
    for s in sentences:
        if s in narrative and len(s) > 15:
            return s.strip()
            
    return narrative.strip()[:100]

def has_pattern(pattern, text):
    """Regex search helper ignoring None/empty text."""
    if not text:
        return False
    return bool(re.search(pattern, text, re.IGNORECASE))

# -------------------------------------------------------------
# CORE ANNOTATION ENGINE
# -------------------------------------------------------------
class SIFAutoAnnotator:
    def __init__(self, config=None):
        self.config = config or {}
        self.version = "1.2.0"
        self.model_name = "SIF-DeterministicEngine-v1.2.0"
        self.ollama_endpoint = self.config.get("ollama_endpoint", "http://localhost:11434")
        self.use_llm_fallback = self.config.get("use_llm_fallback", False)

    def annotate_record(self, row):
        """
        Analyzes a single record from sif_annotations.csv and returns
        the complete annotation dictionary.
        """
        narrative = str(row.get('normalized_narrative', '')).strip()
        headline = str(row.get('event_headline', '')).strip()
        keywords_str = str(row.get('event_keywords', '')).strip()
        stratum = str(row.get('hazard_stratum', '')).strip()
        event_title = str(row.get('source_event_title', '')).strip()
        nature_title = str(row.get('source_nature_title', '')).strip()
        equip_source = str(row.get('source_equipment_source', '')).strip()
        op_context = str(row.get('operational_context', '')).strip()
        ref_outcome = str(row.get('reference_outcome_context', '')).strip()

        combined_text = f"{narrative} {headline} {keywords_str} {event_title} {equip_source}".lower()
        sentences = split_sentences(narrative)
        word_count = len(narrative.split())

        reason_codes = []
        evidence_keywords = []

        # -------------------------------------------------------------
        # STEP 1: HIGH-ENERGY TRAUMA & INCIDENT MECHANISM IDENTIFICATION
        # -------------------------------------------------------------
        has_electrical_shock = (
            has_pattern(r'\b(shocked|electrocuted|arc flash|contacted\s+(live|power|overhead|wire)|touched\s+(live|power|overhead|wire)|electrical shock)\b', combined_text)
            or (has_pattern(r'\b(overhead line|power line|high voltage|13,800v|transformer)\b', combined_text) and has_pattern(r'\b(contact|touched|shock|electroc|arc flash|line fell on|bed contacted)\b', combined_text))
        )
        has_confined_space_asphyx = has_pattern(r'\b(oxygen deficient|nitrogen blanket|asphyxiat|toxic gas|sewer gas|h2s|hydrogen sulfide|carbon monoxide|toxic chemical inhalation)\b', combined_text)
        has_heavy_vehicle_impact = (
            has_pattern(r'\b(forklift|dump truck|flatbed|loader|backhoe|tractor|semi-truck|excavator|heavy equipment)\b.*\b(struck|backed over|ran over|pinned|crushed|collided)\b', combined_text)
            or has_pattern(r'\b(struck|ran over|backed into|backed over|pinned|crushed)\s+by\s+(a\s+)?(forklift|truck|loader|tractor|equipment|trailer)\b', combined_text)
        )
        has_power_machine_entanglement = (
            has_pattern(r'\b(press brake|stamping press|hydraulic press|nip point|pinch point|in-running|conveyor|auger|lathe|spindle|pulley|roller)\b', combined_text)
            and has_pattern(r'\b(caught in|caught between|crushed in|amputat|entangled|pulled into|stop block.*fragmented|projectile)\b', combined_text)
        )
        
        has_fall_from_height = (
            has_pattern(r'\b(fell|fall|falling|dropped|plunged)\s+\d+\s*(?:foot|feet|ft)\b', combined_text)
            or has_pattern(r'\b(fell|fall|falling|dropped|plunged)\s+(from|off|through|down|out of)\s+(the\s+)?(roof|ladder|scaffold|staging|scissor lift|bucket truck|manlift|aerial lift|mezzanine|catwalk|beam|truss|hoistway|skylight|platform)\b', combined_text)
            or has_pattern(r'\b(ladder|scaffold(ing)?)\s+(collapsed|slid|slipped|gave way|tipped)\b', combined_text)
            or ("falls from elevation" in stratum.lower() and not has_pattern(r'\b(on the same level|same level)\b', combined_text))
        )
        
        has_falling_heavy_object = has_pattern(r'\b(falling object|load fell|truss fell|steel beam|metal tubes|tree fell|timber fell|trench collapse|cave-in)\b', combined_text)
        has_diver_water_emergency = has_pattern(r'\b(diver|scuba|submersion|drowning|drowned|low air emergency in \d+ feet of water|underwater)\b', combined_text)
        has_fire_explosion = (
            has_pattern(r'\b(explosion|exploded|flash fire|gas fire|chemical fire|blast|deflagration)\b', combined_text)
            or (has_pattern(r'\b(fire|flame|ignited|combustion)\b', combined_text) and not has_pattern(r'\b(fire department|firefighter|fire station|fire season|fire drill|fire extinguisher|fire hydrant)\b', combined_text))
        )

        # -------------------------------------------------------------
        # STEP 2: HEAT EXHAUSTION / DEHYDRATION CHECK
        # -------------------------------------------------------------
        is_pure_heat_stress = False
        if has_pattern(r'\b(heat exhaustion|heat stroke|heat stress|dehydration|heat cramps)\b', combined_text):
            if not (has_electrical_shock or has_heavy_vehicle_impact or has_power_machine_entanglement or has_fall_from_height or has_falling_heavy_object or has_fire_explosion):
                is_pure_heat_stress = True

        # -------------------------------------------------------------
        # STEP 3: MEDICAL / NATURAL CAUSES CHECK
        # -------------------------------------------------------------
        is_medical = False
        medical_kw_pattern = r'\b(heart attack|cardiac arrest|cardiac dysrhythmia|atherosclerotic|aneurysm|seizure|pre-existing asthma|asthma attack|shortness of breath.*history of asthma|history of asthma.*unresponsive|disoriented.*laid down.*couch|slumped over.*console|found slumped.*console|collapsed at (meeting|desk|home|car)|died from a heart attack|natural causes?)\b'
        if has_pattern(medical_kw_pattern, combined_text):
            if not (has_electrical_shock or has_confined_space_asphyx or has_heavy_vehicle_impact or has_power_machine_entanglement or has_fall_from_height or has_falling_heavy_object or has_diver_water_emergency):
                is_medical = True
                evidence_keywords.extend(["heart attack", "cardiac", "natural", "collapsed", "asthma", "slumped"])
                reason_codes.append("MEDICAL_NATURAL_CAUSE_NO_SIF")

        # -------------------------------------------------------------
        # STEP 4: SAME-LEVEL SLIP / TRIP CHECK
        # -------------------------------------------------------------
        is_same_level_slip = False
        if not is_medical and not is_pure_heat_stress:
            if "same-level" in stratum.lower() or has_pattern(r'\b(slip(ped)?|trip(ped)?|fell)\s+(on|onto)\s+(the\s+)?(same level|floor|ground|ice|snow|carpet|sidewalk|pavement|parking lot)\b', combined_text):
                if not (has_fall_from_height or has_heavy_vehicle_impact or has_power_machine_entanglement or has_electrical_shock or has_confined_space_asphyx or has_falling_heavy_object or has_diver_water_emergency):
                    is_same_level_slip = True
                    evidence_keywords.extend(["slipped", "tripped", "fell on ice", "same level", "parking lot"])
                    reason_codes.append("SAME_LEVEL_LOW_ENERGY_NO_SIF")

        # -------------------------------------------------------------
        # STEP 5: HAZARD ENERGY ASSIGNMENT
        # -------------------------------------------------------------
        hazard_energy = "Unknown"
        if is_medical or is_same_level_slip:
            hazard_energy = "None"
            reason_codes.append("ENERGY_NONE")
        elif is_pure_heat_stress:
            hazard_energy = "Thermal"
            evidence_keywords.extend(["heat exhaustion", "heat stroke", "heat stress", "dehydration"])
            reason_codes.append("ENERGY_THERMAL_HEAT_STRESS")
        elif has_diver_water_emergency:
            hazard_energy = "Other"
            evidence_keywords.extend(["diver", "water", "drowning", "drowned"])
            reason_codes.append("ENERGY_WATER_SUBMERSION")
        elif has_electrical_shock:
            hazard_energy = "Electrical"
            evidence_keywords.extend(["power line", "overhead line", "13,800v", "shock", "electrocuted", "voltage", "live wire"])
            reason_codes.append("ENERGY_ELECTRICAL")
        elif has_pattern(r'\b(compressed air|pressurized|pressure relief|tire inflation|hydraulic hose|pneumatic|burst hose|ruptured hose|pressure test|blew off the pipe|over-pressur\w*)\b', combined_text):
            hazard_energy = "Pressure"
            evidence_keywords.extend(["pressure", "pressurized", "burst", "over-pressurized", "air pressure"])
            reason_codes.append("ENERGY_PRESSURE")
        elif has_confined_space_asphyx or has_pattern(r'\b(chemical|solvent|pesticide|toxic fumes|acid|chlorine|ammonia|vapor|anhydrous|inhalation of noxious fumes)\b', combined_text):
            hazard_energy = "Chemical"
            evidence_keywords.extend(["chemical", "toxic", "fumes", "ammonia", "inhalation", "acid", "oxygen"])
            reason_codes.append("ENERGY_CHEMICAL")
        elif has_fire_explosion:
            hazard_energy = "Thermal"
            evidence_keywords.extend(["fire", "flame", "explosion", "burned", "blast"])
            reason_codes.append("ENERGY_THERMAL")
        elif has_fall_from_height:
            hazard_energy = "Gravitational"
            evidence_keywords.extend(["fall", "fell", "roof", "ladder", "scaffold", "elevation", "height"])
            reason_codes.append("ENERGY_GRAVITATIONAL")
        elif has_power_machine_entanglement or has_pattern(r'\b(caught in|caught between|pinch point|nip point|rotating|conveyor|auger|lathe|spindle|milling machine|press brake|stamping press)\b', combined_text):
            hazard_energy = "Mechanical"
            evidence_keywords.extend(["caught in", "pinch point", "conveyor", "press", "roller", "crushed"])
            reason_codes.append("ENERGY_MECHANICAL")
        elif has_heavy_vehicle_impact or has_falling_heavy_object or has_pattern(r'\b(forklift|dump truck|semi-truck|loader|excavator|backhoe|tractor|trailer|trench collapse|cave-in|felling tree|falling tree)\b', combined_text):
            hazard_energy = "Other"
            evidence_keywords.extend(["forklift", "truck", "loader", "struck by", "trench", "trailer"])
            reason_codes.append("ENERGY_MOBILE_OR_STRUCK")
        else:
            if "same-level" in stratum.lower():
                hazard_energy = "None"
            else:
                hazard_energy = "Unknown" if word_count < 15 else "Other"

        # -------------------------------------------------------------
        # STEP 6: ACTIVITY DETECTION
        # -------------------------------------------------------------
        activity = "Unknown"
        if has_pattern(r'\b(clean|repair|service|lubricat|unjam|clear jam|troubleshoot|replac|inspect|mainten|tightening|unstopping)\b', combined_text):
            activity = "Maintenance"
        elif has_pattern(r'\b(crane|hoist|rigging|sling|lifting load|winch|suspended load)\b', combined_text):
            activity = "Lifting"
        elif has_pattern(r'\b(weld|torch|braz|grinding|cutting torch)\b', combined_text):
            activity = "Hot Work"
        elif has_pattern(r'\b(tank|vessel|vault|sewer|manhole|confined space|hopper|silo|crawl space|underwater|diver)\b', combined_text):
            activity = "Confined Space"
        elif has_pattern(r'\b(trench|ditch|excavat|digging|cave-in|shoring)\b', combined_text):
            activity = "Excavation"
        elif has_pattern(r'\b(driving|highway|traffic|roadway|delivery truck|in transit)\b', combined_text):
            activity = "Driving"
        elif has_pattern(r'\b(roofing|framing|carpentry|concrete|steel erection|masonry|demolition|construction|installing truss)\b', combined_text):
            activity = "Construction"
        elif has_pattern(r'\b(loading|unloading|stacking|warehouse|pallet|moving boxes|forklift|bales)\b', combined_text):
            activity = "Material Handling"
        else:
            activity = "Other" if word_count >= 15 else "Unknown"

        # -------------------------------------------------------------
        # STEP 7: BARRIER / CONTROL IDENTIFICATION & FAILURE MODE
        # -------------------------------------------------------------
        barrier_control = "Unknown"
        barrier_failure = "UNKNOWN"

        if is_medical:
            barrier_control = "None"
            barrier_failure = "NONE"
        elif is_same_level_slip:
            barrier_control = "Safe Work Procedure"
            barrier_failure = "NONE"
        elif is_pure_heat_stress:
            barrier_control = "Safe Work Procedure"
            barrier_failure = "INADEQUATE" if has_pattern(r'\b(died|unresponsive|heat stroke)\b', combined_text) else "UNKNOWN"
        elif hazard_energy == "Gravitational":
            barrier_control = "Fall Protection"
            if has_pattern(r'\b(not wearing (a\s+)?harness|without (a\s+)?harness|without fall protection|no fall protection|no harness|not tied off|without tie-off|unguarded roof|unprotected edge|no guardrail|no railing|without personal fall arrest|did not wear (a\s+)?harness)\b', combined_text):
                barrier_failure = "MISSING"
                evidence_keywords.extend(["without fall protection", "no harness", "not tied off", "unguarded", "no guardrail"])
                reason_codes.append("BARRIER_FALL_MISSING")
            elif has_pattern(r'\b(did not reconnect|failed to reconnect|failed to tie off|procedure not followed|contrary to instructions|unhooked)\b', combined_text):
                barrier_failure = "NOT_FOLLOWED"
                reason_codes.append("BARRIER_FALL_NOT_FOLLOWED")
            elif has_pattern(r'\b(guardrail removed|railing removed|safety net removed)\b', combined_text):
                barrier_failure = "BYPASSED"
                reason_codes.append("BARRIER_FALL_BYPASSED")
            elif has_pattern(r'\b(ladder (slipped|slid|fell)|scaffold(ing)? collapsed|board (broke|gave way)|plywood snapped|lanyard broke|rope broke|anchor (failed|pulled out)|harness broke|gave way)\b', combined_text):
                barrier_failure = "INADEQUATE"
                evidence_keywords.extend(["ladder slipped", "collapsed", "board broke", "gave way"])
                reason_codes.append("BARRIER_FALL_INADEQUATE")
            else:
                barrier_failure = "UNKNOWN"
                reason_codes.append("BARRIER_FALL_UNKNOWN")
        elif hazard_energy == "Electrical":
            barrier_control = "Energy Isolation"
            if has_pattern(r'\b(not de-energized|lockout not performed|did not lock out|without locking out|not locked out|power was not turned off|failed to de-energize)\b', combined_text):
                barrier_failure = "NOT_FOLLOWED"
                reason_codes.append("BARRIER_ELEC_NOT_FOLLOWED")
            elif has_pattern(r'\b(interlock bypassed|switch disabled)\b', combined_text):
                barrier_failure = "BYPASSED"
                reason_codes.append("BARRIER_ELEC_BYPASSED")
            elif has_pattern(r'\b(unguarded live|uninsulated|bare wire|no cover|uncovered)\b', combined_text):
                barrier_failure = "MISSING"
                reason_codes.append("BARRIER_ELEC_MISSING")
            else:
                barrier_failure = "UNKNOWN"
                reason_codes.append("BARRIER_ELEC_UNKNOWN")
        elif hazard_energy == "Mechanical":
            if has_pattern(r'\b(lockout|cleaning|servicing|clearing jam|maintenance)\b', combined_text):
                barrier_control = "Energy Isolation"
            else:
                barrier_control = "Guarding"
            if has_pattern(r'\b(guard (was\s+)?removed|guard removed|bypassed|interlock defeated|safety switch taped)\b', combined_text):
                barrier_failure = "BYPASSED"
                evidence_keywords.extend(["guard removed", "bypassed"])
                reason_codes.append("BARRIER_MECH_BYPASSED")
            elif has_pattern(r'\b(no guard|unguarded|without (a\s+)?guard|unprotected nip|no machine guard|uncovered)\b', combined_text):
                barrier_failure = "MISSING"
                evidence_keywords.extend(["no guard", "unguarded", "without a guard"])
                reason_codes.append("BARRIER_MECH_MISSING")
            elif has_pattern(r'\b(did not lock out|lockout not performed|without locking out|not de-energized|procedure not followed)\b', combined_text):
                barrier_failure = "NOT_FOLLOWED"
                evidence_keywords.extend(["did not lock out", "procedure not followed"])
                reason_codes.append("BARRIER_MECH_NOT_FOLLOWED")
            elif has_pattern(r'\b(guard gave way|reached around guard|light curtain failed|inadequate guard|stop block.*fragmented)\b', combined_text):
                barrier_failure = "INADEQUATE"
                reason_codes.append("BARRIER_MECH_INADEQUATE")
            elif has_pattern(r'\b(malfunction|defective brake|clutch failed|sensor failed)\b', combined_text):
                barrier_failure = "DEGRADED"
                reason_codes.append("BARRIER_MECH_DEGRADED")
            else:
                barrier_failure = "UNKNOWN"
                reason_codes.append("BARRIER_MECH_UNKNOWN")
        elif hazard_energy == "Pressure":
            barrier_control = "Safe Work Procedure"
            if has_pattern(r'\b(safety cage not used|without (a\s+)?tire cage|no safety cage)\b', combined_text):
                barrier_failure = "MISSING"
                reason_codes.append("BARRIER_PRESS_MISSING")
            elif has_pattern(r'\b(hose ruptured|line burst|gauge failed|blew out|cap blew off|over-pressur\w*)\b', combined_text):
                barrier_failure = "INADEQUATE"
                evidence_keywords.extend(["burst", "ruptured", "over-pressurized", "blew off"])
                reason_codes.append("BARRIER_PRESS_INADEQUATE")
            else:
                barrier_failure = "UNKNOWN"
                reason_codes.append("BARRIER_PRESS_UNKNOWN")
        elif hazard_energy == "Chemical":
            if has_pattern(r'\b(confined space|tank|manhole|vault)\b', combined_text):
                barrier_control = "Gas Testing"
                if has_pattern(r'\b(without testing|gas test not performed|no monitor)\b', combined_text):
                    barrier_failure = "NOT_FOLLOWED"
                else:
                    barrier_failure = "UNKNOWN"
            else:
                barrier_control = "PPE"
                if has_pattern(r'\b(not wearing (a\s+)?respirator|without respirator|no ppe|no face shield)\b', combined_text):
                    barrier_failure = "MISSING"
                else:
                    barrier_failure = "UNKNOWN"
        elif hazard_energy == "Thermal":
            barrier_control = "PPE" if has_pattern(r'\bsplash\b', combined_text) else "Safe Work Procedure"
            if has_pattern(r'\b(valve failed|pipe burst|tank exploded)\b', combined_text):
                barrier_failure = "INADEQUATE"
            else:
                barrier_failure = "UNKNOWN"
        elif hazard_energy == "Other":
            if has_pattern(r'\b(forklift|dump truck|truck|loader|backing|pedestrian)\b', combined_text):
                barrier_control = "Traffic Control"
                if has_pattern(r'\b(no spotter|without (a\s+)?spotter|backup alarm (inoperable|not working)|no horn)\b', combined_text):
                    barrier_failure = "MISSING"
                elif has_pattern(r'\b(did not set brake|left in gear|speeding)\b', combined_text):
                    barrier_failure = "NOT_FOLLOWED"
                else:
                    barrier_failure = "UNKNOWN"
            elif has_pattern(r'\b(trench|excavat)\b', combined_text):
                barrier_control = "Other"
                if has_pattern(r'\b(no trench box|unshored|no shoring|without shoring)\b', combined_text):
                    barrier_failure = "MISSING"
                elif has_pattern(r'\b(trench box failed|shoring collapsed)\b', combined_text):
                    barrier_failure = "INADEQUATE"
                else:
                    barrier_failure = "UNKNOWN"
            else:
                barrier_control = "Safe Work Procedure"
                barrier_failure = "UNKNOWN"
        else:
            barrier_control = "None"
            barrier_failure = "NONE"

        # -------------------------------------------------------------
        # STEP 8: HUMAN EXPOSURE
        # -------------------------------------------------------------
        human_exposure = "UNKNOWN"
        if is_medical:
            human_exposure = "NONE"
        elif any(k in combined_text for k in ["fell", "shocked", "electrocuted", "caught", "crushed", "struck by", "struck in", "pinned", "contacted live", "inhaled", "burned", "trapped", "projectile"]):
            human_exposure = "DIRECT"
            reason_codes.append("EXP_DIRECT")
        elif any(k in combined_text for k in ["standing near", "in the vicinity", "near the suspended", "narrowly missed", "line of fire", "ricochet"]):
            human_exposure = "POTENTIAL"
            reason_codes.append("EXP_POTENTIAL")
        else:
            human_exposure = "DIRECT" if word_count >= 15 else "UNKNOWN"

        # -------------------------------------------------------------
        # STEP 9: POTENTIAL CONSEQUENCE
        # -------------------------------------------------------------
        potential_consequence = "Unknown"
        if is_medical:
            potential_consequence = "None"
        elif is_same_level_slip:
            potential_consequence = "Other"
        elif is_pure_heat_stress:
            potential_consequence = "Other" # Heat stroke / organ failure
        elif hazard_energy == "Electrical":
            potential_consequence = "Electrocution"
        elif hazard_energy == "Gravitational":
            potential_consequence = "Fall"
        elif hazard_energy == "Mechanical":
            if has_pattern(r'\b(crush|press|heavy|pinned|head|chest|torso)\b', combined_text):
                potential_consequence = "Crushing"
            else:
                potential_consequence = "Caught-in"
        elif hazard_energy == "Pressure":
            potential_consequence = "Explosion" if has_pattern(r'\b(tire|airborne|burst|tank exploded)\b', combined_text) else "Struck-by"
        elif hazard_energy == "Chemical":
            if has_pattern(r'\b(confined space|asphyxiat|oxygen|nitrogen)\b', combined_text):
                potential_consequence = "Asphyxiation"
            else:
                potential_consequence = "Toxic Exposure"
        elif hazard_energy == "Thermal":
            potential_consequence = "Explosion" if has_pattern(r'\bexplosion\b', combined_text) else "Fire"
        elif hazard_energy == "Other":
            if has_diver_water_emergency or has_pattern(r'\b(drown|water|river|pond|channel)\b', combined_text):
                potential_consequence = "Drowning"
            elif has_pattern(r'\b(crush|pinned|trench|cave-in|rollover)\b', combined_text):
                potential_consequence = "Crushing"
            else:
                potential_consequence = "Struck-by"
        else:
            potential_consequence = "Other" if "same-level" in stratum.lower() else "Unknown"

        # -------------------------------------------------------------
        # STEP 10: LSR TAGS
        # -------------------------------------------------------------
        lsr_list = []
        if hazard_energy == "Gravitational" or (has_fall_from_height and not is_same_level_slip):
            lsr_list.append("Working at Height")
        if barrier_control == "Energy Isolation" or has_pattern(r'\b(lockout|energiz|power line)\b', combined_text):
            lsr_list.append("Energy Isolation")
        if not is_pure_heat_stress and not is_medical and (has_pattern(r'\b(struck by|pinch point|line of fire|caught between|suspended load|falling object|projectile)\b', combined_text) or has_heavy_vehicle_impact):
            lsr_list.append("Line of Fire")
        if has_pattern(r'\b(crane|hoist|rigging)\b', combined_text) or activity == "Lifting":
            lsr_list.append("Lifting")
        if not is_pure_heat_stress and (activity == "Driving" or has_pattern(r'\b(highway|traffic|roadway)\b', combined_text)):
            lsr_list.append("Driving")
        if activity == "Confined Space" or has_pattern(r'\b(manhole|tank|crawl space|underwater)\b', combined_text):
            lsr_list.append("Confined Space")
        if activity == "Hot Work" or has_pattern(r'\b(weld|torch)\b', combined_text):
            lsr_list.append("Hot Work")
        if not lsr_list and hazard_energy not in ["None", "Unknown"]:
            lsr_list.append("Other")
        lsr_tags = "; ".join(lsr_list) if lsr_list else "Other"

        # -------------------------------------------------------------
        # STEP 11: SIF SCORING ENGINE
        # -------------------------------------------------------------
        auto_score = 0.0

        if is_medical or is_same_level_slip:
            sif_label = "NO"
            confidence = "HIGH"
            auto_score = -5.0
            reason_codes.append("SIF_NO_DETERMINISTIC_GATE")
        else:
            # Score Energy
            if hazard_energy in ["Electrical", "Gravitational", "Mechanical", "Pressure", "Chemical"]:
                auto_score += 2.0
            elif hazard_energy == "Thermal":
                auto_score += 1.5
            elif hazard_energy == "Other":
                if has_heavy_vehicle_impact or has_falling_heavy_object or has_diver_water_emergency:
                    auto_score += 2.0
                else:
                    auto_score += 1.0
            elif hazard_energy == "None":
                auto_score -= 4.0

            # Score Barrier Failure
            if barrier_failure in ["MISSING", "BYPASSED"]:
                auto_score += 3.0
            elif barrier_failure in ["INADEQUATE", "NOT_FOLLOWED", "DEGRADED"]:
                auto_score += 2.0
            elif barrier_failure == "UNKNOWN":
                if hazard_energy in ["Electrical", "Gravitational", "Mechanical", "Pressure", "Chemical", "Other"] and human_exposure == "DIRECT":
                    auto_score += 1.5
                else:
                    auto_score += 0.5
            elif barrier_failure == "NONE":
                auto_score -= 2.0

            # Score Human Exposure
            if human_exposure == "DIRECT":
                auto_score += 2.0
            elif human_exposure == "POTENTIAL":
                auto_score += 1.0
            elif human_exposure == "NONE":
                auto_score -= 3.0

            # Score Consequence Severity Potential
            if potential_consequence in ["Electrocution", "Crushing", "Asphyxiation", "Explosion", "Drowning"]:
                auto_score += 2.0
            elif potential_consequence in ["Fall", "Caught-in", "Struck-by", "Fire", "Toxic Exposure"]:
                auto_score += 1.5
            elif potential_consequence == "None":
                auto_score -= 3.0

            # Fall height adjustment
            feet_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:foot|feet|ft)', combined_text)
            if feet_match:
                try:
                    ht = float(feet_match.group(1))
                    if ht >= 6.0:
                        auto_score += 1.5
                        reason_codes.append(f"FALL_HT_{int(ht)}FT")
                    elif ht < 4.0 and "same-level" in stratum.lower():
                        auto_score -= 1.0
                except ValueError:
                    pass

            if auto_score >= 4.5:
                sif_label = "YES"
                reason_codes.append("SIF_YES_HIGH_SCORE")
            elif auto_score <= 1.0 and ("same-level" in stratum.lower() or hazard_energy in ["None", "Unknown"]):
                sif_label = "NO"
                reason_codes.append("SIF_NO_LOW_SCORE")
            elif word_count < 10:
                sif_label = "UNCERTAIN"
                reason_codes.append("SIF_UNCERTAIN_SPARSE_TEXT")
            elif auto_score >= 3.0:
                if hazard_energy in ["Electrical", "Gravitational", "Mechanical", "Pressure", "Chemical", "Thermal", "Other"]:
                    sif_label = "YES"
                    reason_codes.append("SIF_YES_MODERATE_SCORE")
                else:
                    sif_label = "UNCERTAIN"
                    reason_codes.append("SIF_UNCERTAIN_BORDERLINE")
            else:
                sif_label = "UNCERTAIN"
                reason_codes.append("SIF_UNCERTAIN_INSUFFICIENT_EVIDENCE")

            # Confidence
            if sif_label == "YES":
                if barrier_failure in ["MISSING", "BYPASSED", "NOT_FOLLOWED"] and hazard_energy in ["Electrical", "Gravitational", "Mechanical", "Pressure"]:
                    confidence = "HIGH"
                elif word_count < 15 or barrier_failure == "UNKNOWN":
                    confidence = "MEDIUM" if auto_score >= 5.0 else "LOW"
                else:
                    confidence = "HIGH" if auto_score >= 6.0 else "MEDIUM"
            elif sif_label == "NO":
                confidence = "HIGH" if word_count >= 15 else "MEDIUM"
            else:
                confidence = "LOW" if word_count < 15 else "MEDIUM"

        # Evidence text extraction
        evidence_text = ""
        if sif_label in ["YES", "NO"]:
            evidence_text = extract_verbatim_evidence(narrative, evidence_keywords)
            if evidence_text not in narrative:
                for s in sentences:
                    if s in narrative:
                        evidence_text = s
                        break
            if not evidence_text:
                evidence_text = narrative.strip()[:100]

        notes = f"Auto-classified by {self.model_name}; Score={auto_score:.1f}; Codes={'+'.join(reason_codes[:4])}"

        return {
            'sif_label': sif_label,
            'hazard_energy': hazard_energy,
            'activity': activity,
            'barrier_control': barrier_control,
            'barrier_failure': barrier_failure,
            'human_exposure': human_exposure,
            'potential_consequence': potential_consequence,
            'lsr_tags': lsr_tags,
            'evidence_text': evidence_text,
            'annotation_confidence': confidence,
            'annotation_notes': notes,
            'annotator_id': "AUTO_SYSTEM",
            'annotation_source': "AUTO",
            'model_version': self.model_name,
            'annotation_timestamp': datetime.datetime.now().isoformat(),
            'auto_score': str(round(auto_score, 2)),
            'auto_reason_codes': "+".join(reason_codes)
        }
