#!/usr/bin/env bash
EXP_DIR=$1
EXP_NAME=$2
DATA_ROOT=$3
IVEC_EXTRACTOR=$4

python balls/scripts/model_building/build_output_enhanced_lstm.py \
    --wordlist=$DATA_ROOT/wordlist.txt \
    --ivec-size=50 \
    --unk="<unk>" \
    --emsize=20 \
    --nhid=20 \
    --save=$EXP_DIR/$EXP_NAME.init.lm || exit 1

# 2b) train and test SMM-LSTM with partial i-vectors
python balls/scripts/train/train-ivecs-partial.py \
    --train-list=$DATA_ROOT/valid-list.txt \
    --valid-list=$DATA_ROOT/test-list.txt \
    --ivec-extractor=$IVEC_EXTRACTOR \
    --concat-articles \
    --cuda \
    --load=$EXP_DIR/$EXP_NAME.init.lm \
    --save=$EXP_DIR/$EXP_NAME-partial.lm \
    --epochs=1 || exit 1

python balls/scripts/eval/eval-ivecs-partial.py \
    --file-list=$DATA_ROOT/valid-list.txt \
    --ivec-extractor=$IVEC_EXTRACTOR \
    --concat-articles \
    --cuda \
    --load=$EXP_DIR/$EXP_NAME-partial.lm  || exit 1

# 2c) train and test SMM-LSTM with oracle i-vectors
python balls/scripts/train/train-ivecs-oracle.py \
    --train-list=$DATA_ROOT/valid-list.txt \
    --valid-list=$DATA_ROOT/test-list.txt \
    --ivec-extractor=$IVEC_EXTRACTOR \
    --concat-articles \
    --cuda \
    --load=$EXP_DIR/$EXP_NAME.init.lm \
    --save=$EXP_DIR/$EXP_NAME-oracle.lm \
    --epochs=1 || exit 1

python balls/scripts/eval/eval-ivecs-oracle.py \
    --file-list=$DATA_ROOT/valid-list.txt \
    --ivec-extractor=$IVEC_EXTRACTOR \
    --concat-articles \
    --cuda \
    --load=$EXP_DIR/$EXP_NAME-oracle.lm  || exit 1

python balls/scripts/eval/eval-ivecs-domain-adaptation.py \
    --file-list=$DATA_ROOT/valid-list.txt \
    --ivec-extractor=$IVEC_EXTRACTOR \
    --concat-articles \
    --domain-portion=0.25 \
    --cuda \
    --load=$EXP_DIR/$EXP_NAME-oracle.lm  || exit 1