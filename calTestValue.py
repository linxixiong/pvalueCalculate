# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 16:12:51 2020
# 从spark计算或者报表查询得到实验组和对照组的均值，方差，实验人数等信息，输入脚本计算得到对应的p值和置信区间信息
@author: bearlin
"""
import math
from scipy.stats import t
from utils.logging import redirect_stdouterr_to_file, print_flags
from absl import app
from absl import flags
import numpy as np

FLAGS = flags.FLAGS
flags.DEFINE_string("log_file", None, "Logging filepath.")
flags.DEFINE_float("sample_mean_a", 0, "输入对照组均值,t检验时是对照组的均值,proportion检验时是对照组的比例,在spark计算或者报表查询得到")
flags.DEFINE_float("sample_mean_b", 0, "输入实验组均值,t检验时是实验组的均值,proportion检验时是实验组的比例,在spark计算或者报表查询得到")
flags.DEFINE_float("sample_variance_a", 1, "输入对照组方差,proportion检验时不用输入,在spark计算或者报表查询得到")
flags.DEFINE_float("sample_variance_b", 1, "输入实验组方差,proportion检验时不用输入,在spark计算或者报表查询得到")
flags.DEFINE_float("sample_size_a", 1, "输入对照组实验人数,在spark计算或者报表查询得到")
flags.DEFINE_float("sample_size_b", 1, "输入实验组验人数,在spark计算或者报表查询得到")
flags.DEFINE_float("confidence_level", 1.96, "输入置信水平，默认是5%置信水平")
flags.DEFINE_enum("test_type", "ttest",
                  ["ttest", "ptest"], "检验类型.")
flags.mark_flag_as_required("test_type")

def calculate_t_test(sample_mean_a, sample_mean_b, sample_variance_a, 
                       sample_variance_b, sample_size_a, sample_size_b, 
                       confidence_level):
    temp = math.sqrt(sample_variance_a / sample_size_a + sample_variance_b / sample_size_b)
    t_statics = (sample_mean_b - sample_mean_a) / temp  #计算t统计值
    interval_bound = confidence_level * temp / sample_mean_a  #计算提升幅度的置信区间上下界
    print("t statics is %.3f" % (t_statics))
    temp1 = sample_variance_a / sample_size_a
    temp2 = sample_variance_b / sample_size_b
    #计算自由度
    degrees = (temp1 + temp2) ** 2 / (temp1 ** 2 / (sample_size_a - 1) + temp2 ** 2 / (sample_size_b - 1))
    print("Degrees of freedom is %.3f" % (degrees))
    p_value = t.sf(np.abs(t_statics), degrees) * 2  #根据统计值和自由度计算双侧检验p值
    diff = sample_mean_b / sample_mean_a - 1
    return p_value, diff, [diff - interval_bound, diff + interval_bound]  #输出p值，提升幅度和置信区间上下界

def calculate_proportion_test(sample_mean_a, sample_mean_b, 
                              sample_size_a, sample_size_b, 
                              confidence_level):
    sample_variance_a = sample_mean_a * (1 - sample_mean_a)  #计算组1的方差
    sample_variance_b = sample_mean_b * (1 - sample_mean_b)  #计算组2的方差
    p_value, diff, [low, hig] = calculate_t_test(sample_mean_a, sample_mean_b, 
                                                 sample_variance_a, sample_variance_b,
                                                 sample_size_a, sample_size_b, 
                                                 confidence_level) #计算p值和置信区间
    return p_value, diff, [low, hig]

def main(argv):
  redirect_stdouterr_to_file(FLAGS.log_file)
  print_flags(FLAGS, __file__)
  
  if FLAGS.test_type == 'ttest':
      # 根据输入的均值，方差，实验天均人数，以及实验天数，返回p值，提升比例和提升比例执置信区间
      p_value, diff, [low, hig] = calculate_t_test(FLAGS.sample_mean_a, 
                                                   FLAGS.sample_mean_b, 
                                                   FLAGS.sample_variance_a, 
                                                   FLAGS.sample_variance_b, 
                                                   FLAGS.sample_size_a,
                                                   FLAGS.sample_size_b, 
                                                   FLAGS.confidence_level)
      print("p-value is %.8f,diff is %.3f,diffence percent low is %.4f,diffence percent high is %.4f" 
            % (p_value, diff, low, hig))

  elif FLAGS.test_type == 'ptest':
      # 根据输入的CTR或者转化率等，实验天均人数，以及实验天数，返回p值，提升比例和提升比例执置信区间
      p_value, diff, [low, hig] = calculate_proportion_test(FLAGS.sample_mean_a, 
                                                            FLAGS.sample_mean_b, 
                                                            FLAGS.sample_size_a,
                                                            FLAGS.sample_size_b, 
                                                            FLAGS.confidence_level)
      print("p-value is %.8f,diff is %.3f,diffence percent low is %.4f,diffence percent high is %.4f" 
            % (p_value, diff, low, hig))

  else:
      print("fail")

if __name__ == '__main__':
  app.run(main)
