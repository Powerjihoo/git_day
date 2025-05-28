#!/bin/bash

# .env 파일로부터 환경변수 불러오기
export $(egrep -v '^#' .env | xargs)

# 스크립트 실행
torchrun --nproc_per_node=$NPROC_PER_NODE finetune.py \
    --base_model "$BASE_MODEL" \
    --output_dir "$OUTPUT_DIR" \
    --vram_available "$VRAM_AVAILABLE" \
    --per_device_train_batch_size $PER_DEVICE_TRAIN_BATCH_SIZE \
    --gradient_accumulation_steps $GRADIENT_ACCUMULATION_STEPS \
    --num_epochs $NUM_EPOCHS \
    --learning_rate $LEARNING_RATE \
    --cutoff_len $CUTOFF_LEN \
    --warmup_steps $WARMUP_STEPS \
    --logging_steps $LOGGING_STEPS \
    --add_eos_token $ADD_EOS_TOKEN \
    --bf16 $BF16 \
    --save_steps $SAVE_STEPS \
    --eval_steps $EVAL_STEPS \
    --save_total_limit $SAVE_TOTAL_LIMIT \
    --data_path "$DATA_PATH"