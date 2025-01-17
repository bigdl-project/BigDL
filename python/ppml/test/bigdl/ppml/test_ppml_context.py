#
# Copyright 2016 The BigDL Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import unittest
import os
import csv
import random
import shutil

from bigdl.ppml.ppml_context import *
from pyspark.sql import SparkSession

resource_path = os.path.join(os.path.dirname(__file__), "resources")


class TestPPMLContext(unittest.TestCase):
    # generate app_id and app_key
    app_id = ''.join([str(random.randint(0, 9)) for i in range(12)])
    app_key = ''.join([str(random.randint(0, 9)) for j in range(12)])

    df = None
    data_content = None
    csv_content = None
    sc = None

    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.exists(resource_path):
            os.mkdir(resource_path)

        cls.csv_content = "name,age,job\n" + \
                          "jack,18,Developer\n" + \
                          "alex,20,Researcher\n" + \
                          "xuoui,25,Developer\n" + \
                          "hlsgu,29,Researcher\n" + \
                          "xvehlbm,45,Developer\n" + \
                          "ehhxoni,23,Developer\n" + \
                          "capom,60,Developer\n" + \
                          "pjt,24,Developer"

        # create a tmp csv file
        with open(os.path.join(resource_path, "people.csv"), "w") as file:
            file.write(cls.csv_content)

        # generate primaryKey and dataKey
        primary_key_path = os.path.join(resource_path, "primaryKey")
        data_key_path = os.path.join(resource_path, "dataKey")
        kms = init_keys(TestPPMLContext.app_id, TestPPMLContext.app_key,
                        primary_key_path, data_key_path)

        # generate encrypted file
        input_file = os.path.join(resource_path, "people.csv")
        output_file = os.path.join(resource_path, "encrypted/people.csv")
        generate_encrypted_file(kms, primary_key_path, data_key_path, input_file, output_file)

        args = {"kms_type": "SimpleKeyManagementService",
                "simple_app_id": cls.app_id,
                "simple_app_key": cls.app_key,
                "primary_key_path": primary_key_path,
                "data_key_path": data_key_path
                }

        # generate a tmp dataframe for test
        data = [("Java", "20000"), ("Python", "100000"), ("Scala", "3000")]
        spark = SparkSession.builder.appName('initData').getOrCreate()
        cls.df = spark.createDataFrame(data).toDF("language", "user")
        cls.data_content = '\n'.join([str(v['language']) + "," + str(v['user'])
                                      for v in cls.df.orderBy('language').collect()])

        from pyspark import SparkConf
        spark_conf = SparkConf()
        spark_conf.setMaster("local[4]")
        cls.sc = PPMLContext("testApp", args, spark_conf)

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(resource_path):
            shutil.rmtree(resource_path)

    def test_read_plain_file(self):
        input_path = os.path.join(resource_path, "people.csv")
        df = self.sc.read(CryptoMode.PLAIN_TEXT) \
            .option("header", "true") \
            .csv(input_path)
        self.assertEqual(df.count(), 8)

    def test_read_encrypt_file(self):
        input_path = os.path.join(resource_path, "encrypted/people.csv")
        df = self.sc.read(CryptoMode.AES_CBC_PKCS5PADDING) \
            .option("header", "true") \
            .csv(input_path)
        self.assertEqual(df.count(), 8)

    def test_write_plain_file(self):
        self.sc.write(self.df, CryptoMode.PLAIN_TEXT) \
            .mode('overwrite') \
            .option("header", True) \
            .csv(os.path.join(resource_path, "output/plain"))

    def test_write_encrypt_file(self):
        self.sc.write(self.df, CryptoMode.AES_CBC_PKCS5PADDING) \
            .mode('overwrite') \
            .option("header", True) \
            .csv(os.path.join(resource_path, "output/encrypt"))

    def test_write_and_read_plain_parquet(self):
        parquet_path = os.path.join(resource_path, "parquet/plain-parquet")
        # write as a parquet
        self.sc.write(self.df, CryptoMode.PLAIN_TEXT) \
            .mode('overwrite') \
            .parquet(parquet_path)

        # read from a parquet
        df_from_parquet = self.sc.read(CryptoMode.PLAIN_TEXT) \
            .parquet(parquet_path)

        content = '\n'.join([str(v['language']) + "," + str(v['user'])
                             for v in df_from_parquet.orderBy('language').collect()])
        self.assertEqual(content, self.data_content)

    def test_write_and_read_encrypted_parquet(self):
        parquet_path = os.path.join(resource_path, "parquet/en-parquet")
        # write as a parquet
        self.sc.write(self.df, CryptoMode.AES_GCM_CTR_V1) \
            .mode('overwrite') \
            .parquet(parquet_path)

        # read from a parquet
        df_from_parquet = self.sc.read(CryptoMode.AES_GCM_CTR_V1) \
            .parquet(parquet_path)

        content = '\n'.join([str(v['language']) + "," + str(v['user'])
                             for v in df_from_parquet.orderBy('language').collect()])
        self.assertEqual(content, self.data_content)

    def test_plain_text_file(self):
        path = os.path.join(resource_path, "people.csv")
        rdd = self.sc.textfile(path)
        rdd_content = '\n'.join([line for line in rdd.collect()])

        self.assertEqual(rdd_content, self.csv_content)

    def test_encrypted_text_file(self):
        path = os.path.join(resource_path, "encrypted/people.csv")
        rdd = self.sc.textfile(path=path, crypto_mode=CryptoMode.AES_CBC_PKCS5PADDING)
        rdd_content = '\n'.join([line for line in rdd.collect()])
        self.assertEqual(rdd_content, self.csv_content)


if __name__ == "__main__":
    unittest.main()
