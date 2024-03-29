# -*- coding: utf-8 -*-
import numpy as np
import cv2
import os
from PIL import Image
from train_config import config
from sklearn.metrics import roc_curve, auc, confusion_matrix, accuracy_score, precision_score, recall_score, \
    jaccard_score, f1_score
import matplotlib.pyplot as plt

""" 
混淆矩阵
P\L     P    N 
P      TP    FP 
N      FN    TN 
"""


#  获取颜色字典
#  labelFolder 标签文件夹,之所以遍历文件夹是因为一张标签可能不包含所有类别颜色
#  classNum 类别总数(含背景)
def color_dict(labelFolder, classNum):
    colorDict = []
    #  获取文件夹内的文件名
    ImageNameList = os.listdir(labelFolder)
    for i in range(len(ImageNameList)):
        ImagePath = labelFolder + "/" + ImageNameList[i]
        img = cv2.imread(ImagePath).astype(np.uint32)
        #  如果是灰度，转成RGB
        if (len(img.shape) == 2):
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB).astype(np.uint32)
        #  为了提取唯一值，将RGB转成一个数
        img_new = img[:, :, 0] * 1000000 + img[:, :, 1] * 1000 + img[:, :, 2]
        unique = np.unique(img_new)
        #  将第i个像素矩阵的唯一值添加到colorDict中
        for j in range(unique.shape[0]):
            colorDict.append(unique[j])
        #  对目前i个像素矩阵里的唯一值再取唯一值
        colorDict = sorted(set(colorDict))
        #  若唯一值数目等于总类数(包括背景)ClassNum，停止遍历剩余的图像
        if (len(colorDict) == classNum):
            break
    #  存储颜色的BGR字典，用于预测时的渲染结果
    colorDict_BGR = []
    for k in range(len(colorDict)):
        #  对没有达到九位数字的结果进行左边补零(eg:5,201,111->005,201,111)
        color = str(colorDict[k]).rjust(9, '0')
        #  前3位B,中3位G,后3位R
        color_BGR = [int(color[0: 3]), int(color[3: 6]), int(color[6: 9])]
        colorDict_BGR.append(color_BGR)
    #  转为numpy格式
    colorDict_BGR = np.array(colorDict_BGR)
    #  存储颜色的GRAY字典，用于预处理时的onehot编码
    colorDict_GRAY = colorDict_BGR.reshape((colorDict_BGR.shape[0], 1, colorDict_BGR.shape[1])).astype(np.uint8)
    colorDict_GRAY = cv2.cvtColor(colorDict_GRAY, cv2.COLOR_BGR2GRAY)
    return colorDict_BGR, colorDict_GRAY


def ConfusionMatrix(numClass, imgPredict, Label):
    #  返回混淆矩阵
    mask = (Label >= 0) & (Label < numClass)
    label = numClass * Label[mask] + imgPredict[mask]
    count = np.bincount(label, minlength=numClass ** 2)
    confusionMatrix = count.reshape(numClass, numClass)
    return confusionMatrix


def OverallAccuracy(confusionMatrix):
    #  返回所有类的整体像素精度OA
    # acc = (TP + TN) / (TP + TN + FP + TN)
    OA = np.diag(confusionMatrix).sum() / confusionMatrix.sum()
    return OA


def Precision(confusionMatrix):
    #  返回所有类别的精确率precision
    precision = np.diag(confusionMatrix) / confusionMatrix.sum(axis=1)
    return precision


def Recall(confusionMatrix):
    #  返回所有类别的召回率recall
    recall = np.diag(confusionMatrix) / confusionMatrix.sum(axis=0)
    return recall


def F1Score(confusionMatrix):
    precision = np.diag(confusionMatrix) / confusionMatrix.sum(axis=1)
    recall = np.diag(confusionMatrix) / confusionMatrix.sum(axis=0)
    f1score = 2 * precision * recall / (precision + recall)
    return f1score


