import os.path
import secrets
import cv2
import numpy as np
from tqdm import tqdm


def replace_new_point(point: tuple, M, scale_x, scale_y):
    point_new = tuple(np.dot(M, np.array([point[0], point[1], 1]))[:2])
    point_new = (point_new[0] * scale_x, point_new[1] * scale_y)
    point_new = tuple(map(int, point_new))
    return point_new


def expend_image_label(img_path, label_path, scale_x, scale_y, angle, img_save_path: str, label_save_path: str,
                       is_fill=True, is_resize_on_raw=False, is_random_scale_x=False, is_random_scale_y=False,
                       is_random_angle=False, random_angle_tuple=None, extend_name=None):
    """
    :param img_path: 读取的图像路径
    :param label_path: 读取的图像输入路径
    :param scale_x: 水平方向拉伸系数
    :param scale_y: 竖直方向拉伸系数
    :param angle: 图像旋转角度
    :param img_save_path: 生成图像的保存路径
    :param label_save_path: 生成标签的保存路径
    :param is_fill: 旋转会丢失信息，是否填充图像保留信息
    :param is_resize_on_raw: True按照原图比例resize, 否则在填充后的图像上进行resize
    :param is_random_scale_x: 是否随机水平方向拉伸
    :param is_random_scale_y: 是否随机竖直方向拉伸
    :param is_random_angle: 是否随机旋转角度
    :param random_angle_tuple: 如果传入了元组,只能在这个元组中随机选择旋转角度
    :return: None
    """
    if is_random_scale_x:
        scale_x = np.random.uniform(0.5, 1.5)
    if is_random_scale_y:
        scale_y = np.random.uniform(0.5, 1.5)
    if is_random_angle:
        if random_angle_tuple is None:
            angle = np.random.uniform(-10, 10)
        else:
            rand = secrets.randbelow(len(random_angle_tuple))
            angle = random_angle_tuple[rand]
    dot = 4  # 保留小数点后几位
    # 读取图像
    img = cv2.imread(img_path)
    img_height, img_weight, _ = img.shape
    with open(label_path) as f:
        input_ = f.readlines()

    # 旋转和拉伸图像
    rows, cols = img.shape[:2]
    # 旋转矩阵
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)

    if is_fill:
        temp_list = [replace_new_point((0, 0), M, 1, 1),
                     replace_new_point((0, img_height), M, 1, 1),
                     replace_new_point((img_weight, 0), M, 1, 1),
                     replace_new_point((img_weight, img_height), M, 1, 1)]
        n_x, n_y = zip(*temp_list)
        n_x = [-i if i < 0 else i - img_weight for i in n_x if i > img_weight or i < 0]
        n_y = [-i if i < 0 else i - img_height for i in n_y if i > img_height or i < 0]
        n_x = n_x if len(n_x) > 0 else [0]
        n_y = n_y if len(n_y) > 0 else [0]
        img_ = np.zeros((img_height + 2 * max(n_y), img_weight + 2 * max(n_x), 3), dtype=np.uint8)
        img_[max(n_y):max(n_y) + img_height, max(n_x):max(n_x) + img_weight] = img

        img = img_
        # 旋转后也不会缺失图像信息
        rows, cols = img.shape[:2]
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    img_rotated = cv2.warpAffine(img, M, (cols, rows))

    img_t = cv2.cvtColor(img_rotated, cv2.COLOR_BGR2GRAY)

    h1, w1 = 0, 0
    for i in range(img_t.shape[0]):
        if not img_t[i, :].sum():
            h1 += 1
        else:
            break
    for i in range(img_t.shape[1]):
        if not img_t[:, i].sum():
            w1 += 1
        else:
            break
    img_rotated = img_rotated[h1:img_rotated.shape[0] - h1, w1:img_rotated.shape[1] - w1]
    rows, cols = img_rotated.shape[:2]
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    if is_resize_on_raw:
        img_rotated = cv2.resize(img_rotated, (int(img.shape[1] * scale_x), int(img.shape[0] * scale_y)))
    else:
        img_rotated = cv2.resize(img_rotated,
                                 (int(img_rotated.shape[1] * scale_x), int(img_rotated.shape[0] * scale_y)))
    new_name = os.path.basename(img_path) if extend_name is None else os.path.basename(img_path).replace('.', f'{extend_name}.')
    cv2.imwrite(os.path.join(img_save_path, new_name), img_rotated)
    rows, cols = img_rotated.shape[:2]
    temp_str = ''
    for i in input_:
        cls, x, y, w, h = map(float, i.split(' '))
        x, y = int((x - w / 2) * img_weight), int((y - h / 2) * img_height)
        w, h = int(w * img_weight), int(h * img_height)
        if is_fill:
            x, y = x + max(n_x), y + max(n_y)
        x -= w1
        y -= h1
        # 这里是需要转换的点
        point1 = (x, y)
        point2 = (x + w, y)
        point3 = (x + w, y + h)
        point4 = (x, y + h)

        # 将四个点组合起来
        l = [point1, point4, point2, point3]

        nl = []  # 把转化后的点添加这里
        for point in l:
            # 计算标记点point的新位置
            point_new = tuple(np.dot(M, np.array([point[0], point[1], 1]))[:2])
            if not is_resize_on_raw:
                point_new = (point_new[0] * scale_x, point_new[1] * scale_y)
            point_new = tuple(map(int, point_new))
            nl.append(point_new)

        ZIP = list(zip(nl[0], nl[1], nl[2], nl[3]))

        temp = [min(ZIP[0]), min(ZIP[1]), max(ZIP[0]) - min(ZIP[0]), max(ZIP[1]) - min(ZIP[1])]
        temp = [temp[0] + temp[2] // 2, temp[1] + temp[3] // 2, temp[2], temp[3]]
        temp[:] = round(temp[0] / cols, dot), round(temp[1] / rows, dot), round(temp[2] / cols, dot), round(
            temp[3] / rows, dot)
        temp = str(int(cls)) + ' ' + ' '.join(list((map(str, temp)))) + '\n'
        temp_str += temp
        # 保存为yolo格式标签
    new_name = os.path.basename(label_path) if extend_name is None else os.path.basename(label_path).replace('.', f'{extend_name}.')
    with open(os.path.join(label_save_path, new_name), 'w') as f:
        f.write(temp_str.strip())


if __name__ == '__main__':
    raw_data_path = r'C:\Users\lengdan\Desktop\811'
    new_data_path = r'C:\Users\lengdan\Desktop\ex\90'

    label_save_path = os.path.join(new_data_path, 'labels')  # 标签保存路径
    image_save_path = os.path.join(new_data_path, 'images')  # 图片保存路径
    angle_ = 90  # 数据增强采用的图片旋转角度

    if not os.path.exists(label_save_path):
        os.makedirs(label_save_path)
    if not os.path.exists(image_save_path):
        os.makedirs(image_save_path)

    path1 = os.listdir(raw_data_path + '/images')  # images/图片 所在路径
    for p in tqdm(path1):
        im_p = os.path.join(raw_data_path, 'images', p)
        la_p = os.path.join(raw_data_path, 'labels', p.split('.')[0] + '.txt')

        expend_image_label(img_path=im_p,
                           label_path=la_p, scale_x=1,
                           scale_y=1, angle=angle_, img_save_path=image_save_path,
                           label_save_path=label_save_path,
                           random_angle_tuple=(0, 90, 180, 270), extend_name='_90')



if __name__ == '__main__':
    raw_data_path = r'C:\Users\lengdan\Desktop\811'
    new_data_path = r'C:\Users\lengdan\Desktop\ex\180'

    label_save_path = os.path.join(new_data_path, 'labels')  # 标签保存路径
    image_save_path = os.path.join(new_data_path, 'images')  # 图片保存路径
    angle_ = 180  # 数据增强采用的图片旋转角度

    if not os.path.exists(label_save_path):
        os.makedirs(label_save_path)
    if not os.path.exists(image_save_path):
        os.makedirs(image_save_path)

    path1 = os.listdir(raw_data_path + '/images')  # images/图片 所在路径
    for p in tqdm(path1):
        im_p = os.path.join(raw_data_path, 'images', p)
        la_p = os.path.join(raw_data_path, 'labels', p.split('.')[0] + '.txt')

        expend_image_label(img_path=im_p,
                           label_path=la_p, scale_x=1,
                           scale_y=1, angle=angle_, img_save_path=image_save_path,
                           label_save_path=label_save_path,
                           random_angle_tuple=(0, 90, 180, 270), extend_name='_180')


if __name__ == '__main__':
    raw_data_path = r'C:\Users\lengdan\Desktop\811'
    new_data_path = r'C:\Users\lengdan\Desktop\ex\91'

    label_save_path = os.path.join(new_data_path, 'labels')  # 标签保存路径
    image_save_path = os.path.join(new_data_path, 'images')  # 图片保存路径
    angle_ = -90  # 数据增强采用的图片旋转角度

    if not os.path.exists(label_save_path):
        os.makedirs(label_save_path)
    if not os.path.exists(image_save_path):
        os.makedirs(image_save_path)

    path1 = os.listdir(raw_data_path + '/images')  # images/图片 所在路径
    for p in tqdm(path1):
        im_p = os.path.join(raw_data_path, 'images', p)
        la_p = os.path.join(raw_data_path, 'labels', p.split('.')[0] + '.txt')

        expend_image_label(img_path=im_p,
                           label_path=la_p, scale_x=1,
                           scale_y=1, angle=angle_, img_save_path=image_save_path,
                           label_save_path=label_save_path,
                           random_angle_tuple=(0, 90, 180, 270), extend_name='_91')

