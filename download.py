import requests
import tempfile
from os.path import join, exists
import shutil
import glob
import zipfile
import json
from ovos_utils.bracket_expansion import expand_options


def download():
    # download the skills appstore cache from ovos plugin manager
    urls = {
        "MycroftMarketplace": "https://github.com/OpenVoiceOS/ovos_skill_manager/raw/master/ovos_skills_manager/res/MycroftMarketplace.jsondb",
        "Neon": "https://github.com/OpenVoiceOS/ovos_skill_manager/raw/master/ovos_skills_manager/res/Neon.jsondb",
        "Pling": "https://github.com/OpenVoiceOS/ovos_skill_manager/raw/master/ovos_skills_manager/res/Pling.jsondb",
        "OVOS": "https://github.com/OpenVoiceOS/ovos_skill_manager/raw/master/ovos_skills_manager/res/OVOS.jsondb",
        #"AndloSkillList": "https://github.com/OpenVoiceOS/ovos_skill_manager/blob/master/ovos_skills_manager/res/AndloSkillList.jsondb"
    }
    intents = {}
    entities = {}
    keywords = {}
    for skillstore, url in urls.items():
        # download the skills appstore cache from ovos plugin manager
        print(skillstore, url)
        skills = requests.get(url).json()[skillstore]
        for skill in skills:
            print(skill)
            # download the skill to tmp dir
            folder = skill["url"].strip("/").split("/")[-1]
            src = join(tempfile.gettempdir(), folder + ".zip")
            dst = join(tempfile.gettempdir(), folder)
            if not exists(src):
                source = requests.get(skill["url"] + "/archive/refs/heads/master.zip").content
                with open(src, "wb") as f:
                    f.write(source)
            # unzip
            try:
                with zipfile.ZipFile(src, 'r') as zip_ref:
                    zip_ref.extractall(dst)
            except:
                shutil.rmtree(src, ignore_errors=True)
                continue

            # parse
            for path in glob.glob(f'{dst}/*/*/*/*.intent'):
                name = f'{folder}.{path.split("/")[-1]}'.replace("skill-", "").replace(".intent", "")
                lang = path.split("/")[-2].lower()[-5:]
                with open(path) as f:
                    samples = f.read().split("\n")
                    samples = [s for s in samples if s and not s.startswith("#")]
                if lang not in intents:
                    intents[lang] = {}
                intents[lang][name] = samples
                print(lang, "intent:", name, intents[lang][name])
            for path in glob.glob(f'{dst}/*/*/*/*.entity'):
                name = f'{folder}.{path.split("/")[-1]}'.replace("skill-", "").replace(".entity", "")
                lang = path.split("/")[-2].lower()[-5:]
                with open(path) as f:
                    samples = f.read().split("\n")
                    samples = [s for s in samples if s and not s.startswith("#")]
                if lang not in entities:
                    entities[lang] = {}
                entities[lang][name] = samples
                print(lang, "entity:", name, entities[lang][name])
            for path in glob.glob(f'{dst}/*/*/*/*.voc'):
                name = f'{folder}.{path.split("/")[-1]}'.replace("skill-", "").replace(".voc", "")
                lang = path.split("/")[-2].lower()[-5:]
                with open(path) as f:
                    samples = f.read().split("\n")
                    samples = [s for s in samples if s and not s.startswith("#")]
                if lang not in keywords:
                    keywords[lang] = {}
                keywords[lang][name] = samples
                print(lang, "keyword:", name, keywords[lang][name])
            # delete
            shutil.rmtree(dst, ignore_errors=True)
            shutil.rmtree(src, ignore_errors=True)

    with open("mycroft_intents_raw_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=2, sort_keys=True)
    with open("mycroft_keywords_raw_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=2, sort_keys=True)
    with open("mycroft_entities_raw_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, sort_keys=True)
    return intents, entities, keywords


def load_dataset():
    if not exists("mycroft_intents_raw_v0.1.json"):
        intents, entities, keywords = download()
    else:
        with open("mycroft_intents_raw_v0.1.json", encoding="utf-8") as f:
            intents = json.load(f)
        with open("mycroft_keywords_raw_v0.1.json", encoding="utf-8") as f:
            keywords = json.load(f)
        with open("mycroft_entities_raw_v0.1.json", encoding="utf-8") as f:
            entities = json.load(f)
    return intents, entities, keywords


def normalize():
    if exists("mycroft_intents_expanded_v0.1.json"):
        with open("mycroft_intents_expanded_v0.1.json", encoding="utf-8") as f:
            intents = json.load(f)
        with open("mycroft_keywords_expanded_v0.1.json", encoding="utf-8") as f:
            keywords = json.load(f)
        with open("mycroft_entities_expanded_v0.1.json", encoding="utf-8") as f:
            entities = json.load(f)
        return intents, entities, keywords

    intents, entities, keywords = load_dataset()
    for lang, intent_samples in intents.items():
        for intent_name, samples in intent_samples.items():
            expanded = []
            for s in samples:
                expanded += expand_options(s)
            intents[lang][intent_name] = expanded
    for lang, intent_samples in entities.items():
        for intent_name, samples in intent_samples.items():
            expanded = []
            for s in samples:
                expanded += expand_options(s)
            entities[lang][intent_name] = expanded
    for lang, intent_samples in keywords.items():
        for intent_name, samples in intent_samples.items():
            expanded = []
            for s in samples:
                expanded += expand_options(s)
            keywords[lang][intent_name] = expanded

    with open("mycroft_intents_expanded_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=2, sort_keys=True)
    with open("mycroft_keywords_expanded_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=2, sort_keys=True)
    with open("mycroft_entities_expanded_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, sort_keys=True)

    return intents, entities, keywords


def dict2csv(dataset):
    csv = []
    for lang, entries in dataset.items():
        for label, samples in entries.items():
            csv += [f"{lang},{label},{s.replace(',', '')}" for s in samples]

    return "\n".join(csv)


def convert():
    intents, entities, keywords = load_dataset()
    with open("mycroft_intents_raw_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(intents))
    with open("mycroft_keywords_raw_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(keywords))
    with open("mycroft_entities_raw_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(entities))

    intents, entities, keywords = normalize()
    with open("mycroft_intents_expanded_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(intents))
    with open("mycroft_keywords_expanded_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(keywords))
    with open("mycroft_entities_expanded_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(entities))

#download()
#load_dataset()
#normalize()
convert()