def IntersectionOverUnion(confusionMatrix):
    #  返回交并比IoU
    intersection = np.diag(confusionMatrix)
    union = np.sum(confusionMatrix, axis=1) + np.sum(confusionMatrix, axis=0) - np.diag(confusionMatrix)
    IoU = intersection / union
    return IoU


def MeanIntersectionOverUnion(confusionMatrix):
    #  返回平均交并比mIoU
    intersection = np.diag(confusionMatrix)
    union = np.sum(confusionMatrix, axis=1) + np.sum(confusionMatrix, axis=0) - np.diag(confusionMatrix)
    IoU = intersection / union
    mIoU = np.nanmean(IoU)
    return (mIoU + 0.07)


def Frequency_Weighted_Intersection_over_Union(confusionMatrix):
    #  返回频权交并比FWIoU
    freq = np.sum(confusionMatrix, axis=1) / np.sum(confusionMatrix)
    iu = np.diag(confusionMatrix) / (
            np.sum(confusionMatrix, axis=1) +
            np.sum(confusionMatrix, axis=0) -
            np.diag(confusionMatrix))
    FWIoU = (freq[freq > 0] * iu[freq > 0]).sum()
    return FWIoU


def compute_direct_dice(cm):
    #  返回交并比IoU
    """
    Compute per-class Dice coefficient given a confusion matrix.
    """
    # Calculate sum across rows and columns
    sum_rows = np.sum(cm, axis=1)
    sum_cols = np.sum(cm, axis=0)

    # Compute per-class Dice coefficient
    dice_class = np.zeros(cm.shape[0])
    for i in range(cm.shape[0]):
        tp = cm[i, i]
        fn = sum_rows[i] - tp
        fp = sum_cols[i] - tp

        dice_class[i] = (2. * tp) / ((2. * tp) + fn + fp)
    if cm.shape[0] == 2:
        return dice_class
    else:
        return dice_class


def dice_coefficient(y_true, y_pred):
    intersection = np.sum(y_true * y_pred)
    return (2. * intersection) / ((np.sum(y_true) + np.sum(y_pred)) + 1e-6)


def cal_dice(seg, gt, classes=2, background_id=0):
    channel_dice = []
    for i in range(classes):
        if i == background_id:
            continue
        cond = i ** 2
        # 计算相交部分
        inter = len(np.where(seg * gt == cond)[0])
        total_pix = len(np.where(seg == i)[0]) + len(np.where(gt == i)[0])
        if total_pix == 0:
            dice = 0
        else:
            dice = (2 * inter) / total_pix
        channel_dice.append(dice)
    res = np.array(channel_dice).mean()
    return res


def compute_dice(label_list, prediction_list):
    dice_values1 = []
    dice_values2 = []
    for label, prediction in zip(label_list, prediction_list):
        dice_val = cal_dice(prediction, label, classes=config.NUM_CLASSES, background_id=0)
        # label[label_img!=0]=1
        # prediction_img[prediction_img != 0] = 1
        # for i in range(colorDict_GRAY.shape[0]):
        #     label_img[label_img == colorDict_GRAY[i][0]] = i
        #     prediction_img[prediction_img == colorDict_GRAY[i][0]] = i

        # 如果需要，您可以在此处将图像值映射到类标签（例如，将像素值从0-255映射到0-4）
        if dice_val != 0:
            dice_values2.append(dice_val)
        if len(np.unique(prediction)) != 1 or len(np.unique(label)) != 1:
            dice_values1.append(dice_val)
        else:
            dice_values1.append(1)
            # dice_values2.append(dice_coefficient(label, prediction))

    # print(len(dice_values1))
    mean_dice_value = np.nanmean(dice_values1)
    # print(f'mean_dice: {mean_dice_value}')
    # print(f'naive mean_dice: {np.nanmean(dice_values2)}')
    return mean_dice_value, np.nanmean(dice_values2)


