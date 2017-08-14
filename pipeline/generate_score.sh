#!/bin/bash
cd ../model

for filename in ../pipeline/csv_file/*.csv; 
    do
        python model_pipeline.py --save True --test_data $filename;
    done
