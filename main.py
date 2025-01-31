#! /user/bin/evn python
# -*- coding:utf8 -*-

"""
main
======
A class for something.
@author: Guoxiu He
@contact: gxhe@fem.ecnu.edu.cn
@site: https://scholar.google.com/citations?user=2NVhxpAAAAAJ
@time: 18:11, 2021/11/26
@copyright: "Copyright (c) 2021 Guoxiu He. All Rights Reserved"
"""

import os
import sys
import argparse
import datetime
from Data_Loader import Data_Loader
from Shallow.SVM import SVM
from Shallow.AdaBoost import AdaBoost
from Shallow.Gaussian_Naive_Bayes import Gaussian_Naive_Bayes
from Shallow.GBDT import GBDT
from Shallow.Logistic_Regression import Logistic_Regression
from Shallow.Random_Forest import Random_Forest
from Deep.Base_Model import Base_Model
from Deep.TextCNN import TextCNN
import json
import numpy as np
import torch
from torchsummary import summary

ml_model_dict = {
    'svm': SVM,
    'adaboost': AdaBoost,
    'gnb': Gaussian_Naive_Bayes,
    'gbdt': GBDT,
    'lr': Logistic_Regression,
    'rf': Random_Forest,
}

dl_model_dict = {
    'mlp': Base_Model,
    'textcnn': TextCNN
}


def main_ml(config):
    data_name = config['data_name']  # 'aapr'
    model_name = config['model_name']  # 'svm'
    folds = config['folds']  # 10
    feature = config['feature']  # 'tf'
    clear = config['clear']
    clean = config['clean']
    metrics_num = config['metrics_num']

    data_loader = Data_Loader()

    score_list = []
    name_list = None
    for fold in range(folds):
        x_train, y_train = data_loader.data_load(fold=fold, phase='train', **config)
        model = ml_model_dict[model_name](metrics_num=metrics_num)
        model.build()

        model.train(x_train, y_train)
        model_path = "{}{}/{}.{}.{}".format(data_loader.exp_root, data_name, model_name, feature, fold)
        model.save_model(model_path)

        model.evaluate(x_train, y_train, phase='train')

        x_val, y_val = data_loader.data_load(data_name=data_name, phase='val', fold=fold, feature=feature)
        x_test, y_test = data_loader.data_load(data_name=data_name, phase='test', fold=fold, feature=feature)

        model.evaluate(x_val, y_val, phase='val')
        sorted_cal_res = model.evaluate(x_test, y_test, phase='test')
        name_list = [name_score[0][1:] for name_score in sorted_cal_res]
        fold_score_list = [name_score[1] for name_score in sorted_cal_res]
        score_list.append(fold_score_list)
    score_mean = np.mean(score_list, axis=0)
    score_std = np.std(score_list, axis=0)
    mean_std_list = ['{:.2f}+_{:.2f}'.format(mean, std) for mean, std in zip(score_mean, score_std)]
    print('-' * 20)
    print("\t".join(name_list))
    print("\t".join(mean_std_list))


def main_dl(config):
    data_name = config['data_name']

    folds = config['folds']  # 10
    clean = config['clean']  # 10
    cover_rate = config['cover_rate']
    min_count = config['min_count']
    input_shape = tuple(config['input_shape'])

    data_loader = Data_Loader()

    for fold in range(folds):
        print("This is the {} cross fold.".format(fold))
        word_dict_path = "{}{}/dl/vocab/vocab.cover{}.min{}.{}.json"\
            .format(data_loader.exp_root, data_name, cover_rate, min_count, fold)
        with open(word_dict_path, 'r') as fp:
            word_dict = json.load(fp)
            print("Load word dict from {}.".format(word_dict_path))
        if clean:
            mode = '_'.join(['clean'])
            input_path = '{}{}/{}/{}_{}_{}.input'.format(data_loader.data_root, data_name, fold, 'train', mode, fold)
            input_path_val = '{}{}/{}/{}_{}_{}.input'.format(data_loader.data_root, data_name, fold, 'val', mode, fold)
            input_path_test = '{}{}/{}/{}_{}_{}.input'.format(data_loader.data_root, data_name, fold, 'test', mode, fold)
        else:
            input_path = '{}{}/{}/{}_{}.input'.format(data_loader.data_root, data_name, fold, 'train', fold)
            input_path_val = '{}{}/{}/{}_{}.input'.format(data_loader.data_root, data_name, fold, 'val', fold)
            input_path_test = '{}{}/{}/{}_{}.input'.format(data_loader.data_root, data_name, fold, 'test', fold)
        output_path = '{}{}/{}/{}_{}.output'.format(data_loader.data_root, data_name, fold, 'train', fold)
        output_path_val = '{}{}/{}/{}_{}.output'.format(data_loader.data_root, data_name, fold, 'val', fold)
        output_path_test = '{}{}/{}/{}_{}.output'.format(data_loader.data_root, data_name, fold, 'test', fold)
        save_folder = '{}{}/dl/{}/'.format(data_loader.exp_root, data_name, model_name)
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)
        save_fold_folder = '{}{}/dl/{}/{}/'.format(data_loader.exp_root, data_name, model_name, fold)
        if not os.path.exists(save_fold_folder):
            os.mkdir(save_fold_folder)
        vocab_size = len(word_dict)
        model = dl_model_dict[model_name](vocab_size=vocab_size, **config)
        # summary(model, input_shape)
        print(model)
        model.train_model(model, data_loader.data_generator, input_path, output_path, word_dict,
                          input_path_val=input_path_val, output_path_val=output_path_val,
                          input_path_test=input_path_test, output_path_test=output_path_test,
                          save_folder=save_fold_folder)


if __name__ == '__main__':
    start_time = datetime.datetime.now()
    parser = argparse.ArgumentParser(description='Process some description.')
    parser.add_argument('--phase', default='test', help='the function name.')

    args = parser.parse_args()
    data_name = args.phase.strip().split('.')[0]
    model_cate = args.phase.strip().split('.')[1]
    config_path = './config/{}/{}/{}.json'.format(data_name, model_cate, args.phase)
    if not os.path.exists(config_path):
        raise RuntimeError("There is no {} config.".format(args.phase))
    config = json.load(open(config_path, 'r'))
    print('config: ', config)

    model_name = config['model_name']
    if model_name in ml_model_dict:
        main_ml(config)
    elif model_name in dl_model_dict:
        main_dl(config)
    else:
        raise RuntimeError("There is no model name.".format(model_name))

    end_time = datetime.datetime.now()
    print('{} takes {} seconds.'.format(args.phase, (end_time - start_time).seconds))
    print('Done main!')
