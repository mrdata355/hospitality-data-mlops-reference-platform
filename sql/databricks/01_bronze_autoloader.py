# Databricks notebook source
from __future__ import annotations

import argparse
import os

from pyspark.sql import functions as F

parser = argparse.ArgumentParser()
parser.add_argument(
    "--catalog", default=os.getenv("PLATFORM_CATALOG", "hospitality_data_platform_dev")
)
parser.add_argument("--domain", default="reservations")
args = parser.parse_args()

catalog = args.catalog
domain = args.domain
source = f"/Volumes/{catalog}/bronze/landing/{domain}"
checkpoint = f"/Volumes/{catalog}/ops/checkpoints/{domain}"
schema_location = f"/Volumes/{catalog}/ops/schemas/{domain}"
target = f"{catalog}.bronze.{domain}_raw"

query = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", schema_location)
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    .load(source)
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.input_file_name())
    .withColumn("_batch_date", F.current_date())
    .writeStream.option("checkpointLocation", checkpoint)
    .trigger(availableNow=True)
    .toTable(target)
)
query.awaitTermination()
