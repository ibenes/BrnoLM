import argparse
import math
import torch

import model
import lstm_model
import vocab
import language_model
import split_corpus_dataset
from hidden_state_reorganization import HiddenStateReorganizer

from runtime_utils import CudaStream, filelist_to_tokenized_splits
from runtime_multifile import evaluate

import numpy as np


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PyTorch RNN/LSTM Language Model')
    parser.add_argument('--file-list', type=str, required=True,
                        help='file with paths to training documents')
    parser.add_argument('--batch_size', type=int, default=20, metavar='N',
                        help='batch size')
    parser.add_argument('--bptt', type=int, default=35,
                        help='sequence length')
    parser.add_argument('--seed', type=int, default=1111,
                        help='random seed')
    parser.add_argument('--cuda', action='store_true',
                        help='use CUDA')
    parser.add_argument('--concat-articles', action='store_true',
                        help='pass hidden states over article boundaries')
    parser.add_argument('--load', type=str, required=True,
                        help='where to load a model from')
    args = parser.parse_args()
    print(args)

    torch.manual_seed(args.seed)
    if args.cuda and torch.cuda.is_available():
        torch.cuda.manual_seed(args.seed)

    print("loading model...")
    with open(args.load, 'rb') as f:
        lm = language_model.load(f)
    print(lm.model)

    ivec_eetor = lambda x: np.asarray([float(sum(x) % 1337 - 668)/1337]*2, dtype=np.float32)
    ivec_app_creator = lambda ts: split_corpus_dataset.CheatingIvecAppender(ts, ivec_eetor)

    print("preparing data...")
    tss = filelist_to_tokenized_splits(args.file_list, lm.vocab, args.bptt)
    data = split_corpus_dataset.BatchBuilder(tss, ivec_app_creator, args.batch_size,
                                               discard_h=not args.concat_articles)
    if args.cuda:
        data = CudaStream(data)

    loss = evaluate(lm, data, args.batch_size, args.cuda)
    print('loss {:5.2f} | ppl {:8.2f}'.format( loss, math.exp(loss)))
