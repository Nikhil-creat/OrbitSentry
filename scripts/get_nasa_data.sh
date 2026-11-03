#!/usr/bin/env bash
# Telemanom SMAP/MSL data (links from the khundman/telemanom README; verify if a download fails). Best run on Colab/laptop.
set -e
mkdir -p data && cd data
curl -fLO https://s3-us-west-2.amazonaws.com/telemanom/data.zip
unzip -q data.zip && rm data.zip
curl -fLO https://raw.githubusercontent.com/khundman/telemanom/master/labeled_anomalies.csv
echo "Done: data/train, data/test, data/labeled_anomalies.csv"
