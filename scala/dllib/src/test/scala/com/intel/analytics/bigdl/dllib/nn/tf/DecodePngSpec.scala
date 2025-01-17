/*
 * Copyright 2016 The BigDL Authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.intel.analytics.bigdl.dllib.nn.tf

import java.io.{File => JFile}

import com.google.protobuf.ByteString
import com.intel.analytics.bigdl.dllib.tensor.Tensor
import com.intel.analytics.bigdl.dllib.utils.serializer.ModuleSerializationTest
import com.intel.analytics.bigdl.dllib.utils.tf.TFRecordIterator
import org.tensorflow.example.Example

class DecodePngSerialTest extends ModuleSerializationTest {
  private def getInputs(name: String): Tensor[ByteString] = {
    import com.intel.analytics.bigdl.dllib.utils.tf.TFTensorNumeric.NumericByteString
    val index = name match {
      case "png" => 0
      case "jpeg" => 1
      case "gif" => 2
      case "raw" => 3
    }

    val resource = getClass.getClassLoader.getResource("tf")
    val path = resource.getPath + JFile.separator + "decode_image_test_case.tfrecord"
    val file = new JFile(path)

    val bytesVector = TFRecordIterator(file).toVector
    val pngBytes = bytesVector(index)

    val example = Example.parseFrom(pngBytes)
    val imageByteString = example.getFeatures.getFeatureMap.get("image/encoded")
      .getBytesList.getValueList.get(0)

    Tensor[ByteString](Array(imageByteString), Array[Int]())
  }

  override def test(): Unit = {
    val decodePng = new DecodePng[Float](1).setName("decodePng")
    val input = getInputs("png")
    runSerializationTest(decodePng, input)
  }
}