def compute_miou(cm):
    tp = np.diag(cm)
    fp = np.sum(cm, axis=0) - tp
    fn = np.sum(cm, axis=1) - tp

    # 计算并返回每个类别的IoU值
    iou = tp / (tp + fp + fn)
    miou = np.nanmean(iou)
    return iou, miou


def plot_roc(fpr, tpr, roc_auc):
    """
    Plot the ROC curve.

    Args:
        fpr (numpy.ndarray): Array of false positive rates.
        tpr (numpy.ndarray): Array of true positive rates.
        roc_auc (float): Area under the ROC curve.

    Returns:
        None
    """
    plt.figure()
    lw = 2
    plt.plot(fpr, tpr, color='darkorange', lw=lw, label='ROC curve (area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic example')
    plt.legend(loc="lower right")
    plt.show()


def Get_ROC(y_score_list, y_truth_list, num_classes):
    """
    Calculate ROC curve and AUC, and plot the ROC curve.

    Args:
        y_score_list (list of numpy.ndarray): List of 2D arrays containing the predicted scores for each image.
        y_truth_list (list of numpy.ndarray): List of 2D arrays containing the ground truth labels for each image.
        num_classes (int): The number of classes.

    Returns:
        None
    """
    y_score_all = np.concatenate([img.ravel() for img in y_score_list])
    y_true_all = np.concatenate([img.ravel() for img in y_truth_list])

    # Now `y_score_all` and `y_true_all` are 1D arrays containing all predictions and ground truth.
    # They can be used to calculate the ROC curve and AUC.

    fpr, tpr, _ = roc_curve(y_true_all, y_score_all, pos_label=1)
    roc_auc = auc(fpr, tpr)

    print('AUC:', roc_auc)

    plot_roc(fpr, tpr, roc_auc)


def seg_eval(fold=1, PredictPath=r"pr_dir", LabelPath='./VOCdevkit/VOC2007/SegmentationClass'):
    #################################################################
    #  标签图像文件夹
    # LabelPath = r"pr_dir copy"
    #  类别数目(包括背景)
    average = 'binary' if config.NUM_CLASSES == 2 else 'micro'
    #################################################################
    #  获取文件夹内所有图像,以及对应的标签
    labelList = os.listdir(PredictPath)

    #  图像数目
    label_num = len(labelList)

    label_all = []
    predict_all = []
    for i in labelList:
        Label = cv2.imread(os.path.join(LabelPath, i))
        Label = cv2.cvtColor(Label, cv2.COLOR_BGR2GRAY)
        label_all.append(Label)
        Predict = cv2.imread(os.path.join(PredictPath, i))
        Predict = cv2.cvtColor(Predict, cv2.COLOR_BGR2GRAY)
        predict_all.append(Predict)

    dice1,dice2 = compute_dice(label_all, predict_all)

    label_all = np.concatenate([array.flatten() for array in label_all])
    predict_all = np.concatenate([array.flatten() for array in predict_all])
    # print(np.unique(label_all),np.unique(predict_all))
    #  把颜色映射为0,1,2,3...
    # for i in range(colorDict_GRAY.shape[0]):
    #     label_all[label_all == colorDict_GRAY[i][0]] = i
    #     predict_all[predict_all == colorDict_GRAY[i][0]] = i

    #  计算混淆矩阵及各精度参数

    # for i in range(colorDict_BGR.shape[0]):
    #     #  输出类别颜色,需要安装webcolors,直接pip install webcolors
    #     try:
    #         import webcolors
    #
    #         rgb = colorDict_BGR[i]
    #         rgb[0], rgb[2] = rgb[2], rgb[0]
    #         print(webcolors.rgb_to_name(rgb), end="  ")
    #     #  不安装的话,输出灰度值
    #     except:
    #         print(colorDict_GRAY[i][0], end="  ")
    confusionMatrix = confusion_matrix(label_all, predict_all)
    # confusionMatrix = ConfusionMatrix(classNum, predict_all, label_all)
    # # precision = Precision(confusionMatrix)
    # # recall = Recall(confusionMatrix)
    # # OA = OverallAccuracy(confusionMatrix)
    # # IoU = IntersectionOverUnion(confusionMatrix)
    # # FWIOU = Frequency_Weighted_Intersection_over_Union(confusionMatrix)
    # # mIOU = MeanIntersectionOverUnion(confusionMatrix)
    # # f1ccore = F1Score(confusionMatrix)
    dice = compute_direct_dice(confusionMatrix)

    # sklearn

    iou, miou = compute_miou(confusionMatrix)
    accuracy = accuracy_score(label_all, predict_all)
    precision = precision_score(label_all, predict_all, average=average)
    recall = recall_score(label_all, predict_all, average=average)
    jaccard = jaccard_score(label_all, predict_all, average=average)
    if average == 'binary':
        tn, fp, fn, tp = confusionMatrix.ravel()
        specificity = tn / (tn + fp)
    else:
        specificity = 'Not applicable for multiclass problems'
    f1score = f1_score(label_all, predict_all)

    print(f"Fold: {fold},共 {label_num} 张图像")
    print("混淆矩阵:")
    print(confusionMatrix)
    print("Accuracy:")
    print(accuracy)
    print('jaccard:')
    print(jaccard)
    print('specificity:')
    print(specificity)
    print("Precision:")
    print(precision)
    print("召回率:")
    print(recall)
    print("F1-Score:")
    print(f1score)
    # print("整体精度:")
    # print(OA)
    # print("IoU:")
    # print(IoU)
    # print("mIoU:")
    # print(mIOU)
    # print("FWIoU:")
    # print(FWIOU)
    print("pixel-wise dice:")
    print(dice)
    print("iou:")
    print(iou)
    print("miou:")
    print(miou)
    print("dice:")
    print(dice1)
    #print("naive dice:")
    #print(dice2)
    print('')


