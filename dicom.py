from __future__ import annotations
import pydicom
import pydicom.dataset
import pydicom.tag

# DEBUG
import matplotlib.pyplot as plt

import os
from typing import Callable, List
from functools import cmp_to_key
import typing as typ

class DICOMConstants():
    # Keyword constants from the DICOM standard translated to their (group, element) tuples.
    # Maintained for readability, flexibility (since otherwise pydicom only spits out a rdonly value),
    # and staying ahead of the library, in case the standard ever does change (fingers crossed, it doesn't).
    kSeriesNumber = (0x0020, 0x0011)
    kInstanceNumber = (0x0020, 0x0013)
    kStudyInstanceUID = (0x0020, 0x000D)
    kSpacingBetweenSlices = (0x0018, 0x0088)
    kPixelSpacing = (0x0028, 0x0030)    # Row spacing (vert), column spacing (horiz). c2c.

    kSCreator = "avn-surface-area" # Creator name for private blocks as per DICOM spec
    kBAnnotationsBlock = 0x6969 # We store our annotation data here
    class Annotations:
        kPoints = 0x01

    kBPointBlock = 0x6971   # Each point must be represented as a Dataset per DICOM standard.
    # This means the actual (x, y) coord needs to be stored in its own private block.
    class Point:
        kX = 0x01
        kY = 0x02

    # Helper utils
    @staticmethod
    def uid(ds: pydicom.Dataset) -> str:
        return f"{ds[DICOMConstants.kStudyInstanceUID].value}:{ds[DICOMConstants.kSeriesNumber].value}:{ds[DICOMConstants.kInstanceNumber].value}"
    
    @staticmethod
    def getBlock(ds: pydicom.Dataset, group: int) -> pydicom.dataset.PrivateBlock:
        return ds.private_block(group, DICOMConstants.kSCreator)
    
    @staticmethod
    def tag(pb: pydicom.dataset.PrivateBlock, offset: int) -> pydicom.tag.BaseTag:
        return pb.get_tag(offset)

    # Less typing
    @staticmethod
    def get(ds: pydicom.Dataset, tagTuple: typ.Tuple[int, int]):
        return ds[tagTuple].value


