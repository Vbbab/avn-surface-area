# TODO: replace w/ wrapper around gui
from dicom import DICOMStudy
from surface_area import SurfaceArea

path = input("Path to dir containing annotated datasets: ")
series: int = int(input("Series # to analyze: "))

print(SurfaceArea(DICOMStudy(path), series).getArea())
