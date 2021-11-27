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
import json

ml_model_dict = {
    'svm': SVM
}


def main_ml(config):
    data_name = config['data_name']  # 'aapr'
    model_name = config['model_name']  # 'svm'
    folds = config['folds']  # 10
    feature = config['feature']  # 'tf'
    clear = config['clear']

    data_loader = Data_Loader()
    for fold in range(folds):
        x_train, y_train = data_loader.data_load(data_name=data_name, phase='train', fold=fold, feature=feature, clear=clear)
        model = ml_model_dict[model_name]()
        model.build()

        model.train(x_train, y_train)
        model_path = "{}{}/{}.{}.{}".format(data_loader.exp_root, data_name, model_name, feature, fold)
        model.save_model(model_path)

        model.evaluate(x_train, y_train, phase='train')

        x_val, y_val = data_loader.data_load(data_name=data_name, phase='val', fold=fold, feature=feature)
        x_test, y_test = data_loader.data_load(data_name=data_name, phase='test', fold=fold, feature=feature)

        model.evaluate(x_val, y_val, phase='val')
        model.evaluate(x_test, y_test, phase='test')


if __name__ == '__main__':
    start_time = datetime.datetime.now()
    parser = argparse.ArgumentParser(description='Process some description.')
    parser.add_argument('--phase', default='test', help='the function name.')

    args = parser.parse_args()
    config_path = './config/{}.json'.format(args.phase)
    if not os.path.exists(config_path):
        raise RuntimeError("There is no {} config.".format(args.phase))
    config = json.load(open(config_path, 'r'))
    print(config)

    model_name = config['model_name']
    if model_name in ml_model_dict:
        main_ml(config)
    else:
        raise RuntimeError("There is no model name.".format(model_name))

    end_time = datetime.datetime.now()
    print('{} takes {} seconds.'.format(args.phase, (end_time - start_time).seconds))
    print('Done main!')