class DICOMStudy():
    # Some defaults for callbacks
    @staticmethod
    def d_onSeriesBegin(number: int, firstFrame: pydicom.FileDataset) -> None:
        pass

    @staticmethod
    def d_onSeriesEnd(number: int, lastFrame: pydicom.FileDataset) -> None:
        pass

    def __init__(self, dirPath: str = "", onSeriesBegin: Callable = d_onSeriesBegin, onSeriesEnd: Callable = d_onSeriesEnd, skipInitializer = False,
                 series: dict[int, list[str]] = {}, seriesKeys: list[int] = [], dicomObjs: dict[str, pydicom.Dataset] = {}) -> None:
        if skipInitializer:
            self._series = series
            self._seriesKeys = seriesKeys
            self._dicomObjs = dicomObjs
            return # we will get monkeypatched
        elif not len(dirPath):
            raise Exception("Dir path empty!")
        self._i = 0 # Index of the current series we're on
        self._j = 0 # Index of the frame in the series
        self._curr = None
        self._end = False # Have we reached the end of the study?
        self._sBegin = onSeriesBegin
        self._sEnd = onSeriesEnd
        self._studyUid = "" # For metadata purposes.

        """
        Try to find an order for the DICOM files.
        Even assuming there is only one study, there may be multiple different series,
        so find a sorting of the series by something like [(0020, 0011) Series Number] first, 
        and then sort each series by the standard [(0020, 0013) Instance Number].
        """
        # Each series maintains its list of (sorted) images.
        self._series: dict[int, list[str]] = {}
        self._seriesKeys: list[int] = []

        # This should make things more efficient as we don't have to re-read the files multiple times.
        self._dicomObjs: dict[str, pydicom.Dataset] = {}

        path = os.path.abspath(os.path.expanduser(dirPath))

        # Get the study info first
        first = os.listdir(path)[0]
        first = os.path.join(path, first)
        self._studyUid = pydicom.dcmread(first).get(DICOMConstants.kStudyInstanceUID).value
        print(f"Loading and assembling study {self._studyUid}, please wait... ", end="", flush=True)

        for img in os.listdir(path):
            img = os.path.join(path, img)
            ds = pydicom.dcmread(img)
            self._dicomObjs[img] = ds
            seriesNum = int(ds.get(DICOMConstants.kSeriesNumber).value)
            self._series.setdefault(seriesNum, [])
            self._series[seriesNum].append(img)
        
        def compInstanceNumber(x: str, y: str):
            xInst = int(self._dicomObjs[x].get(DICOMConstants.kInstanceNumber).value)
            yInst = int(self._dicomObjs[y].get(DICOMConstants.kInstanceNumber).value)
            return xInst - yInst

        for k in self._series.keys():
            self._series[k] = sorted(self._series[k], key=cmp_to_key(compInstanceNumber))
            self._seriesKeys.append(k)


        self._curr = self._dicomObjs[self._series[self._seriesKeys[self._i]][self._j]]
        print("Done!")

    """
    Load a single series from a list of Datasets.
    Allows for test data to masquerade as DICOM files;
    we only care that we get the headers we need.
    Assume given list is pre-sorted.
    """
    @classmethod
    def fromDatasets(cls: type[DICOMStudy], datasets: typ.List[pydicom.Dataset]) -> DICOMStudy:
        _series: dict[int, list[str]] = {}
        _seriesKeys: list[int] = []
        _dicomObjs: dict[str, pydicom.Dataset] = {}
        seriesNum = int(DICOMConstants.get(datasets[0], DICOMConstants.kSeriesNumber))
        _seriesKeys = [seriesNum]
        _series = {seriesNum: []}
        for i in range(len(datasets)):
            _series[seriesNum].append(str(i))
            _dicomObjs[str(i)] = datasets[i]
        return cls(skipInitializer=True, series=_series, seriesKeys=_seriesKeys, dicomObjs=_dicomObjs)

    """
    Advance to (and get) the next frame, calling any appropriate callbacks as necessary.
    Calling next() at the end of the study has no effect and simply returns None.
    Use reset() to reset to the "beginning" of the study or seek() to seek to a specific series + index.
    """
    def next(self) -> pydicom.Dataset | None:
        if self._end: return
        currFrame = self._dicomObjs[self._series[self._seriesKeys[self._i]][self._j]]
        
        if self._j == 0: 
            self._sBegin(self._seriesKeys[self._i], currFrame)
            self._j += 1
        elif self._j == len(self._series[self._seriesKeys[self._i]]) - 1:
            self._sEnd(self._seriesKeys[self._i], currFrame)
            self._j = 0
            self._i += 1
            if self._i >= len(self._seriesKeys):
                self._end = True
        else:
            self._j += 1

        self._curr = currFrame
        return currFrame
    
    """
    Gets the currently pointed to frame (or None, if at the end).
    """
    def curr(self) -> pydicom.Dataset:
        return self._curr # pyright: ignore
    """
    Resets the internal state to point back at the "first" frame of the entire study,
    specifically the first frame of the first series in the study.
    """
    def reset(self) -> None:
        self._i = self._j = 0
        self._end = False
        self._curr = self._dicomObjs[self._series[self._seriesKeys[self._i]][self._j]]

    """
    Seeks to a specific frame index of a specific SeriesNumber.
    If SeriesNumber/frame index is invalid, throws a ValueError.
    """
    def seek(self, seriesNumber: int, frame: int) -> None:
        if not seriesNumber in self._seriesKeys: raise ValueError(f"Invalid series number ({seriesNumber})!")
        if frame >= len(self._series[seriesNumber]): raise ValueError(f"Invalid frame index ({frame} >= {len(self._series[seriesNumber])})!")

        self._j = frame
        self._i = self._seriesKeys.index(seriesNumber)
        self._end = False
        self._curr = self._dicomObjs[self._series[self._seriesKeys[self._i]][self._j]]
    
    """
    Gets the sorted list of frames corresponding to a specific series
    in the current study.
    """
    def get(self, seriesNumber: int) -> typ.List[pydicom.Dataset]:
        if not seriesNumber in self._seriesKeys: raise ValueError(f"Invalid series number ({seriesNumber})!")
        out: typ.List[pydicom.Dataset] = []
        for file in self._series[seriesNumber]:
            out.append(self._dicomObjs[file])
        return out
    
    """
    NOTE: not to be confused with get(), which gets frames from a SINGLE series (yay english plurals!)
    
    Gets the list of series numbers in the study.
    """
    def getSeries(self) -> typ.List[int]:
        return self._seriesKeys
