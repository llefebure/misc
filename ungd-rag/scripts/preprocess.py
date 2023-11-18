from pathlib import Path
from typing import List

import pandas as pd
import regex as re
import typer
import yaml
from tqdm import tqdm
from yaml import SafeLoader

params = yaml.load(open("config.yaml"), Loader=SafeLoader)

tqdm.pandas()


def paragraph_tokenize(text: str) -> List[str]:
    """Simple paragraph tokenization"""
    return re.split(r"(?<=[\.\?]\s*)\n", text)


def _load_and_preprocess(metadata_filename: str, docs_path: str) -> pd.DataFrame:
    """Load and preprocess raw data files

    Args:
        metadata_filename: Filename of metadata excel sheet
        docs_path: Directory path of raw speech texts

    Returns:
        A dataframe with the records to be indexed
    """
    metadata = pd.read_excel(metadata_filename)
    metadata.columns = [
        "year",
        "session",
        "iso_code",
        "country",
        "speaker",
        "post",
        "drop",
    ]
    metadata.drop("drop", axis=1, inplace=True)
    docs = Path(docs_path)
    all_records = []
    for session in tqdm(
        docs.glob("Session*"), desc="Iterating over session data directories"
    ):
        for speech in session.glob("[A-Z]*"):
            name, _ = speech.parts[-1].split(".")
            country_code, session_num, year = name.split("_")
            all_records.append(
                {
                    "iso_code": country_code,
                    "session": int(session_num),
                    "year": int(year),
                    "text": speech.read_text(),
                }
            )
    all_records = pd.DataFrame(all_records)
    joined = pd.merge(metadata, all_records, on=["iso_code", "session", "year"])
    joined["paragraphs"] = joined.text.progress_apply(paragraph_tokenize)
    joined = (
        joined.drop("text", axis=1)
        .explode("paragraphs")
        .rename({"paragraphs": "text"}, axis=1)
    )
    return joined


def _save(df: pd.DataFrame, path: str) -> None:
    """Save processed file"""
    df.to_csv(path, index=False)


def main():
    """Index data for search

    Args:
        subset: Indicate whether to load a subset of the data for testing.
    """
    df = _load_and_preprocess(
        params["data"]["metadata_fn"], params["data"]["docs_path"]
    )
    # Save the "full" dataset (UNSC members) and a subset for testing
    _save(df[df.iso_code.isin(params["unsc_members"])], params["data"]["processed"])
    _save(
        df[(df.year == 2022) & (df.iso_code == "USA")],
        params["data"]["processed_subset"],
    )


if __name__ == "__main__":
    typer.run(main)
