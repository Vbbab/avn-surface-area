"""
A bootstrap utility to masquerade generated test data
as annotated DICOM data able to be fed into SurfaceArea.
"""
import sys, os
sys.path.append('..')
from dicom import DICOMStudy, DICOMConstants as DC
from surface_area import SurfaceArea
import pydicom
import typing as typ
import argparse

argParser = argparse.ArgumentParser()
argParser.add_argument('file', help='File to test')
args = argParser.parse_args()

file = args.file

SERIES = 1 # Arbitrary series number

"""
Makes a template pydicom.Dataset
with SeriesNumber and InstanceNumber set.
Points list MUST be along one direction (LTR).
dz: Spacing Between Slides, dist (mm) to next slide.
"""
def makeDicom(idx: int, points: typ.List[typ.Tuple[int, int]], sr: float, sc: float, dz: float) -> pydicom.Dataset:
    global SERIES
    ds = pydicom.Dataset()
    ds.add_new(DC.kSeriesNumber, 'DS', str(SERIES))
    ds.add_new(DC.kInstanceNumber, 'DS', str(idx))
    ds.add_new(DC.kStudyInstanceUID, 'UI', '1.1.1.1')

    pointDatasets = []
    for pt in points:
        pd = pydicom.Dataset()
        pointsBlock = pd.private_block(DC.kBPointBlock, DC.kSCreator, create=True)
        pointsBlock.add_new(DC.Point.kX, 'DS', str(pt[0]))
        pointsBlock.add_new(DC.Point.kY, 'DS', str(pt[1]))
        pointDatasets.append(pd)

    annotationsBlock = ds.private_block(DC.kBAnnotationsBlock, DC.kSCreator, create=True)
    annotationsBlock.add_new(DC.Annotations.kPoints, 'SQ', pointDatasets)
    
    ds.add_new(DC.kSpacingBetweenSlices, 'DS', str(dz))
    ds.add_new(DC.kPixelSpacing, 'DS', [str(sr), str(sc)])
    return ds

frames: typ.List[pydicom.Dataset] = []

data = ""
with open(file, 'r') as f:
    data = f.read()

# File format:
# <NUM_FRAMES:N> <POINTS_PER_FRAME:P>
# [Repeated]:
# X Y X Y .. SR SC DZ ==> single line 2P space-separated values followed by Row Spacing, Column Spacing, Spacing Between Slide (mm) each frame (N lines)
# Last frame shall omit DZ. It will be ignored if present.

## TODO: how the fuck am i supposed to get std::cout-style tokenization in Python?!!!
## The user is solely responsible for making sure the file is formatted correctly and valid.
## (Otherwise, hope you like Exceptions...)
lines = data.split('\n')
N, P = [int(i) for i in lines[0].split(' ')]
idx = 0 # Allow for comments
totalValidLines = 0
# Count non-comment lines first. TODO: could this be made better?
for i in range(1, len(lines)):
    if not lines[i].startswith('#') and len(lines[i]): totalValidLines += 1

for i in range(1, len(lines)):
    if lines[i].startswith('#') or not len(lines[i]): continue
    vals = lines[i].split(' ')
    points: typ.List[typ.Tuple[int, int]] = []
    for j in range(0, 2 * P, 2):
        print(i, j)
        points.append((int(vals[j]), int(vals[j + 1])))
    
    sr = float(vals[2 * P])
    sc = float(vals[2 * P + 1])
    dz = 1 # Some random valid value
    if idx < totalValidLines - 1:
        dz = float(vals[2 * P + 2])
    
    frames.append(makeDicom(idx, points, sr, sc, dz))
    idx += 1

study = DICOMStudy.fromDatasets(frames)
print(SurfaceArea(study, SERIES).getArea())
