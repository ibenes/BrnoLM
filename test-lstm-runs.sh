#!/usr/bin/env bash
EXP_DIR=$1
EXP_NAME=$2
DATA_ROOT=$3

python balls/model_building/build_lstm.py \
    --wordlist=$DATA_ROOT/wordlist.txt \
    --unk="<unk>" \
    --emsize=20 \
    --nhid=20 \
    --save=$EXP_DIR/$EXP_NAME.init.lm || exit 1


# 1) train and test in the traditional setup
python balls/train.py \
    --train=$DATA_ROOT/pythlm-symlinks-no-train/train.txt \
    --valid=$DATA_ROOT/pythlm-symlinks-no-train/valid.txt \
    --cuda \
    --epochs=1 \
    --load=$EXP_DIR/$EXP_NAME.init.lm \
    --save=$EXP_DIR/$EXP_NAME.lm || exit 1

python balls/eval.py \
    --data=$DATA_ROOT/wiki.test.tokens \
    --cuda \
    --load=$EXP_DIR/$EXP_NAME.lm || exit 1


# 2) train and test using multifile setup
python balls/train-multifile.py \
    --train-list=$DATA_ROOT/valid-list.txt \
    --valid-list=$DATA_ROOT/test-list.txt \
    --cuda \
    --epochs=1 \
    --load=$EXP_DIR/$EXP_NAME.init.lm \
    --save=$EXP_DIR/$EXP_NAME-mf.lm || exit 1

python balls/eval-multifile.py \
    --file-list=$DATA_ROOT/test-list.txt \
    --cuda \
    --load=$EXP_DIR/$EXP_NAME-mf.lm || exit 1
