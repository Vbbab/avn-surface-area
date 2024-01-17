from sys import stdlib_module_names
import pydicom

# DEBUG
import matplotlib.pyplot as plt

import os
from typing import Callable
from functools import cmp_to_key


class DICOMConstants():
    # Keyword constants from the DICOM standard translated to their (group, element) tuples.
    # Maintained for readability, flexibility (since otherwise pydicom only spits out a rdonly value),
    # and staying ahead of the library, in case the standard ever does change (fingers crossed, it doesn't).
    kSeriesNumber = (0x0020, 0x0011)
    kInstanceNumber = (0x0020, 0x0013)

    kStudyInstanceUID = (0x0020, 0x000D)

class DICOMStudy():
    # Some defaults for callbacks
    @staticmethod
    def d_onSeriesBegin(number: int, firstFrame: pydicom.FileDataset) -> None:
        pass

    @staticmethod
    def d_onSeriesEnd(number: int, lastFrame: pydicom.FileDataset) -> None:
        pass

    def __init__(self, dirPath: str, onSeriesBegin: Callable = d_onSeriesBegin, onSeriesEnd: Callable = d_onSeriesEnd) -> None:
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
        self._dicomObjs: dict[str, pydicom.FileDataset] = {}

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
    Advance to (and get) the next frame, calling any appropriate callbacks as necessary.
    Calling next() at the end of the study has no effect and simply returns None.
    Use reset() to reset to the "beginning" of the study or seek() to seek to a specific series + index.
    """
    def next(self) -> pydicom.FileDataset | None:
        if self._end: return
        print((self._i, self._j), len(self._series[self._seriesKeys[self._i]]), len(self._seriesKeys))
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
    def curr(self) -> pydicom.FileDataset:
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

