# SiamPolar: Realtime Video Object Segmentation with Polar Representation in Traffic Scenes

This is the official code of SiamPolar based on [mmdetection](https://github.com/open-mmlab/mmdetection). 

Paper: [SiamPolar: Realtime Video Object Segmentation with Polar Representation in Traffic Scene](). 

![siam_polarmask_pipeline](./imgs/siam_polarmask_pipeline.png)

## Highlights

- **Improved polar representation**: We introduce a novel polar representation for video object segmentation and propose a real-time video object segmentation method named SiamPolar, which is an anchor-free object tracking method.
- **Asymmetric Siamese network**: An asymmetric Siamese network is developed using similar backbones with different depths, which not only alleviates antagonism among the branches of polar head, but also allows the siamese network to perform better with deeper backbones.
- **Peeling convolutions**: Negative effects exist among the branches of polar head, so we design repeated cross correlation and semi-FPN based on the idea of peeling convolutions. Redundant anti-features can be reduced without convolutions. As a result, the mutual influence between each branch feature can be decreased.

## Performances

**Visualization on TSD-max dataset (truck, car) and DAVIS-2016 (goat, paragliding-launch)**

![vis](./imgs/vis.png)

**Results on DAVIS-2016**

| Methods   | $J_M$    | $J_R$    | $J_D$   | $F_D$    | $F_R$    | $F_D$   | Speed     |
| --------- | -------- | -------- | ------- | -------- | -------- | ------- | --------- |
| SiamMask  | 71.3     | 86.8     | 3.0     | **67.8** | **79.8** | **2.1** | 55.00     |
| SiamPolar | **71.4** | **96.2** | **0.7** | 56.7     | 60.0     | 18.1    | **59.20** |

## Setup Environment

SiamPolar is implemented on [mmdetection](https://github.com/open-mmlab/mmdetection). It can be installed easily as following, and more details can be seen in `./INSTALL.md`.

```shell
git clone ...
cd SiamPolar
conda create -n open_mmlab python=3.7 -y
source activate open_mmlab

pip install --upgrade pip
pip install cython torch==1.4.0 torchvision==0.5.0 mmcv
pip install -r requirements.txt # ignore the errors
pip install "git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI"

python setup.py develop
# or "pip install -v -e ."
```

## Prepare DAVIS Dataset

1. Download DAVIS from [kaggle-DAVIS480p](https://www.kaggle.com/mrjb166/davis480p).

2. Convert DAVIS to coco format by `/tools/conver_datasets/davis2coco.py` and organized it as following

```shell
SiamPolar
├── mmdet
├── tools
├── configs
├── data
│  ├── DAVIS
│  │  ├── Annotations
|  |  |  ├── 480p_train.json
|  |  |  ├── 480p_trainval.json
|  |  |  ├── 480p_val.json
|  |  |  ├── db_info.yml
│  │  ├── Imageset
│  │  ├── JPEGImages
```

## Train & Test

It can be trained and test as other mmdetection models. For more details, you can read [mmdetection-manual](https://mmdetection.readthedocs.io/en/latest/INSTALL.html) and [mmcv-manual](https://mmcv.readthedocs.io/en/latest/image.html). This is an example of SiamPolarMask(ResNet50 Backbone). 

```shell
python tools/train.py ./configs/siampolar/siampolar_r101.py --gpus 1

python tools/test.py ./configs/siampolar/siampolar_r101.py \./work_dirs/siam_polarmask_r50/epoch_12.pth \
--out ./work_dirs/siam_polarmask_r50/res.pkl \
--eval vos
```

We also add some configures for SiamPolar like backbone type, polar points number and so on, which can be easily set in `./configs/siampolar/`.

## Demo

```
cd ./demo
python visualize_vos.py
```

## License

For academic use, this project is licensed under the 2-clause BSD License - see the LICENSE file for details. For commercial use, please contact the authors. 