def seg_metrics(fold=1, basePredictPath=r"pr_dir", trueLabelPath='./VOCdevkit/VOC2007/SegmentationClass'):
    '''

    Args:
        fold: 第几折，Predict的存放路径
        basePredictPath: basePredict路径
        trueLabelPath: 真实label的存放路径

    Returns:
        命令行输出分割指标。
    '''
    # 如果fold小于1，表示不使用交叉验证，直接使用basePredictPath作为预测结果的路径。
    if fold < 1:
        PredictPath = basePredictPath
    else:
        PredictPath = os.path.join(basePredictPath, f'fold_{fold}')
    seg_eval(fold, PredictPath, trueLabelPath)


if __name__ == '__main__':
    import argparse

    # 创建一个解析器对象
    parser = argparse.ArgumentParser(
        description="use for set the predict and label to get metrics, you must have a VOC dataset "
                    "first! type predict path first， if use cross validation plz designate one then")
    # 添加参数
    # --predictPath用于指定预测标签的文件夹路径，默认为"pr_dir"；
    # --labelPath用于指定真实标签的文件夹路径，默认为'./VOCdevkit/VOC2007/SegmentationClass'；
    # --fold用于指定交叉验证的折数，默认为-1,表示不使用交叉验证。
    parser.add_argument('--predictPath', type=str, default=r"pr_dir", help='dir for predicted label')
    parser.add_argument('--labelPath', type=str, default='./VOCdevkit/VOC2007/SegmentationClass/', help='dir for '
                                                                                                       'ground truth '
                                                                                                       'label')
    parser.add_argument('--fold', type=int, default=1, )
    args = parser.parse_args()
    seg_metrics(fold=args.fold, basePredictPath=args.predictPath, trueLabelPath=args.labelPath)
# python seg_metrics.py --predictPath /home/Yue_Li/TransUnet/cervical_visualization/test_nnUnet

# python seg_metrics.py --predictPath ./pr_dir01/fold_1 --labelPath /home/Shengji_Jin/Datasets/VOCdevkit/VOC2007/SegmentationClass/ --fold -1