from PIL import Image
import numpy as np

def convert_image_to_0_255(input_path, output_path):
 # 打开输入图片
    input_image = Image.open(input_path)

   # 将图片转换为NumPy数组
    input_array = np.array(input_image)

    # 将像素值从0-1范围映射到0-255范围
    output_array = (input_array * 255).astype(np.uint8)

    # 创建一个新的RGB图像
    rgb_image = Image.fromarray(output_array)

    # 保存RGB图像
    rgb_image.save(output_path)

if __name__ == '__main__':
    # 示例用法
    input_path = '/home/Shengji_Jin/TransUnet/cervical_visualization/5fold_final/fold_3/204.png'
    output_path = './204_2.png'
    convert_image_to_0_255(input_path, output_path)
