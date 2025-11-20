#!/bin/bash

# Launch Planning Pipeline Script
# 任务规划、文献调研和双审稿人评审流程

python launch_planning.py \
  --image Image/5c5061e3ef9efd41df20f3549563eed0.png \
  --max_rounds 2 \
  --max_papers 80 \
  --non_interactive \
  --verbose \
  --enable_judger \
  --min_acceptable_score 8.0 \
  --enable_review \
  --max_revision_rounds 5 \
  --min_clarity_score 7.5 \
  --min_coherence_score 7.5 \
  --target_audience "beginners"

