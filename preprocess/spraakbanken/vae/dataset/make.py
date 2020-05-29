import pickle 
import librosa 
import sys
import glob 
import random
import os
from collections import defaultdict
import re
import numpy as np
import json
from tacotron.utils import get_spectrograms

#TODO Rewrite to work with Spraakbanken format
def read_speaker_info(speaker_info_path):
    '''
    Reads all lines of a text-file. Each line is regarded as a path to a speaker audio file.
    Each speaker file path is expected to have the speaker id in the beginning of the path.

    :param speaker_info_path:   Path to the text file containing the lines of speaker audio file paths.
    returns a collection of speaker ids
    '''
    speaker_ids = []
    with open(speaker_info_path, 'r') as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            speaker_id = line.strip().split()[0]
            speaker_ids.append(speaker_id)
    return speaker_ids

def read_filenames(root_dir):
    '''
    Creates a map with speaker ids as keys and a collection with the speaker's audio files.
    
    :param root_dir:   The root dir of the speaker corpus 

    returns a dictionary with speaker ids mapped to a collection of speaker audio files
    '''
    speaker2filenames = defaultdict(lambda : [])
    for path in sorted(glob.glob(os.path.join(root_dir, '*/*'))):
        filename = path.strip().split('/')[-1]
        rematch = re.match(r'p(\d+)_(\d+)\.wav', filename)
        if rematch is not None:
            speaker_id, utt_id = rematch.groups()
            speaker2filenames[speaker_id].append(path)
    return speaker2filenames

def wave_feature_extraction(wav_file, sr):
    '''
    Trims leading and trailing silence of the given audio file.
    Silence is defined as a sound level below 20 decibel.

    :param wav_file:    The wav_file to trim for silence
    :param sr:          The sampling rate to use when loading the audio file

    returns the trimmed audio signal
    '''
    y, sr = librosa.load(wav_file, sr)
    y, _ = librosa.effects.trim(y, top_db=20)
    return y

def spec_feature_extraction(wav_file):
    '''
    Extracts the mel and magnitude spectrogram from the given audio file

    :param wav_file:    The audio file to extract spectrogram from

    returns the mel and magnitude spectrogram of the given audio file
    '''
    mel, mag = get_spectrograms(wav_file)
    return mel, mag

if __name__ == '__main__':
    data_dir = sys.argv[1]
    source_speaker_paths = sys.argv[2]
    target_speaker_paths = sys.argv[3]
    output_dir = sys.argv[3]
    test_speakers = int(sys.argv[4])
    test_proportion = float(sys.argv[5])
    sample_rate = int(sys.argv[6])
    n_utts_attr = int(sys.argv[7])

    #Pick target speaker ids
    target_ids = read_speaker_info(target_speaker_paths)

    #Train test split 
    source_ids = read_speaker_info(source_speaker_paths)
    random.shuffle(speaker_ids)

    train_speaker_ids = speaker_ids[:-test_speakers]
    test_speaker_ids = speaker_ids[-test_speakers:]

    speaker2filenames = read_filenames(data_dir)

    #Speaker file extraction
    train_path_list, in_test_path_list, out_test_path_list = [], [], []

    #Randomly shuffling audio files for each speaker and extracting test and training data
    for speaker in train_speaker_ids:
        path_list = speaker2filenames[speaker]
        random.shuffle(path_list)
        test_data_size = int(len(path_list) * test_proportion)
        train_path_list += path_list[:-test_data_size]
        in_test_path_list += path_list[-test_data_size:]

    #Source test speakers
    with open(os.path.join(output_dir, 'in_test_files.txt'), 'w') as f:
        for path in in_test_path_list:
            f.write(f'{path}\n')

    #Target speakers
    for speaker in test_speaker_ids:
        path_list = speaker2filenames[speaker]
        out_test_path_list += path_list

    with open(os.path.join(output_dir, 'out_test_files.txt'), 'w') as f:
        for path in out_test_path_list:
            f.write(f'{path}\n')

    #Feature extraction, mean and variance vectors, saved as pickle
    for dset, path_list in zip(['train', 'in_test', 'out_test'], \
            [train_path_list, in_test_path_list, out_test_path_list]):
        print(f'processing {dset} set, {len(path_list)} files')
        data = {}
        output_path = os.path.join(output_dir, f'{dset}.pkl')
        all_train_data = []
        for i, path in enumerate(sorted(path_list)):
            if i % 500 == 0 or i == len(path_list) - 1:
                print(f'processing {i} files')
            filename = path.strip().split('/')[-1]
            mel, mag = spec_feature_extraction(path)
            data[filename] = mel
            if dset == 'train' and i < n_utts_attr:
                all_train_data.append(mel)
        #Extrating mean and standard deviation for training data and saves it in .pkl
        if dset == 'train':
            all_train_data = np.concatenate(all_train_data)
            mean = np.mean(all_train_data, axis=0)
            std = np.std(all_train_data, axis=0)
            attr = {'mean': mean, 'std': std}
            with open(os.path.join(output_dir, 'attr.pkl'), 'wb') as f:
                pickle.dump(attr, f)
        #Normalizing mel spectrogram data
        for key, val in data.items():
            val = (val - mean) / std
            data[key] = val
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
