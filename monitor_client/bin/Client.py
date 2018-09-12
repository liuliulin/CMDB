# _*_coding:utf-8_*_
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 程序文件所在的上一级目录
sys.path.append(BASE_DIR)

from core import main

if __name__ == "__main__":
    client = main.command_handler(sys.argv)
