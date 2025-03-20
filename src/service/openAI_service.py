from openai import OpenAI
from dotenv import load_dotenv
import os, json, re
import nltk
from nltk.tokenize import word_tokenize


load_dotenv()

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')

energy_esg_data = {
    # Environmental (E)
    "E_GHG_SCOPE1": "Direct greenhouse gas emissions from owned or controlled sources (tons CO2e).",
    "E_GHG_SCOPE2": "Indirect greenhouse gas emissions from purchased electricity, steam, heating, and cooling (tons CO2e).",
    "E_GHG_SCOPE3": "Indirect greenhouse gas emissions from upstream and downstream activities (tons CO2e).",
    "E_RENEWABLE_ENERGY_PERCENT": "Percentage of total energy generated or consumed from renewable sources.",
    "E_METHANE_EMISSIONS": "Methane emissions from oil and gas operations (tons or cubic meters).",
    "E_WATER_WITHDRAWAL": "Total water withdrawn for operations (cubic meters).",
    "E_WATER_DISCHARGE": "Total water discharged from operations (cubic meters).",
    "E_OIL_SPILLS": "Number and volume of oil spills.",
    "E_LAND_DISTURBANCE": "Area of land disturbed by operations (acres or hectares).",
    "E_WASTE_MANAGEMENT": "Amount of hazardous and non-hazardous waste generated and managed (tons).",
    "E_CARBON_CAPTURE": "Capacity and efficiency of carbon capture and storage/utilization projects.",
    "E_DECOMMISSIONING_LIABILITIES": "Estimated costs for decommissioning oil and gas wells, pipelines, and other infrastructure.",

    # Social (S)
    "S_WORKER_SAFETY_RATE": "Worker safety incident rate (e.g., Total Recordable Incident Rate - TRIR).",
    "S_COMMUNITY_ENGAGEMENT": "Investment in and engagement with local communities affected by operations.",
    "S_INDIGENOUS_RIGHTS": "Policies and practices related to respecting indigenous rights and land.",
    "S_LABOR_RIGHTS": "Adherence to labor rights and fair employment practices.",
    "S_SUPPLY_CHAIN_STANDARDS": "Standards and practices for ensuring ethical and sustainable supply chains.",
    "S_LOCAL_EMPLOYMENT": "Percentage of employees hired from local communities.",
    "S_HUMAN_RIGHTS_DUE_DILIGENCE": "Processes for identifying and addressing human rights risks.",
    "S_ENERGY_ACCESS": "Contributions to providing access to affordable and reliable energy.",
    "S_HEALTH_AND_SAFETY_TRAINING": "Hours of health and safety training provided to employees and contractors.",

    # Governance (G)
    "G_BOARD_DIVERSITY": "Diversity of the board of directors (e.g., gender, ethnicity, skills).",
    "G_EXECUTIVE_COMPENSATION": "Executive compensation tied to ESG performance.",
    "G_ESG_OVERSIGHT": "Board-level oversight of ESG risks and performance.",
    "G_RISK_MANAGEMENT": "Processes for identifying and managing ESG-related risks.",
    "G_ETHICS_PROGRAM": "Existence and effectiveness of an ethics and compliance program.",
    "G_LOBBYING_TRANSPARENCY": "Transparency in lobbying activities and political contributions.",
    "G_SHAREHOLDER_ENGAGEMENT": "Engagement with shareholders on ESG issues.",
    "G_CYBERSECURITY": "Measures taken to protect against cybersecurity threats.",
    "G_WHISTLEBLOWER_PROTECTION": "Policies and procedures for whistleblower protection."
}


openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)


def filter_esg_relevant_sentences(text, esg_data = energy_esg_data):
    """Filters sentences relevant to ESG metrics."""
    keywords = set()
    try:
        for description in esg_data.values():
            words = word_tokenize(description.lower())
            tagged_words = nltk.pos_tag(words)
            # keywords.update(word for word, pos in tagged_words if pos.startswith(('NN'))) 
            keywords.update(word for word, pos in tagged_words if pos.startswith(('NN', 'VB', 'JJ', 'RB'))) # keep nouns, verbs, adjectives, adverbs.
            # keywords.update(re.findall(r'\b\w+\b', description.lower()))
        print(f'keywords:{keywords}')
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        relevant_sentences = []
        for sentence in sentences:
            keyword_count = sum(1 for keyword in keywords if keyword in sentence.lower())
            if keyword_count > 2:
                relevant_sentences.append(sentence)
        # relevant_sentences = [sentence for sentence in sentences if any(keyword in sentence.lower() for keyword in keywords)]

        return " ".join(relevant_sentences)
    except Exception as e:
        print(f"An error occurred in filter_esg_relevant_sentences: {e}")
        raise e
        # return None


def extract_esg_values_openai(text, esg_data = energy_esg_data):
    print(f'Length of text before filter:{len(text)}')
    text = filter_esg_relevant_sentences(text)
    print(f'Length of text after filter:{len(text)}')
    prompt = f"""
    Extract the numerical values for the following ESG metrics from the text below. Return the results as a JSON object, where the keys are the metric names and the values are the corresponding numerical values. If a value is not found, set it to null.

    Text:
    {text}

    ESG Metrics:
    {json.dumps(esg_data, indent=2)}

    JSON Output:
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-4"  ??? gpt-4-32k-0613 ??? gpt-3.5-turbo 19385 tokens is maximun for potentially better results
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # Lower temperature for more consistent results
        )
        extracted_values = json.loads(response.choices[0].message.content)
        return extracted_values

    except Exception as e:
        print(f"An error occurred: {e}")
        raise e
        # return None