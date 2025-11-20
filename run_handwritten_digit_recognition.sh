#!/bin/bash

# Launch Planning Pipeline Script for Handwritten Digit Recognition
# 手写数字识别任务规划、文献调研和双审稿人评审流程

python3 launch_planning.py \
  --text-input "vision transformer 网络结构的学习和搭建，不包括训练" \
  --max_rounds 3 \
  --max_papers 80 \
  --non_interactive \
  --verbose \
  --enable_judger \
  --min_acceptable_score 8.0 \
  --enable_review \
  --max_revision_rounds 2 \
  --min_clarity_score 7.5 \
  --min_coherence_score 7.5 \
  --target_audience "beginners" 




