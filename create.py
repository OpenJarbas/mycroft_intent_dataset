import requests
import tempfile
from os.path import join, exists
import os
import shutil
import glob
import zipfile
import json
from ovos_utils.bracket_expansion import expand_options


def download():
    os.makedirs("json", exist_ok=True)
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
    dialogs = {}
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
            for path in glob.glob(f'{dst}/*/*/*/*.dialog'):
                name = f'{folder}.{path.split("/")[-1]}'.replace("skill-", "").replace(".dialog", "")
                lang = path.split("/")[-2].lower()[-5:]
                with open(path) as f:
                    samples = f.read().split("\n")
                    samples = [s for s in samples if s and not s.startswith("#")]
                if lang not in dialogs:
                    dialogs[lang] = {}
                dialogs[lang][name] = samples
                print(lang, "dialog:", name, dialogs[lang][name])
            # delete
            shutil.rmtree(dst, ignore_errors=True)
            shutil.rmtree(src, ignore_errors=True)

    with open("json/mycroft_intents_raw_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=2, sort_keys=True)
    with open("json/mycroft_keywords_raw_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=2, sort_keys=True)
    with open("json/mycroft_entities_raw_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, sort_keys=True)
    with open("json/mycroft_dialogs_raw_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(dialogs, f, indent=2, sort_keys=True)
    return intents, entities, keywords, dialogs


def load_dataset():
    if not exists("json/mycroft_intents_raw_v0.1.json"):
        intents, entities, keywords, dialogs = download()
    else:
        with open("json/mycroft_intents_raw_v0.1.json", encoding="utf-8") as f:
            intents = json.load(f)
        with open("json/mycroft_keywords_raw_v0.1.json", encoding="utf-8") as f:
            keywords = json.load(f)
        with open("json/mycroft_entities_raw_v0.1.json", encoding="utf-8") as f:
            entities = json.load(f)
        with open("json/mycroft_dialogs_raw_v0.1.json", encoding="utf-8") as f:
            dialogs = json.load(f)
    return intents, entities, keywords, dialogs


def normalize():
    os.makedirs("json", exist_ok=True)
    intents, entities, keywords, dialogs = load_dataset()
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
    for lang, intent_samples in dialogs.items():
        for intent_name, samples in intent_samples.items():
            expanded = []
            for s in samples:
                expanded += expand_options(s)
            dialogs[lang][intent_name] = expanded

    with open("json/mycroft_intents_expanded_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=2, sort_keys=True)
    with open("json/mycroft_keywords_expanded_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=2, sort_keys=True)
    with open("json/mycroft_entities_expanded_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, sort_keys=True)
    with open("json/mycroft_dialogs_expanded_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(dialogs, f, indent=2, sort_keys=True)

    return intents, entities, keywords, dialogs


def dict2csv(dataset):
    csv = []
    for lang, entries in dataset.items():
        for label, samples in entries.items():
            csv += [f"{lang},{label},{s.replace(',', '')}" for s in samples]

    return "\n".join(csv)


def convert():
    os.makedirs("csv", exist_ok=True)
    intents, entities, keywords, dialogs = load_dataset()
    with open("csv/mycroft_intents_raw_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(intents))
    with open("csv/mycroft_keywords_raw_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(keywords))
    with open("csv/mycroft_entities_raw_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(entities))
    with open("csv/mycroft_dialogs_raw_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(dialogs))

    intents, entities, keywords, dialogs = normalize()
    with open("csv/mycroft_intents_expanded_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(intents))
    with open("csv/mycroft_keywords_expanded_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(keywords))
    with open("csv/mycroft_entities_expanded_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(entities))
    with open("csv/mycroft_dialogs_expanded_v0.1.csv", "w", encoding="utf-8") as f:
        f.write(dict2csv(dialogs))


def filter_per_lang(dataset, name):
    for lang, entries in dataset.items():
        os.makedirs(f"csv/lang/{lang}", exist_ok=True)
        os.makedirs(f"json/lang/{lang}", exist_ok=True)
        subset = {lang: entries}
        with open(f"csv/lang/{lang}/{name}.{lang}.csv", "w", encoding="utf-8") as f:
            f.write(dict2csv(subset))
        with open(f"json/lang/{lang}/{name}.{lang}.json", "w", encoding="utf-8") as f:
            json.dump(subset, f, indent=2, sort_keys=True)


def split_datasets():
    intents, entities, keywords, dialogs = load_dataset()
    filter_per_lang(intents, "mycroft_intents_raw_v0.1")
    filter_per_lang(keywords, "mycroft_keywords_raw_v0.1")
    filter_per_lang(entities, "mycroft_entities_raw_v0.1")
    filter_per_lang(dialogs, "mycroft_dialogs_raw_v0.1")
    intents, entities, keywords, dialogs = normalize()
    filter_per_lang(intents, "mycroft_intents_expanded_v0.1")
    filter_per_lang(keywords, "mycroft_keywords_expanded_v0.1")
    filter_per_lang(entities, "mycroft_entities_expanded_v0.1")
    filter_per_lang(dialogs, "mycroft_dialogs_expanded_v0.1")


download()
#load_dataset()
#normalize()
convert()

split_datasets()
