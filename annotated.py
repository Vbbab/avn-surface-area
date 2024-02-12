import pydicom
import pydicom.dataset
from dicom import DICOMConstants as DC
from typing import List, Tuple

class Annotated:
    def __init__(self, ds: pydicom.FileDataset):
        self.ds = ds
        self.points: List[Tuple[int, int]] = []
        block: pydicom.dataset.PrivateBlock
        # Let's make sure we're not trolling
        try:
            block = DC.getBlock(self.ds, DC.kBAnnotationsBlock)
        except KeyError:
            raise ValueError(f"DS {DC.uid(self.ds)} not annotated!")
        
        # Load the data into List[tuple]
        points: pydicom.Sequence = ds.get(DC.tag(block, DC.Annotations.kPoints)).value
        for pointDataset in points:
            pointBlock: pydicom.dataset.PrivateBlock
            try:
                pointBlock = DC.getBlock(pointDataset, DC.kBPointBlock)
            except KeyError:
                raise ValueError(f"DS {DC.uid(self.ds)} not annotated properly (invalid point datasets)")
            x: int = pointDataset.get(DC.tag(pointBlock, DC.Point.kX)).value
            y: int = pointDataset.get(DC.tag(pointBlock, DC.Point.kY)).value
            self.points.append((x, y))

    def getPoints(self):
        return self.points

