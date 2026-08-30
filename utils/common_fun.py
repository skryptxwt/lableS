import cv2
import numpy as np
from PIL import Image
from pathlib import Path

root = Path(__file__).parent


def distance(x1y1, x2y2):
    return ((x1y1[0] - x2y2[0]) ** 2 + (x1y1[1] - x2y2[1]) ** 2) ** 0.5


def read_img(img_path):
    """Read an image from any filesystem path and return a BGR array.

    Converting through Pillow keeps support for non-ASCII paths and also
    normalizes grayscale, palette and RGBA images to the three channels used
    by the rest of the application.
    """
    with Image.open(img_path) as pil_image:
        image_np = np.asarray(pil_image.convert('RGB'))
    return cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)


def resize_img(img: np.ndarray, resize_img):
    """
    调整图像大小，填充黑色边框不改变图像的原始比例，缩放为窗口大小的scale倍
    """

    h, w = resize_img
    if h <= 0 or w <= 0:
        raise ValueError('目标图像尺寸必须大于 0')
    if img is None or img.size == 0:
        raise ValueError('输入图像不能为空')

    # 把图像按照原始的比例显示在Qt_label中
    scale_h = img.shape[0] / h
    scale_w = img.shape[1] / w

    scale_ = max(scale_w, scale_h)
    # 双线性插值
    zoom_img = cv2.resize(img,
                          (int(img.shape[1] / scale_), int(img.shape[0] / scale_))
                          , interpolation=cv2.INTER_LINEAR)
    back = np.zeros((h, w, 3), dtype=np.uint8)

    if scale_h >= scale_w:
        # 水平填充
        x1 = (back.shape[1] - zoom_img.shape[1]) // 2
        x2 = zoom_img.shape[1] + x1
        back[0:zoom_img.shape[0], x1: x2, :] = \
            zoom_img
    else:
        # 竖直填充
        y1 = (back.shape[0] - zoom_img.shape[0]) // 2
        y2 = zoom_img.shape[0] + y1
        back[y1:y2, 0:zoom_img.shape[1], :] = zoom_img
    zoom_img = back.astype(zoom_img.dtype)
    return cv2.resize(zoom_img, (w, h), interpolation=cv2.INTER_LINEAR)
