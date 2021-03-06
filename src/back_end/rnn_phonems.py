import scipy.io.wavfile as wav
import data
from train_RNN import reshape_data
import numpy as np
from python_speech_features import mfcc, base
from keras.models import load_model


def low_pass_data(result_phonemes, fs, coef=4, step_size=0.01):
    i = 1
    while i < len(result_phonemes) - 1:
        if (result_phonemes[i + 1][0] - result_phonemes[i][0]) < coef * step_size * fs:
            del result_phonemes[i]
            while (i != len(result_phonemes) - 1) and result_phonemes[i][1] == result_phonemes[i - 1][1]:
                del result_phonemes[i]
        else:
            i = i + 1
    return result_phonemes


def rnn_phonemes():
    window_size = 0.02  # length of window in seconds
    step_size = 0.01  # step of succesive windows in seconds
    numcep = 13  # number of cepstrum to return (paper uses 40, default is 13)
    nfft = 512  # FFT size

    data_rnn = data.LipSyncData.get_instance()
    x = data_rnn.rnn_audio
    fs = data_rnn.fs

    # (fs, x) = wav.read('../data/SA1RIFF.WAV')
    # import pdb; pdb.set_trace()

    mfcc_feat = mfcc(x, fs, winlen=window_size, winstep=step_size, numcep=numcep, nfft=nfft, appendEnergy=True)
    mfcc_delta = base.delta(mfcc_feat, 2)
    mfcc_delta_delta = base.delta(mfcc_delta, 2)
    all_data = np.hstack([mfcc_feat, mfcc_delta, mfcc_delta_delta])
    center_of_win = (np.arange(len(all_data)) + 1) * fs * 0.01  # returns position of the center of the window

    timesteps = 4

    data_reshaped = reshape_data(all_data, timesteps)

    model = load_model('../data/saved_rnn/model_17_0.8750.hdf5')

    classes = model.predict(data_reshaped, batch_size=100)

    result_phonemes = []
    first = True
    for i, win_class in enumerate(classes):
        if first:
            result_phonemes.append((int(i * step_size * fs), data.Phonemes(win_class.argmax() + 1)))
            first = False
        elif data.Phonemes(win_class.argmax()+1) is not result_phonemes[len(result_phonemes)-1][1]:
            result_phonemes.append((int(i*step_size*fs), data.Phonemes(win_class.argmax()+1)))

    for i in range(1, 7):
        result_phonemes = low_pass_data(result_phonemes, fs, i)

    # import pdb; pdb.set_trace()

    data_rnn.dat = result_phonemes


if __name__ == '__main__':
    rnn_phonemes()
