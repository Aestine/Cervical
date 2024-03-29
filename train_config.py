class BaseConfig:
    inputs_size = [256, 256, 3]
    image_type = '.png'  # image is jpg or png
    # ---------------------#
    #   if n_fold=1 then all train, if other divide the dataset into n part, using cross validation
    #   建议为5，大数据集可以为10
    #   cur_fold represent the fold that been training, if cur_fold=-1, then train all folds.
    # ---------------------#
    n_fold = 5
    cur_fold=-1
    # ---------
    log_dir = "logs/"
    # ---------------------#
    #   分类个数+1
    #   2+1
    # ---------------------#
    NUM_CLASSES = 3
    # --------------------------------------------------------------------#
    #   建议选项：
    #   种类少（几类）时，设置为True
    #   种类多（十几类）时，如果batch_size比较大（10以上），那么设置为True
    #   种类多（十几类）时，如果batch_size比较小（10以下），那么设置为False
    # ---------------------------------------------------------------------#

    # -------------------------------#
    #   选用的MODEL
    # -------------------------------#
    model = 'BASIC'
    # -------------------------------#
    #   1: BASIC(defaultTransUnet)
    #   2: Vit_CBAM_ASPP
    #   3: Vit_CBAM
    #   4：Vit_CBAM_CBAM(w/o ASPP)
    # -------------------------------#
    # (focal or ce) + dice
    focal_loss = True
    cls_weights = True
    # -------------------------------#
    #   主干网络预训练权重的使用
    #
    # -------------------------------#
    pretrained = True
    # backbone = "ECAresnet"
    # ---------------------#
    #   是否使用辅助分支
    #   会占用大量显存
    # ---------------------#
    aux_branch = False
    # ---------------------#
    #   下采样的倍数
    #   8和16
    # ---------------------#
    downsample_factor = 16
    # -------------------------------#
    #   Cuda的使用
    # -------------------------------#
    Cuda = True
    # ---------------------------------------------------------------------#
    #   distributed     用于指定是否使用单机多卡分布式运行
    #                   终端指令仅支持Ubuntu。CUDA_VISIBLE_DEVICES用于在Ubuntu下指定显卡。
    #                   Windows系统下默认使用DP模式调用所有显卡，不支持DDP。
    #   DP模式：
    #       设置            distributed = False
    #       在终端中输入    CUDA_VISIBLE_DEVICES=0,1 python train.py
    #   DDP模式：
    #       设置            distributed = True
    #       在终端中输入    CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.launch --nproc_per_node=2 train.py
    # ---------------------------------------------------------------------#
    distributed = True
    # ---------------------------------------------------------------------#
    #   sync_bn     是否使用sync_bn，DDP模式多卡可用
    # ---------------------------------------------------------------------#
    sync_bn = True
    model_path = './model_data/pretrained_weight.pth'
    # no_load_dict,加载预训练时不加载解码器部分
    no_load_dict = ['decoder', 'segmentation_head']
    # 设置解冻部分！
    frozen_modules = ["cbam", "decoder", 'ASPP_unit1', 'ASPP_unit2', 'ASPP_unit3', 'segmentation_head', 'se',
                      'aspp_cbam', ]  # removed: 'cls','ASPP_unit1', 'ASPP_unit2' 'aspp'

    # ----------------------#
    #   记录Loss
    # ----------------------#
    save_dir = 'logs'
    Init_Epoch = 0
    Interval_Epoch = 200
    # 设置冻结的epoch
    Freeze_Epoch = 40
    Freeze_Batch_Size = 2
    set_epoch_batch = [150, 1]
    # --------------#
    # BATCH_SIZE
    # --------------#
    Batch_size = 2
    # ----------------------#
    # 输出图像的形式
    # 0：不上色
    # 1：上色
    # 2：混合
    # -----------------------#
    output_type = 2
    # 跳跃连接数量
    n_skip = 4

    # 连通部件数量，不指定则为-1
    component = -1


class Config_Cervical(BaseConfig):
    inputs_size = [512, 512, 3]
    image_type = '.jpg'  # image is jpg or png
    NUM_CLASSES = 2
    model = 'BASIC'
    component = 1


class Config_Breast(BaseConfig):
    inputs_size = [512, 512, 3]
    image_type = '.png'  # image is jpg or png
    NUM_CLASSES = 2
    model = 'BASIC'


class Config_DDTI(BaseConfig):
    # n_skip = 3
    inputs_size = [256, 256, 3]
    image_type = '.png'  # image is jpg or png
    NUM_CLASSES = 2
    component = 1
    model = 'BASIC'


config = Config_Breast()
