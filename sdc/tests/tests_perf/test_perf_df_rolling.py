# -*- coding: utf-8 -*-
# *****************************************************************************
# Copyright (c) 2020, Intel Corporation All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *****************************************************************************
import string
import time

import numpy

from sdc.tests.test_utils import test_global_input_data_float64
from sdc.tests.tests_perf.data_generator import gen_df
from sdc.tests.tests_perf.test_perf_base import TestBase


rolling_usecase_tmpl = """
def df_rolling_{method_name}_usecase(data, {extra_usecase_params}):
    start_time = time.time()
    for i in range({ncalls}):
        res = data.rolling({rolling_params}).{method_name}({method_params})
    end_time = time.time()
    return end_time - start_time, res
"""


def get_rolling_params(window=100, min_periods=None):
    """Generate supported rolling parameters"""
    rolling_params = [f'{window}']
    if min_periods:
        rolling_params.append(f'min_periods={min_periods}')

    return ', '.join(rolling_params)


def gen_df_rolling_usecase(method_name, rolling_params=None,
                           extra_usecase_params='', method_params='', ncalls=1):
    """Generate df rolling method use case"""
    if not rolling_params:
        rolling_params = get_rolling_params()

    func_text = rolling_usecase_tmpl.format(**{
        'method_name': method_name,
        'extra_usecase_params': extra_usecase_params,
        'rolling_params': rolling_params,
        'method_params': method_params,
        'ncalls': ncalls
    })

    global_vars = {'np': numpy, 'time': time}
    loc_vars = {}
    exec(func_text, global_vars, loc_vars)
    _df_rolling_usecase = loc_vars[f'df_rolling_{method_name}_usecase']

    return _df_rolling_usecase


# python -m sdc.runtests sdc.tests.tests_perf.test_perf_df_rolling.TestDFRollingMethods
class TestDFRollingMethods(TestBase):
    # more than 19 columns raise SystemError: CPUDispatcher() returned a result with an error set
    max_columns_num = 19

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.map_ncalls_dlength = {
            'apply': (10, [10 ** 4]),
            'corr': (10, [8 * 10 ** 5]),
            'count': (10, [10 ** 6]),
            'cov': (10, [8 * 10 ** 5]),
            'kurt': (10, [4 * 10 ** 5]),
            'max': (10, [4 * 10 ** 5]),
            'mean': (10, [10 ** 6]),
            'median': (10, [10 ** 4]),
            'min': (10, [4 * 10 ** 5]),
            'quantile': (10, [4 * 10 ** 3]),
            'skew': (10, [2 * 10 ** 5]),
            'std': (10, [8 * 10 ** 5]),
            'sum': (10, [10 ** 6]),
            'var': (10, [8 * 10 ** 5]),
        }

    def _test_case(self, pyfunc, name, total_data_length,
                   input_data=test_global_input_data_float64,
                   columns_num=10, extra_data_num=0):
        """
        Test DataFrame.rolling method
        :param pyfunc: Python function to test which calls tested method inside
        :param name: name of the tested method, e.g. min
        :param total_data_length: length of generating test data
        :param input_data: initial data used for generating test data
        :param columns_num: number of columns in generated DataFrame
        :param extra_data_num: number of additionally generated DataFrames
        """
        if columns_num > self.max_columns_num:
            columns_num = self.max_columns_num

        for data_length in total_data_length:
            base = {
                'test_name': f'DataFrame.rolling.{name}',
                'data_size': data_length,
            }
            args = [gen_df(data_length, columns=columns_num,
                           col_names=string.ascii_uppercase[:columns_num],
                           random=False, input_data=input_data)]
            for i in range(extra_data_num):
                extra_data = gen_df(data_length, columns=columns_num,
                                    col_names=string.ascii_uppercase[:columns_num],
                                    seed=i)
                args.append(extra_data)

            self._test_jit(pyfunc, base, *args)
            self._test_py(pyfunc, base, *args)

    def _test_df_rolling_method(self, name, rolling_params=None,
                                extra_usecase_params='', method_params=''):
        ncalls, total_data_length = self.map_ncalls_dlength[name]
        usecase = gen_df_rolling_usecase(name, rolling_params=rolling_params,
                                         extra_usecase_params=extra_usecase_params,
                                         method_params=method_params, ncalls=ncalls)
        extra_data_num = 0
        if extra_usecase_params:
            extra_data_num += len(extra_usecase_params.split(', '))
        self._test_case(usecase, name, total_data_length,
                        extra_data_num=extra_data_num)

    def test_df_rolling_apply_mean(self):
        method_params = 'lambda x: np.nan if len(x) == 0 else x.mean()'
        self._test_df_rolling_method('apply', method_params=method_params)

    def test_df_rolling_corr(self):
        self._test_df_rolling_method('corr', extra_usecase_params='other',
                                     method_params='other=other')

    def test_df_rolling_count(self):
        self._test_df_rolling_method('count')

    def test_df_rolling_cov(self):
        self._test_df_rolling_method('cov', extra_usecase_params='other',
                                     method_params='other=other')

    def test_df_rolling_kurt(self):
        self._test_df_rolling_method('kurt')

    def test_df_rolling_max(self):
        self._test_df_rolling_method('max')

    def test_df_rolling_mean(self):
        self._test_df_rolling_method('mean')

    def test_df_rolling_median(self):
        self._test_df_rolling_method('median')

    def test_df_rolling_min(self):
        self._test_df_rolling_method('min')

    def test_df_rolling_quantile(self):
        self._test_df_rolling_method('quantile', method_params='0.25')

    def test_df_rolling_skew(self):
        self._test_df_rolling_method('skew')

    def test_df_rolling_std(self):
        self._test_df_rolling_method('std')

    def test_df_rolling_sum(self):
        self._test_df_rolling_method('sum')

    def test_df_rolling_var(self):
        self._test_df_rolling_method('var')
