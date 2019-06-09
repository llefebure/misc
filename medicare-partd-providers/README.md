Medicare Part D Provider Data
=============================

In [this blog post](https://roamanalytics.com/2016/09/13/prescription-based-prediction/) from Roam Analytics, the authors dig into data on care providers and their record of prescriptions issued under Medicare Part D. Inspired by this, I investigate to what extent a care provider's prescribing behavior is predictive of their specialty.

Prescribing decisions appear to be a product of a far more nuanced decision making process than I had thought as someone without a background in this area which makes for an interesting ML problem. [This paper](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5499356/) lays out some of the models and theories of how decisions are made. Additionally, the Roam Analytics team summarizes their motivation nicely as follows:

> We expect a doctor's prescribing behavior to be governed by many complex, interacting factors related to her specialty, the place she works, her personal preferences, and so forth. How much of this information is hidden away in the Medicare Part D database?

# Data

The Medicare Part D data is publically available from https://data.cms.gov/. In this analysis, however, I use a preprocessed version curated by Roam Analytics and hosted [here](https://www.kaggle.com/roamresearch/prescriptionbasedprediction) on Kaggle. If you're trying to reproduce my analysis, that JSONL file should be downloaded into `data/`.

# Analysis

See the following for more details on the analysis:
1. https://llefebure.github.io/articles/2019-06/prescribing-behavior-part1
