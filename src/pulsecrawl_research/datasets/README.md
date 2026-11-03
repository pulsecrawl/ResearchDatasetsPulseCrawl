# Versioned dataset studies

`experiments.py` contains the publication, replay, query, compaction, and
interruption workloads used to evaluate versioned structured datasets. These
studies generate known rows and expected versions, then compare retained output
with those expectations.

Dataset-producing retained runs publish a readable CSV and a checksum-linked
Parquet file under their `readable-output/` folder. Generated storage inputs
are documented under [`datasets/storage/`](../../../datasets/storage/).
