'''
@Author: JosieHong
@Reference: cocodataset/cocoapi(author: tsungyi),
            fperazzi/davis(author: federico perazzi)
@Date: 2020-05-08 12:04:38
@LastEditAuthor: JosieHong
LastEditTime: 2021-01-17 01:23:17
'''
import numpy as np
import time
import warnings

from .vos_measures import db_eval_iou, db_eval_boundary#, db_eval_t_stab

class DAVISeval:
    # The usage for DAVISeval is as follows:
    #  davisGt=..., davisDt=...         # load dataset and results
    #  E = DavisEval(davisGt,davisDt);  # initialize DavisEval object
    #  E.evaluate();                    # run per method evaluation

    def __init__(self, davisGt=None, davisDt=None):
        '''
        Initialize DavisEval using coco APIs for gt and dt
        :param davisGt: coco object with ground truth annotations
        :param davisDt: coco object with detection results
        :return: None
        '''
        self.davisGt = davisGt              # ground truth COCO API
        self.davisDt = davisDt              # detections COCO API
        self._gts = []                      # gt for evaluation  
        self._dts = []                      # dt for evaluation (chose hightest score's results per image)
        self.params = Params()              # parameters
        if not davisGt is None:
            self.params.imgIds = sorted(davisGt.getImgIds())
            self.params.catIds = sorted(davisGt.getCatIds())

        # josie
        self.measures = ['J', 'F']
        # self.measures = ['J', 'F', 'T']

    def _prepare(self):
        '''
        Prepare ._gts and ._dts for evaluation based on params
        :return: None
        '''
        def _toMask(anns, davis):
            # modify ann['segmentation'] by reference
            for ann in anns:
                # rle = davis.annToRLE(ann)
                mask = davis.annToMask(ann)
                ann['segmentation'] = mask
        p = self.params

        gts=self.davisGt.loadAnns(self.davisGt.getAnnIds(imgIds=p.imgIds, catIds=p.catIds))
        dts=self.davisDt.loadAnns(self.davisDt.getAnnIds(imgIds=p.imgIds, catIds=p.catIds))

        _toMask(gts, self.davisGt)
        _toMask(dts, self.davisDt)

        # set ignore flag
        for gt in gts:
            gt['ignore'] = gt['ignore'] if 'ignore' in gt else 0
            gt['ignore'] = 'iscrowd' in gt and gt['iscrowd']
        for gt in gts:
            self._gts.append(gt)
        last_img_id = 0 # the first img_id is 1
        for dt in dts:
            if dt['image_id'] == last_img_id:
                continue
            self._dts.append(dt)
            if dt['image_id'] > last_img_id + 1:
                missing_range = dt['image_id'] - (last_img_id + 1)
                for i in range(missing_range):
                    print("Image {} is missing. An empty result is appended.".format(last_img_id + 1 + i))
                    self._dts.append(dict({'image_id':last_img_id + 1 + i,
                                            'score': 0,
                                            'category_id': None,
                                            'segmentation': np.zeros(dt['segmentation'].shape), 
                                            'area': 0,
                                            'bbox': np.array([0, 0, 0, 0]),
                                            'id': None,
                                            'iscrowd': None}))
            last_img_id = dt['image_id']
        

    def _eval(self, annotations, segmentations, eval_func, measure):
        """ Evaluate all videos.
                Arguments:
                        annotations(ndarray):           binary annotation maps.
            segmentations(ndarray):         binary segmentation maps.
            eval_func(list: ['db_eval_iou', 'db_eval_boundary', 'db_eval_t_stab'])
                        measure(string: 'J','F','T'):   measure to be computed
                Returns:
                        X: per-frame measure evaluation.
                        M: mean   of per-frame measure.
                        O: recall of per-frame measure.
                        D: decay  of per-frame measure.
                """
        assert len(annotations) == len(segmentations)

        # if measure == 'T':
        #     return None
        #     magic_number = 5.0
        #     X = np.array([np.nan]+[eval_func(an,sg)*magic_number for an,sg
                #               in zip(segmentations[:-1], segmentations[1:])] + [np.nan])
        # else:
        X = np.array([np.nan]+[eval_func(an, sg) for an,sg in zip(annotations, segmentations)]+[np.nan])

        M,O,D = self.db_statistics(X)

        if measure == 'T': O = D = np.nan

        return X,M,O,D

    def db_statistics(self, per_frame_values):
        """ Compute mean,recall and decay from per-frame evaluation.
        Arguments:
            per_frame_values (ndarray): per-frame evaluation
        Returns:
            M,O,D (float,float,float):
                return evaluation statistics: mean,recall,decay.
        """

        # strip off nan values
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            M = np.nanmean(per_frame_values)
            O = np.nanmean(per_frame_values[1:-1]>0.5)

        # Compute decay as implemented in Matlab
        per_frame_values = per_frame_values[1:-1] # Remove first frame

        N_bins = 4
        ids = np.round(np.linspace(1,len(per_frame_values),N_bins+1)+1e-10)-1;
        ids = ids.astype(np.uint8)

        D_bins = [per_frame_values[ids[i]:ids[i+1]+1] for i in range(0,4)]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            D = np.nanmean(D_bins[0])-np.nanmean(D_bins[3])

        return M,O,D

    def evaluate(self):
        '''
        Run evaluation on different functions
        :return: None
        '''
        # metrix over all ---------------------------------------------------------------------------
        tic = time.time()
        self._prepare()
        
        annotations = [np.array(anno['segmentation']) for anno in self._gts]
        segmentations = [np.array(segm['segmentation']) for segm in self._dts]

        for measure in self.measures:
            if measure == 'J':
                J, Jm, Jo, Jd = self._eval(annotations, segmentations, db_eval_iou, measure)
            elif measure=='F':
                F, Fm, Fo, Fd = self._eval(annotations, segmentations, db_eval_boundary, measure)
            # elif measure=='T':
            #     T, Tm, To, Td = self._eval(annotations, segmentations, db_eval_t_stab, measure)
            else:
                raise Exception("Unknown measure=[{}}]. \
                    Valid options are measure={J,F,T}".format(measure))

        toc = time.time()
        print('DONE (t={:0.2f}s).'.format(toc-tic))

        print('J(M): {}, J(O): {}, J(D): {}'.format(Jm, Jo, Jd))
        print('F(M): {}, F(O): {}, F(D): {}'.format(Fm, Fo, Fd))
        print('T(M): unfinished')


        # # metrix per sequence ---------------------------------------------------------------------------
        # # note: for every category (no shuffle)
        # tic = time.time()
        # self._prepare()

        # last_category = -1
        # start_frame = 0
        # category_dict = {}
        # for i, gt in enumerate(self._gts):
        #     if gt['category_id'] != last_category:
        #         category_dict[self._gts[i-1]['category_id']] = [start_frame, self._gts[i-1]['image_id']]
        #         start_frame = gt['image_id']
        #         last_category = gt['category_id']
        # print('category_dict: ', category_dict)

        # for category in category_dict.keys():
        #     start_frame = category_dict[category][0]
        #     end_frame = category_dict[category][1]
        #     annotations = [np.array(anno['segmentation']) for anno in self._gts[start_frame:end_frame]]
        #     segmentations = [np.array(segm['segmentation']) for segm in self._dts[start_frame:end_frame]]

        #     for measure in self.measures:
        #         if measure == 'J':
        #             J, Jm, Jo, Jd = self._eval(annotations, segmentations, db_eval_iou, measure)
        #         elif measure=='F':
        #             F, Fm, Fo, Fd = self._eval(annotations, segmentations, db_eval_boundary, measure)
        #         # elif measure=='T':
        #         #     T, Tm, To, Td = self._eval(annotations, segmentations, db_eval_t_stab, measure)
        #         else:
        #             raise Exception("Unknown measure=[{}}]. \
        #                 Valid options are measure={J,F,T}".format(measure))

        #     print(category)
        #     print('J(M): {}, J(O): {}, J(D): {}'.format(Jm, Jo, Jd))
        #     print('F(M): {}, F(O): {}, F(D): {}'.format(Fm, Fo, Fd))
        #     print('T(M): unfinished')

        # toc = time.time()
        # print('DONE (t={:0.2f}s).'.format(toc-tic))


        # # metrix per sequence ---------------------------------------------------------------------------
        # # note: for every category (no shuffle)
        # tic = time.time()
        # self._prepare()

        # last_category = -1
        # start_frame = 0
        # category_dict = {}
        # for i, gt in enumerate(self._gts):
        #     if gt['category_id'] != last_category:
        #         if last_category != -1:
        #             category_dict[self._gts[i-1]['category_id']] = [start_frame, self._gts[i-1]['image_id']]
        #         start_frame = gt['image_id']
        #         last_category = gt['category_id']
        # print('category_dict: ', category_dict)

        # for category in category_dict.keys():
        #     start_frame = category_dict[category][0]
        #     end_frame = category_dict[category][1]
        #     annotations = [np.array(anno['segmentation']) for anno in self._gts[start_frame:end_frame]]
        #     segmentations = [np.array(segm['segmentation']) for segm in self._dts[start_frame:end_frame]]

        #     ape = 0
        #     for a, s in zip(annotations, segmentations):
        #         ape += np.sum(a) - np.sum(a*s)
        #     ape = ape / len(annotations)

        #     print(category)
        #     print('APE: ', ape)

        # toc = time.time()
        # print('DONE (t={:0.2f}s).'.format(toc-tic))
        
class Params:
    '''
    Params for davis evaluation api
    '''
    def setDetParams(self):
        self.imgIds = []
        self.catIds = []

    def __init__(self):
        self.setDetParams()