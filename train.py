import argparse
import math
import torch

import data
import multistream
import split_corpus_dataset
import lstm_model
import vocab
import language_model

from runtime_multifile import evaluate_uniform_stream, train_uniform_stream

from loggers import ProgressLogger


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PyTorch RNN/LSTM Language Model')
    parser.add_argument('--train', type=str, required=True,
                        help='location of the train corpus')
    parser.add_argument('--valid', type=str, required=True,
                        help='location of the valid corpus')
    parser.add_argument('--lr', type=float, default=20,
                        help='initial learning rate')
    parser.add_argument('--beta', type=float, default=0,
                        help='L2 regularization penalty')
    parser.add_argument('--clip', type=float, default=0.25,
                        help='gradient clipping')
    parser.add_argument('--epochs', type=int, default=40,
                        help='upper epoch limit')
    parser.add_argument('--batch_size', type=int, default=20, metavar='N',
                        help='batch size')
    parser.add_argument('--bptt', type=int, default=35,
                        help='sequence length')
    parser.add_argument('--seed', type=int, default=1111,
                        help='random seed')
    parser.add_argument('--shuffle-lines', action='store_true',
                        help='shuffle lines before every epoch')
    parser.add_argument('--cuda', action='store_true',
                        help='use CUDA')
    parser.add_argument('--log-interval', type=int, default=200, metavar='N',
                        help='report interval')
    parser.add_argument('--load', type=str, required=True,
                        help='where to load a model from')
    parser.add_argument('--save', type=str,  required=True,
                        help='path to save the final model')
    args = parser.parse_args()
    print(args)

    # Set the random seed manually for reproducibility.
    torch.manual_seed(args.seed)
    if args.cuda and torch.cuda.is_available():
        torch.cuda.manual_seed(args.seed)

    print("loading model...")
    with open(args.load, 'rb') as f:
        lm = language_model.load(f)
    if args.cuda:
        lm.model.cuda()
    print(lm.model)

    print("preparing data...")
    train_ids = data.tokens_from_fn(args.train, lm.vocab, randomize=False)
    train_batched = multistream.batchify(train_ids, args.batch_size, args.cuda)
    train_data = split_corpus_dataset.TemporalSplits(train_batched, nb_inputs_necessary=1, nb_targets_parallel=args.bptt)

    valid_ids = data.tokens_from_fn(args.valid, lm.vocab, randomize=False)
    valid_batched = multistream.batchify(valid_ids, 10, args.cuda)
    valid_data = split_corpus_dataset.TemporalSplits(valid_batched, nb_inputs_necessary=1, nb_targets_parallel=args.bptt)

    print("training...")
    lr = args.lr
    best_val_loss = None

    for epoch in range(1, args.epochs+1):
        logger = ProgressLogger(epoch, args.log_interval, lr, len(train_batched)//args.bptt)
        optim = torch.optim.SGD(lm.model.parameters(), lr, weight_decay=args.beta)

        train_uniform_stream(
            lm.model, train_data, logger, 
            optim, args.clip
        )
        val_loss = evaluate_uniform_stream(lm.model, valid_data)
        print('-' * 89)
        print('| end of epoch {:3d} | time: {:5.2f}s | # updates: {} | valid loss {:5.2f} | '
                'valid ppl {:8.2f}'.format(epoch, logger.time_since_creation(), logger.nb_updates(),
                                           val_loss, math.exp(val_loss)))
        print('-' * 89)

        # Save the model if the validation loss is the best we've seen so far.
        if not best_val_loss or val_loss < best_val_loss:
            with open(args.save, 'wb') as f:
                lm.save(f)
            best_val_loss = val_loss
        else:
            lr /= 2.0
            pass
