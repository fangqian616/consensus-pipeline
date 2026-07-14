#!/bin/bash
cd "./project"
python3 -u test_full_pipeline.py > /tmp/test_output.log 2>&1
echo "DONE" >> /tmp/test_output.log